# Secrets Pipeline - SAM Applications

Three Lambda functions that form the secrets synchronization pipeline:

1. **secrets-config** - Loads config from SSM, discovers accounts, triggers merging
2. **secrets-merging** - Fetches and merges secrets from import sources  
3. **secrets-syncing** - Syncs merged secrets to target AWS accounts

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GitHub Actions │────▶│  SSM Parameters  │────▶│  secrets-config │
│  (config push)  │     │  /terraform-     │     │  Lambda         │
└─────────────────┘     │  modules/secrets │     └────────┬────────┘
                        └──────────────────┘              │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  S3 Trigger     │◀────│  S3 Bucket       │◀────│  secrets-merging│
│  secrets/*.json │     │  (artifacts)     │     │  Lambda         │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │                       ▲                        │
         ▼                       │                        │
┌─────────────────┐              │              ┌─────────▼─────────┐
│  secrets-syncing│──────────────┘              │  /vendors/*       │
│  Lambda         │                             │  ASM Secrets      │
└────────┬────────┘                             │  (Vault creds)    │
         │                                      └───────────────────┘
         ▼
┌─────────────────┐
│  Target Account │
│  Secrets Manager│
└─────────────────┘
```

## Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed (`pip install aws-sam-cli`)
- GitHub repository: `FlipsideCrypto/terraform-modules`

## Initial Setup - Pipeline Bootstrap

Use SAM's built-in pipeline bootstrap to create the required AWS infrastructure:

```bash
cd sam/

# Bootstrap with GitHub Actions OIDC (recommended - no secrets needed)
sam pipeline bootstrap \
  --stage prod \
  --region us-east-1 \
  --permissions-provider oidc \
  --oidc-provider github-actions \
  --github-org FlipsideCrypto \
  --github-repo terraform-modules \
  --deployment-branch main \
  --confirm-changeset
```

This creates:
- **S3 Artifacts Bucket** - Used for SAM deployments AND secrets storage
- **OIDC Provider** - GitHub Actions can assume roles without IAM keys
- **Pipeline Execution Role** - For SAM to deploy CloudFormation
- **CloudFormation Execution Role** - For stack resource creation

### After Bootstrap

The bootstrap outputs the ARNs you need. Update `samconfig.toml`:

```toml
[prod.pipeline_bootstrap.parameters]
pipeline_execution_role_arn = "arn:aws:iam::ACCOUNT:role/aws-sam-cli-managed-prod-pipe-PipelineExecutionRole-XXX"
cloudformation_execution_role_arn = "arn:aws:iam::ACCOUNT:role/aws-sam-cli-managed-prod-CloudFormationExecutionR-XXX"
artifacts_bucket_arn = "arn:aws:s3:::aws-sam-cli-managed-prod-pipeline-artifactsbucket-XXX"
```

### Generate CI/CD Workflow

```bash
sam pipeline init
```

This generates `.github/workflows/pipeline.yaml` configured for your bootstrap.

## Manual Deployment

If you need to deploy manually:

```bash
# Build all applications
sam build --template-file secrets-merging/template.yaml

# Deploy (uses samconfig.toml)
sam deploy --config-env prod
```

## Configuration

### Environment Variables

All Lambdas use minimal configuration - most values are discovered at runtime:

| Variable | Description |
|----------|-------------|
| `TM_VENDORS_SOURCE` | `asm` - Load vendor secrets from ASM `/vendors/*` |
| `SECRETS_BUCKET` | S3 bucket for context and secrets (from bootstrap) |

### Vendor Secrets (from `/vendors/*`)

These are pushed to ASM by `terraform-organization-administration`:
- `HCP_CLIENT_ID`, `HCP_CLIENT_SECRET` - Vault authentication
- `GITHUB_TOKEN` - GitHub API access
- Other vendor credentials as needed

### SSM Configuration (from GHA workflow)

Config files in `../config/secrets/` are pushed to SSM by GitHub Actions:
- `/terraform-modules/secrets-config/imports` - Import source definitions
- `/terraform-modules/secrets-config/targets` - Target account mappings
- `/terraform-modules/secrets-config/sandbox` - Sandbox discovery config

## Development

### Local Testing

```bash
# Invoke locally with test event
sam local invoke SecretsConfigFunction -e secrets-config/events/event.json

# Start local API (if applicable)
sam local start-api
```

### Adding New Functions

1. Create new directory under `sam/`
2. Add `template.yaml`, `handler/handler.py`
3. Update `justfile` build/deploy targets
4. Run `sam validate` and `sam build`

## Troubleshooting

### OIDC Authentication Issues

Ensure the GitHub Actions workflow has:
```yaml
permissions:
  id-token: write
  contents: read
```

### Missing Vendor Secrets

Verify `/vendors/*` secrets exist in ASM:
```bash
aws secretsmanager list-secrets --filter Key=name,Values=/vendors/
```

### Lambda Timeout

- secrets-config: 5 min (account discovery)
- secrets-merging: 15 min (Vault + ASM fetches)
- secrets-syncing: 10 min (per-account sync)
