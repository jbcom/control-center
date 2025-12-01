# Secrets Merging Lambda

AWS Lambda function for merging secrets from multiple sources (AWS Secrets Manager accounts and HashiCorp Vault) into target-specific JSON files stored in S3.

## Overview

This Lambda function:
1. Reads configuration from S3 (permanent records from terraform-aws-organization generator)
2. Fetches secrets from import sources:
   - AWS Secrets Manager (via role assumption into source accounts)
   - HashiCorp Vault (via AppRole or Token authentication)
3. Deep merges secrets according to target configurations
4. Writes merged secrets to S3 as `secrets/{target_name}.json`

The merged secrets in S3 trigger the secrets-syncing Lambda to distribute them to target accounts.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   EventBridge   │────▶│ Merging Lambda   │────▶│    S3 Bucket    │
│  (30 min rate)  │     │                  │     │  secrets/*.json │
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                    ┌────────────┼────────────┐           │
                    ▼            ▼            ▼           ▼
            ┌───────────┐ ┌───────────┐ ┌─────────┐  ┌─────────┐
            │ AWS Acct  │ │ AWS Acct  │ │  Vault  │  │ Syncing │
            │ Secrets   │ │ Secrets   │ │ Secrets │  │ Lambda  │
            └───────────┘ └───────────┘ └─────────┘  └─────────┘
```

## Deployment

### Prerequisites

- AWS SAM CLI installed
- Access to the secrets S3 bucket and KMS key
- IAM permissions to assume roles in source accounts

### Build and Deploy

```bash
# From terraform-modules root
just build-merging
just deploy-merging
```

Or manually:

```bash
cd sam/secrets-merging
sam build --use-container
sam deploy --guided
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| SecretsBucketName | S3 bucket for secrets storage | Yes |
| SecretsBucketArn | ARN of the S3 bucket | Yes |
| KmsKeyArn | KMS key ARN for encryption | Yes |
| RecordsKey | S3 key for configuration JSON | No (default: records/workspaces/secrets/merging.json) |
| VaultUrl | HashiCorp Vault URL | No |
| VaultNamespace | Vault namespace | No |
| ScheduleExpression | EventBridge schedule | No (default: rate(30 minutes)) |

## Configuration Format

The Lambda expects a configuration JSON in S3 with this structure:

```json
{
  "imports": {
    "analytics": "arn:aws:iam::111111111111:role/secrets-import-analytics",
    "vault-secrets": null
  },
  "merged_targets": {
    "Serverless_Stg": {
      "imports": ["analytics", "vault-secrets"],
      "execution_role_arn": "arn:aws:iam::222222222222:role/secrets-sync-role"
    }
  }
}
```

- **imports**: Map of import source names to execution role ARNs (null for Vault sources)
- **merged_targets**: Map of target account names to their configuration
  - **imports**: List of import sources to merge for this target
  - **execution_role_arn**: Role for the syncing Lambda to use

## Local Testing

```bash
# With a test event
sam local invoke SecretsMergingFunction -e events/event.json

# With custom event
sam local invoke SecretsMergingFunction -e - <<< '{"operation": "merge_secrets", "config": {"secrets_bucket": "my-bucket"}}'
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| TM_OPERATION | Set to "merge_secrets" (configured in template) |
| SECRETS_BUCKET | S3 bucket name |
| RECORDS_KEY | S3 key for configuration |
| VAULT_URL | Vault server URL |
| VAULT_NAMESPACE | Vault namespace |
| VAULT_TOKEN | Vault token (or use VAULT_ROLE_ID/SECRET_ID) |

## Integration with terraform-modules Library

This Lambda uses the `terraform_modules` library from this repository. The library is packaged as a Lambda Layer and provides:

- `list_aws_account_secrets`: Fetch secrets from AWS Secrets Manager
- `list_vault_secrets`: Fetch secrets from HashiCorp Vault
- `deepmerge`: Deep merge multiple secret maps

The handler is a thin shim that delegates to `terraform_modules.__main__.lambda_handler`.
