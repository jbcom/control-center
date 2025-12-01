import json
import os
import sys
from typing import Any, Dict, Optional

from terraform_modules.logging import Logging
from terraform_modules.settings import TERRAFORM_MODULES_DIR
from terraform_modules.terraform_data_source import TerraformDataSource
from terraform_modules.terraform_null_resource import TerraformNullResource
from terraform_modules.utils import FilePath, get_available_methods, get_process_output


def invoke(cls, method):
    invocation = getattr(cls, method, None)

    if invocation is None:
        raise AttributeError(f"No method {method} in the class {cls}")

    return cls.exit_run(invocation())


def invoke_method_with_kwargs(method_name: str, **kwargs) -> Any:
    """
    Invoke a method from the registry with explicit kwargs instead of stdin/env.

    This is the core function for Lambda handlers - it creates an instance
    of TerraformDataSource configured for non-interactive use and invokes
    the requested method directly with the provided parameters.
    """
    avail_tds = get_available_methods(TerraformDataSource)
    avail_nr = get_available_methods(TerraformNullResource)

    if method_name in avail_tds:
        # Create data source without stdin, with console logging for Lambda
        ds = TerraformDataSource(to_console=True, to_file=False, from_stdin=False)
        method = getattr(ds, method_name, None)
        if method is None:
            raise AttributeError(f"Method {method_name} not found in TerraformDataSource")
        # Call method with exit_on_completion=False to get return value
        return method(exit_on_completion=False, **kwargs)
    elif method_name in avail_nr:
        nr = TerraformNullResource(to_console=True, to_file=False)
        method = getattr(nr, method_name, None)
        if method is None:
            raise AttributeError(f"Method {method_name} not found in TerraformNullResource")
        return method(exit_on_completion=False, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method_name}. Available: {list(avail_tds.keys()) + list(avail_nr.keys())}")


def lambda_handler(event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """
    AWS Lambda entry point for terraform_modules.

    Supports two invocation modes:

    1. Direct method invocation:
       {
         "method": "list_aws_account_secrets",
         "kwargs": {"execution_role_arn": "arn:aws:iam::...", "get_secrets": true}
       }

    2. Secrets operations (merging/syncing):
       {
         "operation": "merge_secrets" | "sync_secrets",
         "config": { ... operation-specific config ... }
       }

    Environment variables can provide defaults:
    - TM_METHOD: Default method to invoke
    - TM_OPERATION: Default operation (merge_secrets, sync_secrets)
    - SECRETS_BUCKET: S3 bucket for secrets operations
    - RECORDS_KEY: S3 key for records JSON (e.g., "records/workspaces/secrets.json")
    """
    logging = Logging(to_console=True, to_file=False, logger_name="lambda_handler")
    logger = logging.logger

    logger.info(f"Lambda invoked with event: {json.dumps(event, default=str)}")
    if context:
        logger.info(f"Function: {context.function_name}, Request ID: {context.aws_request_id}")

    try:
        # Check for operation mode (merging/syncing)
        operation = event.get("operation") or os.environ.get("TM_OPERATION")

        if operation == "merge_secrets":
            result = _handle_merge_secrets(event, logger)
        elif operation == "sync_secrets":
            result = _handle_sync_secrets(event, logger)
        else:
            # Direct method invocation mode
            method_name = event.get("method") or os.environ.get("TM_METHOD")
            if not method_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {
                            "error": "No method or operation specified",
                            "available_operations": ["merge_secrets", "sync_secrets"],
                            "usage": "Provide 'method' or 'operation' in event, or TM_METHOD/TM_OPERATION env var",
                        }
                    ),
                }

            kwargs = event.get("kwargs", {})
            # Also check for env var overrides for common parameters
            for env_key in ["EXECUTION_ROLE_ARN", "ROLE_SESSION_NAME"]:
                if env_key in os.environ and env_key.lower() not in kwargs:
                    kwargs[env_key.lower()] = os.environ[env_key]

            logger.info(f"Invoking method: {method_name} with kwargs: {kwargs}")
            result = invoke_method_with_kwargs(method_name, **kwargs)

        return {"statusCode": 200, "body": json.dumps(result, default=str) if not isinstance(result, str) else result}

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": str(e), "type": type(e).__name__})}


def _handle_merge_secrets(event: Dict[str, Any], logger) -> Dict[str, Any]:
    """
    Handle secrets merging operation.

    Reads context from S3 (permanent records), fetches secrets from import sources
    (AWS accounts or Vault), merges them using deepmerge, and writes results to S3.

    Expected config (from event or environment):
    - SECRETS_BUCKET: S3 bucket containing records and for writing merged secrets
    - RECORDS_KEY: S3 key for the merging context JSON
    - VAULT_URL, VAULT_NAMESPACE, VAULT_TOKEN/VAULT_ROLE_ID/VAULT_SECRET_ID: For Vault imports
    """
    import boto3

    config = event.get("config", {})
    secrets_bucket = config.get("secrets_bucket") or os.environ.get("SECRETS_BUCKET")
    records_key = config.get("records_key") or os.environ.get("RECORDS_KEY", "records/workspaces/secrets/merging.json")

    if not secrets_bucket:
        raise ValueError("SECRETS_BUCKET is required")

    s3 = boto3.client("s3")

    # Load context from permanent record
    logger.info(f"Loading context from s3://{secrets_bucket}/{records_key}")
    try:
        response = s3.get_object(Bucket=secrets_bucket, Key=records_key)
        context = json.loads(response["Body"].read())
    except Exception as e:
        logger.error(f"Failed to load context: {e}")
        raise ValueError(f"Failed to load context from s3://{secrets_bucket}/{records_key}: {e}")

    imports_data = context.get("imports", {})
    merged_targets = context.get("merged_targets", {})

    logger.info(f"Processing {len(imports_data)} import sources for {len(merged_targets)} targets")

    # Fetch secrets from all import sources
    import_sources = {}

    for import_source, execution_role_arn in imports_data.items():
        logger.info(f"Fetching secrets from import source: {import_source}")

        if execution_role_arn:
            # AWS Secrets Manager source
            secrets = invoke_method_with_kwargs(
                "list_aws_account_secrets",
                execution_role_arn=execution_role_arn,
                get_secrets=True,
                no_empty_secrets=True,
            )
            import_sources[import_source] = secrets.get("secrets", secrets) if isinstance(secrets, dict) else secrets
        else:
            # Vault source
            secrets = invoke_method_with_kwargs(
                "list_vault_secrets",
                mount_point=f"/{import_source}",
            )
            import_sources[import_source] = secrets.get("secrets", secrets) if isinstance(secrets, dict) else secrets

    logger.info(f"Fetched secrets from {len(import_sources)} sources")

    # Merge secrets for each target and write to S3
    results = {}
    for target_name, target_config in merged_targets.items():
        target_imports = target_config.get("imports", [])
        logger.info(f"Merging secrets for target: {target_name} from {len(target_imports)} sources")

        source_maps = [import_sources.get(src, {}) for src in target_imports if src in import_sources]

        if source_maps:
            merged = invoke_method_with_kwargs(
                "deepmerge",
                source_maps=source_maps,
            )
            merged_secrets = merged.get("merged_maps", merged) if isinstance(merged, dict) else merged
        else:
            merged_secrets = {}

        # Write merged secrets to S3
        s3_key = f"secrets/{target_name}.json"
        logger.info(f"Writing {len(merged_secrets)} merged secrets to s3://{secrets_bucket}/{s3_key}")

        s3.put_object(
            Bucket=secrets_bucket,
            Key=s3_key,
            Body=json.dumps(merged_secrets),
            ContentType="application/json",
        )

        results[target_name] = {
            "secrets_count": len(merged_secrets),
            "s3_key": s3_key,
        }

    return {
        "status": "success",
        "targets_processed": len(results),
        "results": results,
    }


def _handle_sync_secrets(event: Dict[str, Any], logger) -> Dict[str, Any]:
    """
    Handle secrets syncing operation.

    This is typically triggered by S3 object creation. Reads merged secrets
    from S3 and syncs them to the target AWS account's Secrets Manager.

    For S3 trigger events, extracts bucket/key from the event.
    For direct invocation, expects config with target_account and execution_role_arn.

    The execution_role_arn can be:
    1. Provided directly in config or EXECUTION_ROLE_ARN env var
    2. Looked up from the merging records in S3 (accounts_by_json_key)
    """
    import boto3
    from botocore.exceptions import ClientError

    config = event.get("config", {})

    # Check if this is an S3 trigger event
    if "Records" in event:
        record = event["Records"][0]
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")

        # Extract target from key (e.g., "secrets/MyAccount.json" -> "MyAccount")
        if key and key.startswith("secrets/") and key.endswith(".json"):
            target_account = key[8:-5]  # Remove "secrets/" prefix and ".json" suffix
        else:
            raise ValueError(f"Invalid S3 key format: {key}")
    else:
        bucket = config.get("secrets_bucket") or os.environ.get("SECRETS_BUCKET")
        target_account = config.get("target_account") or os.environ.get("TARGET_ACCOUNT")
        key = f"secrets/{target_account}.json"

    if not bucket:
        raise ValueError("SECRETS_BUCKET is required")
    if not target_account:
        raise ValueError("TARGET_ACCOUNT is required (from S3 key or config)")

    execution_role_arn = config.get("execution_role_arn") or os.environ.get("EXECUTION_ROLE_ARN")

    # If no execution_role_arn provided, look it up from the merging records
    s3 = boto3.client("s3")

    if not execution_role_arn:
        records_key = config.get("records_key") or os.environ.get(
            "RECORDS_KEY", "records/workspaces/secrets/merging.json"
        )
        logger.info(f"Looking up execution_role_arn from s3://{bucket}/{records_key}")

        try:
            response = s3.get_object(Bucket=bucket, Key=records_key)
            context = json.loads(response["Body"].read())

            # Look for the account in merged_targets or accounts_by_json_key
            accounts_by_key = context.get("accounts_by_json_key", {})
            merged_targets = context.get("merged_targets", {})

            if target_account in accounts_by_key:
                execution_role_arn = accounts_by_key[target_account].get("execution_role_arn")
            elif target_account in merged_targets:
                execution_role_arn = merged_targets[target_account].get("execution_role_arn")

            if not execution_role_arn:
                raise ValueError(f"Could not find execution_role_arn for {target_account} in records")

            logger.info(f"Found execution_role_arn: {execution_role_arn}")

        except Exception as e:
            logger.error(f"Failed to lookup execution_role_arn: {e}")
            raise ValueError(f"execution_role_arn not provided and lookup failed: {e}")

    logger.info(f"Syncing secrets for {target_account} from s3://{bucket}/{key}")

    sts = boto3.client("sts")

    # Get secrets from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    secrets_data = json.loads(response["Body"].read())

    logger.info(f"Found {len(secrets_data)} secrets to sync")

    # Assume role in target account
    logger.info(f"Assuming role: {execution_role_arn}")
    assumed_role = sts.assume_role(RoleArn=execution_role_arn, RoleSessionName="SecretsSyncSession")
    credentials = assumed_role["Credentials"]

    # Create Secrets Manager client with assumed role
    sm = boto3.client(
        "secretsmanager",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    # Sync each secret
    synced = 0
    errors = []

    for secret_name, secret_value in secrets_data.items():
        try:
            # Normalize value to string
            if isinstance(secret_value, (dict, list)):
                secret_value = json.dumps(secret_value)
            elif not isinstance(secret_value, str):
                secret_value = str(secret_value)

            # Try to update existing secret, create if not exists
            try:
                sm.put_secret_value(SecretId=secret_name, SecretString=secret_value)
                logger.debug(f"Updated secret: {secret_name}")
            except sm.exceptions.ResourceNotFoundException:
                sm.create_secret(
                    Name=secret_name,
                    SecretString=secret_value,
                    ForceOverwriteReplicaSecret=True,
                )
                logger.debug(f"Created secret: {secret_name}")

            synced += 1

        except ClientError as e:
            logger.error(f"Failed to sync secret {secret_name}: {e}")
            errors.append({"secret": secret_name, "error": str(e)})

    return {
        "status": "success" if not errors else "partial_success",
        "target_account": target_account,
        "synced_count": synced,
        "error_count": len(errors),
        "errors": errors[:10] if errors else [],  # Limit errors in response
    }


def main():
    avail_tds = get_available_methods(TerraformDataSource)
    avail_nr = get_available_methods(TerraformNullResource)

    help_txt = f"""\
{sys.argv[0]} Terraform Modules CLI

Acts as a bridge against Python extensions of Terraform data sources and null resources

terraform_modules: Generates all Terraform modules\n
"""

    help_txt += "Data Sources:\n\n"
    for method_name, method_docs in avail_tds.items():
        if method_name.startswith("__") or "NOPARSE" in method_docs:
            continue

        try:
            help_txt += f"\t{method_name}: {method_docs.splitlines()[0]}\n"
        except AttributeError:
            continue

    help_txt += "\nResources:\n\n"
    for method_name, method_docs in avail_nr.items():
        if method_name.startswith("_"):
            continue

        try:
            help_txt += f"\t{method_name}: {method_docs.splitlines()[0]}\n"
        except AttributeError:
            continue

    method = "_".join(sys.argv[1:])

    if method == "terraform_modules":
        logging = Logging(
            to_console=True, to_file=False, logger_name="terraform_modules", log_file_name="terraform_modules.log"
        )
        logger = logging.logger
        logged_statement = logging.logged_statement
        nr = TerraformNullResource(to_console=True, to_file=False, logging=logging)

        logger.info(f"Checking for existing Terraform module directories in {TERRAFORM_MODULES_DIR}")
        existing_tf_library_modules = nr.ds.scan_dir(
            files_path=TERRAFORM_MODULES_DIR,
            decode=False,
            allowed_extensions=[".library-module"],
            reject_dotfiles=False,
            paths_only=True,
            exit_on_completion=False,
        )

        logged_statement("Existing Terraform modules", json_data=existing_tf_library_modules)

        new_tf_library_modules = set()

        all_terraform_module_resources = nr.terraform_module_resources + nr.ds.terraform_module_resources

        def update_module_dir(mp: FilePath):
            local_module_path = nr.local_path(mp)
            local_module_parent = local_module_path.parent

            flag_file_path = local_module_parent.joinpath(".library-module")

            nr.update_file(
                file_path=flag_file_path,
                file_data="# Gitops Library Terraform Module",
            )

            new_tf_library_modules.add(flag_file_path)

            stdout, stderr = get_process_output(f"terraform-docs markdown table {local_module_parent}")

            if stdout is None:
                raise RuntimeError(f"Failed to generate Terraform docs: {stderr}")

            nr.update_file(file_path=local_module_parent.joinpath("README.md"), file_data=stdout)

        for terraform_module_resources in all_terraform_module_resources:
            if terraform_module_resources.generation_forbidden:
                logger.warning(f"f[{terraform_module_resources.module_name}] Generation forbidden, skipping")
                continue

            for (
                target_module_path,
                target_module_json,
            ) in terraform_module_resources.get_modules_to_copy_variables_to():
                logger.info(
                    f"[{terraform_module_resources.module_name}] Saving Terraform module variables"
                    f" to {target_module_path}"
                )

                nr.update_file(
                    file_path=target_module_path,
                    file_data=target_module_json,
                    allow_encoding=True,
                )

                update_module_dir(target_module_path)

            for (
                foreach_module_path,
                foreach_module_json,
            ) in terraform_module_resources.get_foreach():
                logger.info(
                    f"[{terraform_module_resources.module_name}] Saving Terraform foreach module"
                    f" to {foreach_module_path}"
                )

                nr.update_file(
                    file_path=foreach_module_path,
                    file_data=foreach_module_json,
                    allow_encoding=True,
                )

                update_module_dir(foreach_module_path)

            module_path = terraform_module_resources.get_module_path()
            logger.info(f"[{terraform_module_resources.module_name}] Saving Terraform module to {module_path}")

            nr.update_file(
                file_path=module_path,
                file_data=terraform_module_resources.get_mixed(),
                allow_encoding=True,
            )

            update_module_dir(module_path)

        logged_statement(f"New Terraform library modules: {new_tf_library_modules}")

        orphan_tf_library_modules = set(existing_tf_library_modules) - new_tf_library_modules

        for library_module in orphan_tf_library_modules:
            library_module_dir = nr.local_path(library_module).parent
            logger.warning(f"Deleting orphan library module directory {library_module_dir}")
            nr.delete_dir(dir_path=library_module_dir, exit_on_completion=False)

        sys.exit(0)
    elif method in avail_tds:
        ds = TerraformDataSource(to_console=False, to_file=True, from_stdin=True)
        return invoke(ds, method)
    elif method in avail_nr:
        nr = TerraformNullResource(to_console=True, to_file=True)
        return invoke(nr, method)
    else:
        logging = Logging(to_console=True, to_file=False)
        logging.logger.info(help_txt)
        sys.exit(1)


if __name__ == "__main__":
    main()
