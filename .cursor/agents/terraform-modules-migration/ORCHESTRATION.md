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

---

## Active Agents (Spawned 2025-11-29)

### QC Verification Agents

| Agent ID | Task | Issue | Branch |
|----------|------|-------|--------|
| `bc-09948622-174f-4d77-b79c-afe3cb99db40` | Verify AWS operations 1:1 | [#230](https://github.com/jbcom/jbcom-control-center/issues/230) | `cursor/verify-aws-operations-against-terraform-modules-f7e6` |
| `bc-f5391b3e-5208-4c16-94f8-ee24601f04be` | Verify Google operations 1:1 | [#231](https://github.com/jbcom/jbcom-control-center/issues/231) | `cursor/verify-google-operations-against-terraform-modules-e499` |

### Migration Agents

| Agent ID | Task | Issue | Branch |
|----------|------|-------|--------|
| `bc-911ea566-1b4b-4205-94ba-e4cb244e4b0e` | Migrate Slack operations | [#232](https://github.com/jbcom/jbcom-control-center/issues/232) | `cursor/migrate-and-refactor-slack-connector-40fe` |
| `bc-fbdd5365-b399-419c-a5a9-55cd8392b3fd` | Migrate Vault operations | [#233](https://github.com/jbcom/jbcom-control-center/issues/233) | `cursor/migrate-vault-connector-with-aws-iam-methods-934b` |
| `bc-445d072f-add9-4bab-992a-02f759d8a6ea` | Create AWS CodeDeploy module | [#234](https://github.com/jbcom/jbcom-control-center/issues/234) | `cursor/migrate-aws-codedeploy-to-new-module-af98` |
| `bc-9393bfef-686c-4274-a5c1-731a854e0d88` | Extend AWS Secrets Manager | [#235](https://github.com/jbcom/jbcom-control-center/issues/235) | `cursor/extend-aws-secrets-manager-operations-d3b2` |

---

## NOT Migrating (Serverless/SAM candidates)
These are FlipsideCrypto-specific business logic, not generic connectors:
- `sync_flipsidecrypto_users_and_groups` - Should be SAM function
- `get_flipsidecrypto_team_*` - Should be SAM function
- `get_new_aws_controltower_accounts_from_google` - Should be SAM function

## Monitor Agents
```bash
# List all agents
/workspace/scripts/fleet-manager.sh list

# Check specific agent status
/workspace/scripts/fleet-manager.sh status bc-09948622-174f-4d77-b79c-afe3cb99db40

# Send followup to agent
/workspace/scripts/fleet-manager.sh followup bc-09948622-174f-4d77-b79c-afe3cb99db40 "Please also check X"
```

## Verification
After all agents complete:
1. Run full test suite: `uv run python -m pytest packages/vendor-connectors/tests -v`
2. Run linter: `uv run ruff check packages/vendor-connectors/src`
3. Review and merge PRs from each agent branch
