# Unified Control Center

**Single control surface for jbcom + FlipsideCrypto ecosystems.**

## What's Managed

### jbcom Ecosystem (Python Packages → PyPI)

```
packages/
├── extended-data-types/    → PyPI: extended-data-types
├── lifecyclelogging/       → PyPI: lifecyclelogging
├── directed-inputs-class/  → PyPI: directed-inputs-class
├── python-terraform-bridge/→ PyPI: python-terraform-bridge
├── vendor-connectors/      → PyPI: vendor-connectors
└── agentic-control/        → npm: agentic-control
```

### FlipsideCrypto Ecosystem (Infrastructure → AWS/GCP)

```
ecosystems/flipside-crypto/
├── terraform/
│   ├── modules/           # 30 module categories (100+ modules)
│   │   ├── aws/           # AWS infrastructure
│   │   ├── google/        # Google Cloud
│   │   ├── github/        # GitHub management
│   │   └── terraform/     # Pipeline generation
│   └── workspaces/        # 44 workspaces
│       ├── terraform-aws-organization/    # 37 AWS workspaces
│       └── terraform-google-organization/ # 7 GCP workspaces
├── sam/                   # AWS Lambda applications
│   ├── secrets-config/
│   ├── secrets-merging/
│   └── secrets-syncing/
├── lib/                   # Python libraries
│   └── terraform_modules/
├── config/                # State paths, pipelines
└── memory-bank/           # Agent context
```

## Quick Start

```bash
# Python packages
uv sync
cd packages/extended-data-types && pytest

# Node.js (agentic-control)
pnpm install
cd packages/agentic-control && pnpm test

# Terraform (FlipsideCrypto)
cd ecosystems/flipside-crypto/terraform/workspaces/<workspace>
terraform init && terraform plan
```

## Agent Orchestration

This repo includes `agentic-control` - a unified CLI for AI agent management:

```bash
npm install -g agentic-control

# Initialize configuration
agentic init

# Spawn agents
agentic fleet spawn --repo jbcom/jbcom-control-center --task "Fix CI"
agentic fleet spawn --repo FlipsideCrypto/fsc-control-center --task "Update modules"

# Triage conversations
agentic triage analyze <session-id>
```

## Token Configuration

```bash
# jbcom repos
export GITHUB_JBCOM_TOKEN="..."

# FlipsideCrypto repos
export GITHUB_FSC_TOKEN="..."

# Default operations
export GITHUB_TOKEN="$GITHUB_JBCOM_TOKEN"
```

All PR reviews use `GITHUB_JBCOM_TOKEN` regardless of target repo.

## CI/CD

| Ecosystem | Registry | Trigger |
|-----------|----------|---------|
| jbcom Python | PyPI | Merge to main + conventional commit |
| agentic-control | npm | Merge to main + changes detected |
| FlipsideCrypto | N/A | Terraform apply (manual) |

## Key Files

| File | Purpose |
|------|---------|
| `ECOSYSTEM.toml` | Unified ecosystem manifest |
| `agentic.config.json` | Agent token/org configuration |
| `packages/*/pyproject.toml` | Python package config |
| `packages/agentic-control/package.json` | Node.js package config |
| `ecosystems/flipside-crypto/config/` | Terraform state paths |
| `.github/workflows/ci.yml` | Unified CI (Python + Node.js) |

## Versioning

- **Python packages**: SemVer via python-semantic-release
- **agentic-control**: SemVer via conventional commits
- **Terraform**: State-managed, no version tags

Commit format:
```bash
feat(edt): new utility         # → extended-data-types minor
fix(connectors): handle null   # → vendor-connectors patch
feat(agentic-control): fleet   # → agentic-control minor
```

## Cross-Ecosystem Dependencies

```
jbcom (packages)
├── extended-data-types (foundation)
├── lifecyclelogging
├── directed-inputs-class
├── vendor-connectors
│   └── used by → FlipsideCrypto (infrastructure)
└── agentic-control
    └── orchestrates → both ecosystems
```

---

See `ECOSYSTEM.toml` for complete manifest.
