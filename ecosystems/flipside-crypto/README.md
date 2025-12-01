# FlipsideCrypto Infrastructure

> AWS and GCP infrastructure management for FlipsideCrypto, absorbed from `FlipsideCrypto/fsc-control-center`.

## Overview

This directory contains the complete infrastructure-as-code for FlipsideCrypto's cloud environments:

- **44 Terraform workspaces** (37 AWS + 7 GCP)
- **100+ reusable modules** across AWS, GCP, GitHub
- **3 SAM Lambda applications** for secrets management
- **Python library** for Terraform data sources

## Structure

```
ecosystems/flipside-crypto/
├── terraform/
│   ├── modules/              # Reusable infrastructure modules
│   │   ├── aws/              # 70+ AWS modules
│   │   ├── google/           # 38 GCP modules
│   │   ├── github/           # GitHub org management
│   │   └── terraform/        # Pipeline generation
│   └── workspaces/           # Live infrastructure state
│       ├── terraform-aws-organization/     # 37 workspaces
│       └── terraform-google-organization/  # 7 workspaces
├── sam/                      # AWS Lambda applications
│   ├── secrets-config/       # Secrets configuration service
│   ├── secrets-merging/      # Secrets merging service
│   └── secrets-syncing/      # Secrets syncing service
├── lib/                      # Python libraries
│   └── terraform_modules/    # Data sources, null resources, CLI
├── config/                   # Configuration files
│   ├── state-paths.yaml      # Terraform state locations
│   ├── pipelines.yaml        # CI/CD pipeline config
│   └── defaults.yaml         # Default values
├── scripts/                  # Operational scripts
├── memory-bank/              # Agent context and state
└── ECOSYSTEM.toml            # Package manifest
```

## Terraform Workspaces

### AWS Organization (37 workspaces)

| Category | Workspaces | Description |
|----------|------------|-------------|
| `organization/` | 1 | AWS Organizations, Control Tower |
| `authentication/` | 1 | IAM, IdP, SAML federation |
| `sso/` | 1 | AWS IAM Identity Center |
| `secrets/` | 1 | Doppler integration |
| `security/` | 4 | GuardDuty, SecurityHub, Macie |
| `billing/` | 2 | Cost management, budgets |
| `components/` | 20+ | Service-specific infra |
| `aggregator/` | 1 | Cross-workspace outputs |

### Google Organization (7 workspaces)

| Category | Workspaces | Description |
|----------|------------|-------------|
| `gws/` | 2 | Google Workspace (org units, assignments) |
| `gcp/` | 5 | GCP projects, policies, functions |

## State Management

All Terraform state is stored in S3:

```
s3://flipside-crypto-internal-tooling/
└── terraform/state/{pipeline}/workspaces/{workspace}/terraform.tfstate
```

**State paths are IMMUTABLE.** See `config/state-paths.yaml` for the complete registry.

## Working with Workspaces

```bash
# Navigate to a workspace
cd ecosystems/flipside-crypto/terraform/workspaces/terraform-aws-organization/security

# Initialize
terraform init

# Plan changes
terraform plan

# Apply (requires appropriate AWS credentials)
terraform apply
```

## Python Library

The `lib/terraform_modules/` package provides:

- **Data Sources**: Python-based Terraform data source implementations
- **Null Resources**: Custom resource handlers
- **CLI**: `tm_cli` command for module operations

```bash
# Install
cd ecosystems/flipside-crypto/lib
pip install -e .

# Use CLI
tm_cli --help
```

## SAM Applications

AWS Lambda functions for secrets management. See individual README files:

- [`sam/secrets-config/README.md`](sam/secrets-config/README.md)
- [`sam/secrets-merging/README.md`](sam/secrets-merging/README.md)
- [`sam/secrets-syncing/README.md`](sam/secrets-syncing/README.md)

## Token Configuration

FlipsideCrypto operations require `GITHUB_FSC_TOKEN`:

```bash
export GITHUB_FSC_TOKEN="ghp_..."
```

The unified `agentic-control` CLI handles token switching automatically based on repository organization.

## Dependencies

This infrastructure depends on jbcom packages:

- `vendor-connectors` - Cloud SDK wrappers
- `lifecyclelogging` - Structured logging
- `extended-data-types` - Foundation utilities

## Migration History

| Date | Event |
|------|-------|
| 2025-12-01 | Absorbed into `jbcom-control-center` |
| Prior | Standalone at `FlipsideCrypto/fsc-control-center` |

The original repository has been archived.

---

See [`ECOSYSTEM.toml`](ECOSYSTEM.toml) for package manifest.
