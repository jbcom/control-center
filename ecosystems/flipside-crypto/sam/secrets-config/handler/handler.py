"""
Secrets Config Preprocessor Lambda

This Lambda is responsible for:
1. Loading config from SSM (pushed by GHA workflow)
2. Discovering AWS accounts via Organizations
3. Discovering sandbox accounts via SSO/Identity Center group membership
4. Building the complete context for the merging Lambda
5. Writing the context to S3 and triggering the merging Lambda

Triggered by:
- SSM Parameter Store change events (via EventBridge)
- Direct invocation from GHA workflow
- Scheduled (optional backup trigger)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Environment variables
SSM_PREFIX = os.environ.get("SSM_PREFIX", "/terraform-modules/secrets-config")
SECRETS_BUCKET = os.environ.get("SECRETS_BUCKET")
RECORDS_KEY = os.environ.get("RECORDS_KEY", "records/workspaces/secrets/merging.json")
MERGING_FUNCTION_NAME = os.environ.get("MERGING_FUNCTION_NAME", "secrets-merging")
CONTROL_TOWER_EXEC_ROLE = os.environ.get("CONTROL_TOWER_EXECUTION_ROLE", "AWSControlTowerExecution")
IDENTITY_STORE_REGION = os.environ.get("IDENTITY_STORE_REGION", "us-east-1")


def load_config_from_ssm() -> Dict[str, Any]:
    """Load secrets pipeline configuration from SSM Parameter Store."""
    ssm = boto3.client("ssm")
    
    # Try to load combined config first
    try:
        response = ssm.get_parameter(Name=f"{SSM_PREFIX}/combined")
        config = json.loads(response["Parameter"]["Value"])
        LOGGER.info(f"Loaded combined config from SSM (version: {config.get('version', 'unknown')})")
        return config
    except ClientError as e:
        if e.response["Error"]["Code"] != "ParameterNotFound":
            raise
        LOGGER.info("Combined config not found, loading individual configs")
    
    # Fall back to loading individual configs
    config = {}
    for key in ["imports", "targets", "sandbox"]:
        try:
            response = ssm.get_parameter(Name=f"{SSM_PREFIX}/{key}")
            config[key] = json.loads(response["Parameter"]["Value"]).get(key, {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                LOGGER.warning(f"Config {key} not found in SSM")
                config[key] = {}
            else:
                raise
    
    return config


def discover_accounts() -> Dict[str, Dict[str, Any]]:
    """Discover AWS accounts via Organizations API."""
    org = boto3.client("organizations")
    accounts = {}
    
    try:
        paginator = org.get_paginator("list_accounts")
        for page in paginator.paginate():
            for account in page.get("Accounts", []):
                if account.get("Status") != "ACTIVE":
                    continue
                
                name = account.get("Name")
                if not name:
                    continue
                
                account_id = account.get("Id")
                email = (account.get("Email") or "").lower()
                
                data = {
                    "account_id": account_id,
                    "account_name": name,
                    "email": email,
                    "execution_role_arn": f"arn:aws:iam::{account_id}:role/{CONTROL_TOWER_EXEC_ROLE}",
                    "sso": [{"email": email}] if email else [],
                }
                
                # Generate aliases for flexible lookup
                for alias in _generate_aliases(name):
                    if alias not in accounts:
                        accounts[alias] = data
                        
    except ClientError as e:
        LOGGER.error(f"Failed to list accounts: {e}")
        raise
    
    LOGGER.info(f"Discovered {len(set(a['account_id'] for a in accounts.values()))} unique accounts")
    return accounts


def _generate_aliases(name: str) -> List[str]:
    """Generate aliases for account name lookup."""
    aliases = set()
    aliases.add(name)
    aliases.add(name.replace("-", "_"))
    aliases.add(name.replace("_", "-"))
    aliases.add(name.replace(" ", "-"))
    aliases.add(name.replace(" ", "_"))
    aliases.add(name.replace("-", ""))
    aliases.add(name.replace("_", ""))
    aliases.add(name.replace(" ", ""))
    return [a for a in aliases if a]


def discover_sandbox_accounts(
    sandbox_config: Dict[str, Any],
    accounts_map: Dict[str, Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover sandbox accounts via Identity Center group membership.
    
    For each sandbox classification that uses identity_center discovery,
    look up the SSO group and match members to AWS accounts.
    """
    if os.environ.get("SKIP_SANDBOX_DISCOVERY") == "1":
        LOGGER.info("SKIP_SANDBOX_DISCOVERY enabled; returning empty sandbox accounts")
        return {}
    
    identity_store = boto3.client("identitystore", region_name=IDENTITY_STORE_REGION)
    sso_admin = boto3.client("sso-admin", region_name=IDENTITY_STORE_REGION)
    
    # Get Identity Store ID
    identity_store_id = os.environ.get("IDENTITY_STORE_ID")
    if not identity_store_id:
        try:
            response = sso_admin.list_instances()
            instances = response.get("Instances", [])
            if instances:
                identity_store_id = instances[0]["IdentityStoreId"]
            else:
                LOGGER.warning("No SSO instances found; skipping sandbox discovery")
                return {}
        except ClientError as e:
            LOGGER.warning(f"Failed to get Identity Store ID: {e}")
            return {}
    
    # Build email-to-account index
    email_index = _build_email_index(accounts_map)
    
    discovered = {}
    for classification, cfg in sandbox_config.items():
        discovery = cfg.get("discovery", {})
        if discovery.get("method") != "identity_center":
            continue
        
        group_name = discovery.get("identity_center", {}).get("group_name")
        if not group_name:
            continue
        
        LOGGER.info(f"Discovering sandbox accounts for classification: {classification}")
        
        try:
            # Find the group
            response = identity_store.list_groups(
                IdentityStoreId=identity_store_id,
                Filters=[{"AttributePath": "DisplayName", "AttributeValue": group_name}],
            )
            groups = response.get("Groups", [])
            if not groups:
                LOGGER.warning(f"SSO group '{group_name}' not found")
                continue
            
            group_id = groups[0]["GroupId"]
            
            # List group members and match to accounts
            matched_accounts = []
            paginator = identity_store.get_paginator("list_group_memberships")
            
            for page in paginator.paginate(IdentityStoreId=identity_store_id, GroupId=group_id):
                for membership in page.get("GroupMemberships", []):
                    user_id = membership["MemberId"]["UserId"]
                    
                    try:
                        user = identity_store.describe_user(
                            IdentityStoreId=identity_store_id,
                            UserId=user_id
                        )
                    except ClientError:
                        continue
                    
                    # Get user's primary email
                    emails = user.get("Emails", [])
                    primary_email = None
                    for entry in emails:
                        if entry.get("Primary"):
                            primary_email = entry.get("Value", "").lower()
                            break
                    if not primary_email and emails:
                        primary_email = emails[0].get("Value", "").lower()
                    
                    if not primary_email:
                        continue
                    
                    # Match email to accounts
                    for account in email_index.get(primary_email, []):
                        if account.get("execution_role_arn"):
                            matched_accounts.append({
                                "account_key": account["account_name"],
                                "account_name": account["account_name"],
                                "execution_role_arn": account["execution_role_arn"],
                                "email": primary_email,
                                "username": user.get("UserName"),
                            })
            
            discovered[classification] = matched_accounts
            LOGGER.info(f"Found {len(matched_accounts)} accounts for {classification}")
            
        except ClientError as e:
            LOGGER.error(f"Failed to discover {classification}: {e}")
            continue
    
    return discovered


def _build_email_index(accounts_map: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Build an index from email to account data."""
    email_index = {}
    seen = set()
    
    for data in accounts_map.values():
        identity = (data.get("account_id"), data.get("execution_role_arn"))
        if identity in seen:
            continue
        seen.add(identity)
        
        emails = set()
        if data.get("email"):
            emails.add(data["email"].lower())
        for entry in data.get("sso", []):
            mail = entry.get("email")
            if mail:
                emails.add(mail.lower())
        
        for mail in emails:
            email_index.setdefault(mail, []).append({
                "account_name": data.get("account_name"),
                "execution_role_arn": data.get("execution_role_arn"),
                "email": mail,
            })
    
    return email_index


def build_merging_context(
    config: Dict[str, Any],
    accounts_map: Dict[str, Dict[str, Any]],
    sandbox_accounts: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """Build the complete context for the merging Lambda."""
    imports_config = config.get("imports", {})
    targets_config = config.get("targets", {})
    sandbox_config = config.get("sandbox", {})
    
    # Build imports map (source name -> execution_role_arn or None for Vault)
    imports = {}
    for name, cfg in imports_config.items():
        if isinstance(cfg, dict):
            imports[name] = cfg.get("execution_role_arn")
        else:
            imports[name] = cfg  # Legacy format: just the ARN
    
    # Build merged_targets map
    merged_targets = {}
    
    # Static targets
    for name, cfg in targets_config.items():
        account_name = cfg.get("account_name") or cfg.get("account") or name
        
        # Look up account in accounts_map
        account_data = accounts_map.get(account_name, {})
        
        merged_targets[name] = {
            "imports": cfg.get("imports", []),
            "syncing": cfg.get("syncing", True),
            "execution_role_arn": cfg.get("execution_role_arn") or account_data.get("execution_role_arn"),
            "account_name": account_name,
            "account_id": account_data.get("account_id"),
        }
    
    # Sandbox targets (from SSO discovery)
    for classification, accounts in sandbox_accounts.items():
        class_config = sandbox_config.get(classification, {})
        class_imports = class_config.get("imports", [])
        
        for account in accounts:
            name = account["account_name"]
            if name not in merged_targets:  # Don't override static targets
                merged_targets[name] = {
                    "imports": class_imports,
                    "syncing": class_config.get("syncing", True),
                    "execution_role_arn": account["execution_role_arn"],
                    "account_name": name,
                    "classification": classification,
                }
    
    return {
        "imports": imports,
        "merged_targets": merged_targets,
        "accounts_by_json_key": {
            name: {
                "account_name": cfg.get("account_name", name),
                "execution_role_arn": cfg.get("execution_role_arn"),
                "account_id": cfg.get("account_id"),
            }
            for name, cfg in merged_targets.items()
        },
        "sandbox_accounts": sandbox_accounts,
        "config_version": config.get("version"),
        "config_timestamp": config.get("timestamp"),
    }


def write_context_to_s3(context: Dict[str, Any]) -> str:
    """Write the merging context to S3."""
    if not SECRETS_BUCKET:
        raise ValueError("SECRETS_BUCKET environment variable is required")
    
    s3 = boto3.client("s3")
    
    s3.put_object(
        Bucket=SECRETS_BUCKET,
        Key=RECORDS_KEY,
        Body=json.dumps(context, indent=2),
        ContentType="application/json",
    )
    
    LOGGER.info(f"Wrote context to s3://{SECRETS_BUCKET}/{RECORDS_KEY}")
    return f"s3://{SECRETS_BUCKET}/{RECORDS_KEY}"


def trigger_merging_lambda(context: Dict[str, Any]) -> Optional[str]:
    """Trigger the secrets-merging Lambda."""
    lambda_client = boto3.client("lambda")
    
    try:
        response = lambda_client.invoke(
            FunctionName=MERGING_FUNCTION_NAME,
            InvocationType="Event",  # Async
            Payload=json.dumps({
                "operation": "merge_secrets",
                "config": {
                    "secrets_bucket": SECRETS_BUCKET,
                    "records_key": RECORDS_KEY,
                },
            }),
        )
        LOGGER.info(f"Triggered {MERGING_FUNCTION_NAME} (status: {response['StatusCode']})")
        return response.get("FunctionError")
    except ClientError as e:
        LOGGER.error(f"Failed to trigger merging lambda: {e}")
        return str(e)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler.
    
    Triggered by:
    - SSM Parameter Store change events
    - Direct invocation (e.g., from GHA workflow)
    - EventBridge schedule
    """
    LOGGER.info(f"Invoked with event: {json.dumps(event, default=str)}")
    
    try:
        # 1. Load config from SSM
        config = load_config_from_ssm()
        
        # 2. Discover accounts
        accounts_map = discover_accounts()
        
        # 3. Discover sandbox accounts via SSO
        sandbox_accounts = discover_sandbox_accounts(
            config.get("sandbox", {}),
            accounts_map
        )
        
        # 4. Build merging context
        merging_context = build_merging_context(config, accounts_map, sandbox_accounts)
        
        # 5. Write context to S3
        context_uri = write_context_to_s3(merging_context)
        
        # 6. Trigger merging Lambda
        error = trigger_merging_lambda(merging_context)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success" if not error else "partial_success",
                "context_uri": context_uri,
                "accounts_discovered": len(set(a["account_id"] for a in accounts_map.values() if a.get("account_id"))),
                "targets_configured": len(merging_context["merged_targets"]),
                "sandbox_classifications": list(sandbox_accounts.keys()),
                "merging_lambda_error": error,
            }),
        }
        
    except Exception as e:
        LOGGER.error(f"Config preprocessing failed: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": str(e),
                "type": type(e).__name__,
            }),
        }
