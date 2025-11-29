# Terraform Modules Migration - Agent Orchestration

## Overview
Migration of cloud-specific operations from `FlipsideCrypto/terraform-modules` to `jbcom/jbcom-control-center` vendor-connectors package.

## Control Repository
- **Source**: https://github.com/FlipsideCrypto/terraform-modules (cloned at /tmp/terraform-modules)
- **Target**: /workspace/packages/vendor-connectors/

## Completed Migrations

### AWS Package (✅ DONE)
- `aws/__init__.py` - Base connector, sessions, Secrets Manager
- `aws/organizations.py` - Organizations, Control Tower accounts
- `aws/sso.py` - IAM Identity Center users, groups, permission sets
- `aws/s3.py` - S3 objects, buckets, features

### Google Package (✅ DONE)  
- `google/__init__.py` - Base connector, authentication
- `google/workspace.py` - Workspace users, groups
- `google/cloud.py` - Projects, folders, IAM
- `google/billing.py` - Billing accounts
- `google/services.py` - GKE, Compute, Storage, SQL, Pub/Sub, KMS

### GitHub (✅ DONE)
- `github/__init__.py` - Extended with members, repos, teams

## Remaining Migrations

### Agent 1: Slack Operations
- **File**: AGENT_SLACK_OPERATIONS.md
- **Task**: Extend slack/__init__.py with users, usergroups, conversations
- **Priority**: HIGH

### Agent 2: Vault Operations  
- **File**: AGENT_VAULT_OPERATIONS.md
- **Task**: Extend vault/__init__.py with AWS IAM roles
- **Priority**: MEDIUM

### Agent 3: AWS CodeDeploy
- **File**: AGENT_AWS_CODEDEPLOY.md
- **Task**: Create new aws/codedeploy.py module
- **Priority**: MEDIUM

### Agent 4: AWS Secrets Manager
- **File**: AGENT_AWS_SECRETS.md
- **Task**: Extend AWSConnector with create/update/delete secrets
- **Priority**: HIGH

## NOT Migrating (Serverless/SAM candidates)
These are FlipsideCrypto-specific business logic, not generic connectors:
- `sync_flipsidecrypto_users_and_groups` - Should be SAM function
- `get_flipsidecrypto_team_*` - Should be SAM function
- `get_new_aws_controltower_accounts_from_google` - Should be SAM function

## Spawn Commands
```bash
# Slack
/workspace/scripts/fleet-manager.sh spawn https://github.com/jbcom/jbcom-control-center "$(cat .cursor/agents/terraform-modules-migration/AGENT_SLACK_OPERATIONS.md)" main

# Vault
/workspace/scripts/fleet-manager.sh spawn https://github.com/jbcom/jbcom-control-center "$(cat .cursor/agents/terraform-modules-migration/AGENT_VAULT_OPERATIONS.md)" main

# CodeDeploy
/workspace/scripts/fleet-manager.sh spawn https://github.com/jbcom/jbcom-control-center "$(cat .cursor/agents/terraform-modules-migration/AGENT_AWS_CODEDEPLOY.md)" main

# Secrets
/workspace/scripts/fleet-manager.sh spawn https://github.com/jbcom/jbcom-control-center "$(cat .cursor/agents/terraform-modules-migration/AGENT_AWS_SECRETS.md)" main
```

## Verification
After all agents complete:
1. Run full test suite: `uv run python -m pytest packages/vendor-connectors/tests -v`
2. Run linter: `uv run ruff check packages/vendor-connectors/src`
3. Create consolidated PR
