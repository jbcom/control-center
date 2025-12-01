# SAM Lambda Agent Instructions

## Scope
This `.ruler/` applies to the `sam/` directory containing AWS SAM Lambda applications for secrets management.

## Architecture Overview

### Lambda Functions
- **`secrets-config/`** - Config preprocessor triggered by SSM parameter changes
- **`secrets-merging/`** - Secrets merger triggered by EventBridge schedule
- **`secrets-syncing/`** - Secrets syncer triggered by S3 object creation

### Pipeline Flow
```
config/secrets/*.yaml → GHA → SSM Parameters → secrets-config Lambda
                                                     ↓
                                    S3 (merging context) → secrets-merging Lambda
                                                                   ↓
                                                          S3 (secrets/*.json)
                                                                   ↓
                                                          secrets-syncing Lambda
                                                                   ↓
                                                 Target Account Secrets Manager
```

## File Structure

Each Lambda follows the same pattern:
```
sam/{function-name}/
├── template.yaml       # SAM template (CloudFormation)
├── samconfig.toml      # SAM deployment configuration
├── README.md           # Function documentation
├── events/
│   └── event.json      # Sample test event
└── handler/
    ├── handler.py      # Lambda handler (thin shim)
    └── requirements.txt # Python dependencies
```

## Key Design Principle

**The terraform_modules library IS the Lambda code.** 

Each handler is a thin shim that imports from `lib.terraform_modules`:
```python
# handler/handler.py
from lib.terraform_modules import lambda_handler

def handler(event, context):
    return lambda_handler(event, context)
```

The actual business logic is in `lib/terraform_modules/__main__.py`:
- `lambda_handler()` - Main Lambda entry point
- `_handle_merge_secrets()` - Secrets merging logic
- `_handle_sync_secrets()` - Secrets syncing logic

## Build Commands

```bash
# Build Lambda layer with terraform_modules library
just build-layer

# Build individual applications
just build-config
just build-merging
just build-syncing

# Build all SAM applications
just build-sam
```

## Deploy Commands

```bash
# Deploy individual applications (guided mode)
just deploy-config
just deploy-merging
just deploy-syncing

# Deploy all (in dependency order)
just deploy-sam
```

## Testing

### Validate Templates
```bash
just validate-sam
```

### Local Invocation
```bash
# Invoke with default empty event
just invoke-config-local
just invoke-merging-local
just invoke-syncing-local

# Invoke with custom event
just invoke-config-local event='{"source": "manual"}'
```

### Sample Events
Edit the files in `events/event.json` for realistic test scenarios.

## Template Configuration

### Environment Variables
```yaml
Environment:
  Variables:
    TM_OPERATION: merge_secrets  # or sync_secrets
    TM_VENDORS_SOURCE: asm       # Read vendor secrets from ASM
    TM_S3_BUCKET: !Ref S3Bucket
    PYTHONPATH: /opt/python      # Lambda layer
```

### Common Parameters
```yaml
Parameters:
  Environment:
    Type: String
    Default: production
  S3BucketName:
    Type: String
    Description: S3 bucket for secrets data
```

### IAM Permissions
Each Lambda needs specific permissions:
- **secrets-config**: SSM read, S3 write, Lambda invoke
- **secrets-merging**: S3 read/write, Vault access, cross-account assume
- **secrets-syncing**: S3 read, cross-account assume, Secrets Manager write

## Vendor Secrets (Lambda Mode)

Lambdas read vendor secrets from AWS Secrets Manager instead of Doppler:

```yaml
Environment:
  Variables:
    TM_VENDORS_SOURCE: asm
    TM_VENDORS_PREFIX: /vendors/
```

Required IAM:
```yaml
- Effect: Allow
  Action:
    - secretsmanager:GetSecretValue
    - secretsmanager:ListSecrets
  Resource: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:/vendors/*"
```

## Code Changes

### Modifying Lambda Logic
1. Edit `lib/terraform_modules/__main__.py` (NOT `handler/handler.py`)
2. Test locally with `just invoke-*-local`
3. Rebuild with `just build-sam`
4. Deploy with `just deploy-*`

### Modifying SAM Templates
1. Edit `template.yaml` in the function directory
2. Validate with `just validate-sam`
3. Deploy with `just deploy-*`

### Adding New Lambda
1. Create directory structure under `sam/`
2. Create `template.yaml` with SAM resources
3. Create thin handler shim in `handler/handler.py`
4. Add `TM_OPERATION` env var for routing
5. Add handler logic in `lib/terraform_modules/__main__.py`
6. Add build/deploy targets to `justfile`

## Don't Do
- Don't put business logic in `handler/handler.py` - use the library
- Don't hardcode secrets in templates - use ASM or SSM
- Don't forget to rebuild after library changes
- Don't deploy without validating templates first
- Don't use `--use-container` unnecessarily (slower builds)

## MCP Tools for SAM

Use these MCP servers when working on SAM:
- **aws-serverless** - SAM operations, Lambda deployment
- **lambda-tool** - Lambda function management
- **cloudformation** - Template validation, stack operations
- **cloudwatch** - Lambda logs and metrics
- **iam** - Permission analysis
