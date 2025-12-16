# FlipsideCrypto Infrastructure Maintenance

## Overview

This control center manages infrastructure that deploys to these FSC repositories:

| Repo | Purpose |
|------|---------|
| `FlipsideCrypto/terraform-modules` | Reusable Terraform modules |
| `fsc-platform/cluster-ops` | Kubernetes cluster operations |
| `fsc-internal-tooling-administration/terraform-organization-administration` | Org-level Terraform |

All repos use `GITHUB_TOKEN` for API access.

## Local Infrastructure

The `ecosystems/flipside-crypto/` directory mirrors and extends these repos:

```
ecosystems/flipside-crypto/
├── terraform/
│   ├── modules/           # 100+ reusable modules
│   └── workspaces/        # 44 live workspaces
├── sam/                   # AWS Lambda apps
├── lib/terraform_modules/ # Python library
└── config/                # State paths, pipelines
```

## jbcom Package Dependencies

These FSC repos consume jbcom packages:

| Package | Used By | Purpose |
|---------|---------|---------|
| `vendor-connectors` | terraform-modules, cluster-ops | AWS, GCP, Slack clients |
| `lifecyclelogging` | All | Structured logging |
| `extended-data-types` | All | Config utilities |

### Checking Package Versions in FSC Repos

```bash
# terraform-modules (gh CLI auto-uses GITHUB_TOKEN)
gh api /repos/FlipsideCrypto/terraform-modules/contents/requirements.txt \
  --jq '.content' | base64 -d | grep -E "vendor-connectors|lifecyclelogging|extended-data-types"

# cluster-ops
gh api /repos/fsc-platform/cluster-ops/contents/requirements.txt \
  --jq '.content' | base64 -d | grep -E "vendor-connectors|lifecyclelogging|extended-data-types"
```

### Updating FSC to Use New Package Versions

After releasing a jbcom package:

```bash
# Clone the FSC repo (uses GITHUB_TOKEN from environment)
git clone https://github.com/FlipsideCrypto/terraform-modules.git /tmp/terraform-modules
cd /tmp/terraform-modules

# Update requirements
# Edit requirements.txt or pyproject.toml with new versions

# Test
pip install -e .
pytest

# Create PR
git checkout -b deps/update-jbcom-packages
git add requirements.txt
git commit -m "deps: update jbcom packages

- vendor-connectors: X.Y.Z
- lifecyclelogging: X.Y.Z"
gh pr create --title "deps: update jbcom packages"
```

## Token Configuration

All FSC organizations use the unified `GITHUB_TOKEN`:

| Org | Repos |
|-----|-------|
| FlipsideCrypto | terraform-modules |
| fsc-platform | cluster-ops |
| fsc-internal-tooling-administration | terraform-organization-administration |

The `gh` CLI automatically uses `GITHUB_TOKEN` from environment.

## Key Operations

### Check CI Status

```bash
# terraform-modules (gh CLI auto-uses GITHUB_TOKEN)
gh run list --repo FlipsideCrypto/terraform-modules --limit 5

# cluster-ops
gh run list --repo fsc-platform/cluster-ops --limit 5
```

### View Open PRs

```bash
gh pr list --repo FlipsideCrypto/terraform-modules
gh pr list --repo fsc-platform/cluster-ops
```

### Spawn Agent to FSC Repo

```bash
agentic fleet spawn "https://github.com/FlipsideCrypto/terraform-modules" "Update to latest jbcom packages"
agentic fleet spawn "https://github.com/fsc-platform/cluster-ops" "Fix CI"
```

## Local Development

### Terraform

```bash
cd ecosystems/flipside-crypto/terraform/workspaces/terraform-aws-organization/<workspace>
terraform init
terraform plan
terraform apply  # Requires AWS creds
```

### SAM Lambda

```bash
cd ecosystems/flipside-crypto/sam/<app>
sam build
sam local invoke  # Test locally
sam deploy        # Requires AWS creds
```

### Python Library

```bash
cd ecosystems/flipside-crypto/lib
pip install -e .
python -m terraform_modules --help
```

## Sync Relationship

```
jbcom-control-center (this repo)
├── packages/vendor-connectors  ─────→  PyPI
│                                         │
│                                         ▼
└── ecosystems/flipside-crypto/     FSC repos consume from PyPI
                                    ├── FlipsideCrypto/terraform-modules
                                    ├── fsc-platform/cluster-ops
                                    └── fsc-internal-tooling-administration/...
```

---

**Related**: [docs/JBCOM-ECOSYSTEM-INTEGRATION.md](./JBCOM-ECOSYSTEM-INTEGRATION.md)
