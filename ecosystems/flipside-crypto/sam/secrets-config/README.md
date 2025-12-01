# Secrets Config Preprocessor Lambda

This Lambda preprocesses the secrets pipeline configuration by:
1. Loading config from SSM Parameter Store (pushed by GHA workflow)
2. Discovering AWS accounts via Organizations API
3. Discovering sandbox accounts via SSO/Identity Center group membership
4. Building the complete merging context
5. Writing context to S3 and triggering the secrets-merging Lambda

## Architecture

```
┌─────────────────┐     ┌────────────────┐     ┌─────────────────┐
│  config/secrets │────▶│  GHA Workflow  │────▶│ SSM Parameters  │
│  *.yaml         │     │  (yq → json)   │     │                 │
└─────────────────┘     └────────────────┘     └────────┬────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ secrets-config  │
                                               │     Lambda      │
                                               └────────┬────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        │                               │                               │
                        ▼                               ▼                               ▼
               ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
               │  Organizations  │             │ Identity Center │             │   S3 Context    │
               │  Account List   │             │ Sandbox Groups  │             │    + Trigger    │
               └─────────────────┘             └─────────────────┘             └────────┬────────┘
                                                                                        │
                                                                                        ▼
                                                                               ┌─────────────────┐
                                                                               │ secrets-merging │
                                                                               │     Lambda      │
                                                                               └─────────────────┘
```

## Configuration Files

The config lives in `terraform-modules/config/secrets/`:

### `imports.yaml`
Defines import sources (AWS accounts or Vault mounts):
```yaml
imports:
  analytics:
    execution_role_arn: arn:aws:iam::123:role/secrets-import
  vault-shared:
    execution_role_arn: null
    mount_point: /shared
```

### `targets.yaml`
Defines target accounts and their import sources:
```yaml
targets:
  Serverless_Stg:
    imports: [analytics, vault-shared]
    syncing: true
    execution_role_arn: arn:aws:iam::456:role/secrets-sync
```

### `sandbox.yaml`
Defines sandbox discovery via SSO groups:
```yaml
sandbox_classifications:
  developer:
    discovery:
      method: identity_center
      identity_center:
        group_name: "Developers"
    imports: [analytics]
```

## Triggers

1. **SSM Parameter Change** (primary): EventBridge rule watches for changes to `/terraform-modules/secrets-config/*`
2. **GHA Workflow**: Direct invocation after pushing config to SSM
3. **Schedule** (backup): Runs every 6 hours to catch any missed events

## Deployment

```bash
# From terraform-modules root
cd sam/secrets-config
sam build
sam deploy --guided
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SSM_PREFIX | SSM parameter prefix | /terraform-modules/secrets-config |
| SECRETS_BUCKET | S3 bucket for context/secrets | (required) |
| RECORDS_KEY | S3 key for merging context | records/workspaces/secrets/merging.json |
| MERGING_FUNCTION_NAME | Lambda to trigger | secrets-merging |
| CONTROL_TOWER_EXECUTION_ROLE | Role name for account access | AWSControlTowerExecution |
| IDENTITY_STORE_REGION | Region for SSO operations | us-east-1 |
| SKIP_SANDBOX_DISCOVERY | Skip SSO discovery if "1" | (unset) |

## Flow

1. **Config Change**: User edits `config/secrets/*.yaml` and pushes to main
2. **GHA Workflow**: Converts YAML to JSON, pushes to SSM, triggers Lambda
3. **SSM Event**: EventBridge detects parameter change, triggers Lambda
4. **Account Discovery**: Lambda calls Organizations API to list accounts
5. **Sandbox Discovery**: Lambda queries Identity Center for group membership
6. **Context Build**: Lambda combines config + accounts into merging context
7. **S3 Write**: Context written to `records/workspaces/secrets/merging.json`
8. **Trigger Merging**: Lambda invokes secrets-merging asynchronously

## Local Testing

```bash
# Test with sample event
sam local invoke SecretsConfigFunction -e events/event.json

# Set required env vars for local testing
export SECRETS_BUCKET=my-bucket
export SSM_PREFIX=/test/secrets-config
```
