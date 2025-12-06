# FlipsideCrypto Infrastructure Maintenance

## Overview

The `ecosystems/flipside-crypto/` directory contains FlipsideCrypto's cloud infrastructure. This control center is the source of truth.

## Structure

```
ecosystems/flipside-crypto/
├── terraform/
│   ├── modules/           # 100+ reusable modules
│   │   ├── aws/           # 70+ AWS modules
│   │   ├── google/        # 38 GCP modules
│   │   └── github/        # GitHub management
│   └── workspaces/        # 44 live workspaces
├── sam/                   # AWS Lambda apps
├── lib/terraform_modules/ # Python library
└── config/                # State paths, pipelines
```

## jbcom Package Dependencies

The FSC infrastructure uses these jbcom packages:

| Package | Used In | Purpose |
|---------|---------|---------|
| `vendor-connectors` | lib/, sam/ | AWS, GCP, Slack clients |
| `lifecyclelogging` | lib/, sam/ | Structured logging |
| `extended-data-types` | lib/ | Config utilities |

### Updating Package Versions

When jbcom packages are released, update FSC:

```bash
# Check current versions
grep -r "vendor-connectors\|lifecyclelogging\|extended-data-types" \
  ecosystems/flipside-crypto/lib/pyproject.toml \
  ecosystems/flipside-crypto/sam/*/handler/requirements.txt

# Update to new version
# Edit pyproject.toml or requirements.txt

# Test
cd ecosystems/flipside-crypto/lib
pip install -e .
pytest
```

## Token Usage

FSC operations use `GITHUB_FSC_TOKEN` (if pushing to FlipsideCrypto repos):

```bash
GH_TOKEN="$GITHUB_FSC_TOKEN" gh <command> --repo FlipsideCrypto/<repo>
```

The `agentic` CLI handles this automatically.

## Terraform Operations

```bash
# Navigate to workspace
cd ecosystems/flipside-crypto/terraform/workspaces/terraform-aws-organization/<workspace>

# Plan
terraform plan

# Apply (requires AWS creds)
terraform apply
```

### State Management

State is in S3:
```
s3://flipside-crypto-internal-tooling/terraform/state/{pipeline}/workspaces/{workspace}/
```

**Never modify state paths in `config/state-paths.yaml`** - they're immutable.

## SAM Lambda Deployment

```bash
cd ecosystems/flipside-crypto/sam/<app>

# Build
sam build

# Deploy (requires AWS creds)
sam deploy
```

## Common Tasks

### Add New Terraform Module

1. Create in `terraform/modules/{provider}/`
2. Add README, variables.tf, outputs.tf
3. Use in workspace

### Update SAM Handler Dependencies

1. Edit `sam/<app>/handler/requirements.txt`
2. Test locally: `sam local invoke`
3. Deploy: `sam deploy`

### Sync to FlipsideCrypto Repos

If changes need to go to public FlipsideCrypto repos, use the sync workflow or manual push:

```bash
GH_TOKEN="$GITHUB_FSC_TOKEN" gh repo sync FlipsideCrypto/<repo>
```

---

**Related**: [ecosystems/flipside-crypto/README.md](/ecosystems/flipside-crypto/README.md)
