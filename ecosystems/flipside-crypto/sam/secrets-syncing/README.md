# Secrets Syncing Lambda

AWS Lambda function for syncing merged secrets from S3 to target AWS accounts' Secrets Manager.

## Overview

This Lambda function:
1. Is triggered by S3 ObjectCreated events when the merging Lambda writes new `secrets/{target}.json` files
2. Reads the merged secrets from S3
3. Looks up the target account's execution role ARN from configuration
4. Assumes the role in the target account
5. Syncs secrets to the target account's Secrets Manager (create/update)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    S3 Bucket    │────▶│ Syncing Lambda   │────▶│  Target Account │
│ secrets/*.json  │     │                  │     │ Secrets Manager │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │ STS AssumeRole │
                        │ Target Account │
                        └────────────────┘
```

## Deployment

### Prerequisites

- AWS SAM CLI installed
- Access to the secrets S3 bucket and KMS key
- IAM permissions to assume roles in target accounts
- (Optional) Terraform Modules Layer ARN from the merging stack

### Build and Deploy

```bash
# From terraform-modules root
just build-syncing
just deploy-syncing
```

Or manually:

```bash
cd sam/secrets-syncing
sam build --use-container
sam deploy --guided
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| SecretsBucketName | S3 bucket containing merged secrets | Yes |
| SecretsBucketArn | ARN of the S3 bucket | Yes |
| KmsKeyArn | KMS key ARN for decryption | Yes |
| TerraformModulesLayerArn | Shared layer ARN (if using existing) | No |
| TargetAccount | Target account name (for per-account deployment) | No |
| ExecutionRoleArn | Role ARN to assume in target | No |

## Invocation Modes

### S3 Trigger (Primary)

The Lambda is triggered when the merging Lambda writes `secrets/{target}.json` to S3:

```json
{
  "Records": [{
    "s3": {
      "bucket": {"name": "secrets-bucket"},
      "object": {"key": "secrets/Serverless_Stg.json"}
    }
  }]
}
```

The target account name is extracted from the S3 key, and the execution role ARN is looked up from the merging configuration.

### Direct Invocation

Can also be invoked directly with explicit configuration:

```json
{
  "operation": "sync_secrets",
  "config": {
    "secrets_bucket": "my-bucket",
    "target_account": "Serverless_Stg",
    "execution_role_arn": "arn:aws:iam::123456789012:role/secrets-sync-role"
  }
}
```

## Local Testing

```bash
# With S3 trigger event
sam local invoke SecretsSyncingFunction -e events/event.json

# With direct invocation
sam local invoke SecretsSyncingFunction -e - <<< '{
  "operation": "sync_secrets",
  "config": {
    "secrets_bucket": "my-bucket",
    "target_account": "MyAccount",
    "execution_role_arn": "arn:aws:iam::123456789012:role/my-role"
  }
}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| TM_OPERATION | Set to "sync_secrets" (configured in template) |
| SECRETS_BUCKET | S3 bucket name |
| TARGET_ACCOUNT | Target account name (optional, can be from S3 key) |
| EXECUTION_ROLE_ARN | Role to assume (optional, can be looked up) |
| RECORDS_KEY | S3 key for configuration (for role lookup) |

## Execution Role Lookup

When `EXECUTION_ROLE_ARN` is not provided, the Lambda looks up the role from the merging configuration:

1. Fetches `records/workspaces/secrets/merging.json` from S3
2. Looks for the target account in `accounts_by_json_key` or `merged_targets`
3. Uses the `execution_role_arn` from that configuration

This allows a single Lambda to sync to multiple accounts without per-account deployment.

## Integration with terraform-modules Library

This Lambda uses the `terraform_modules` library from this repository. The library is packaged as a Lambda Layer and provides the sync operation logic in `terraform_modules.__main__._handle_sync_secrets`.

The handler is a thin shim that delegates to `terraform_modules.__main__.lambda_handler`.

## Per-Account vs Shared Deployment

### Shared Deployment (Recommended)

Deploy a single Lambda that handles all accounts:
- Set S3 trigger for `secrets/*.json` prefix
- Execution role ARN is looked up per invocation
- Simpler management, single deployment

### Per-Account Deployment

Deploy separate Lambdas per target account:
- Use `TargetAccount` and `ExecutionRoleArn` parameters
- S3 trigger filtered to `secrets/{TargetAccount}.json`
- More isolation, separate IAM roles per function
