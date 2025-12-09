# jbcom Control Center

Central control surface for managing jbcom public repositories and FlipsideCrypto infrastructure.

## What This Repo Does

1. **Manages repository configuration** via Terraform (settings, branch protection, security)
2. **Syncs secrets** to all jbcom public repos (daily)
3. **Syncs repository files** to all jbcom public repos (on push)
4. **Holds FSC infrastructure** (Terraform, SAM, Python libs)

## Structure

```
.
├── terragrunt-stacks/       # Repository configuration (Terragrunt)
│   ├── terragrunt.hcl       # Root config (provider, local backend)
│   ├── modules/repository/  # Shared repository module
│   ├── python/              # Python repos (8 repos)
│   ├── nodejs/              # Node.js repos (6 repos)
│   ├── go/                  # Go repos (2 repos)
│   └── terraform/           # Terraform repos (2 repos)
├── .github/
│   ├── sync.yml             # File sync config
│   └── workflows/
│       ├── sync.yml         # Secrets + file sync
│       └── terraform-sync.yml  # Repository config management
├── repository-files/        # Files synced to target repos
│   ├── always-sync/         # Rules (always overwrite)
│   ├── initial-only/        # Scaffold (sync once)
│   ├── python/              # Python language rules
│   ├── nodejs/              # Node.js/TypeScript rules
│   ├── go/                  # Go language rules
│   └── terraform/           # Terraform/HCL rules
├── ecosystems/flipside-crypto/  # FSC infrastructure
│   ├── terraform/           # Modules + workspaces
│   ├── sam/                 # Lambda apps
│   └── lib/                 # Python utilities
├── docs/                    # Documentation
├── scripts/                 # Helper scripts
└── memory-bank/             # Agent context
```

## Managed Repositories (18)

All configuration, secrets, and files managed across:

**Python** (8): agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors

**Node.js** (6): agentic-control, otter-river-rush, otterfall, pixels-pygame-palace, rivermarsh, strata

**Go** (2): port-api, vault-secret-sync

**Terraform** (2): terraform-github-markdown, terraform-repository-automation

## Management Approach

### Terragrunt-Managed (Active)
- Repository settings (merge strategies, features)
- Branch protection rules
- Security settings (secret scanning, Dependabot)
- GitHub Pages configuration
- State: Local state files (in each Terragrunt unit directory)

### Sync Workflow (Passive)
- Secrets distribution (CI_GITHUB_TOKEN, NPM_TOKEN, etc.)
- File synchronization (Cursor rules, Dockerfiles, workflows)
- Repository rulesets (CodeQL, Copilot code review)

| Directory | Behavior | Contents |
|-----------|----------|----------|
| `always-sync/` | Always overwrite | Cursor rules (must stay consistent) |
| `initial-only/` | Sync once (`replace: false`) | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/`, `terraform/` | Always overwrite | Language-specific rules |

## FSC Production Repos

These consume jbcom packages:
- `FlipsideCrypto/terraform-modules`
- `fsc-platform/cluster-ops`
- `fsc-internal-tooling-administration/terraform-organization-administration`

## Token Configuration

```bash
export GITHUB_JBCOM_TOKEN="..."  # jbcom repos
export GITHUB_FSC_TOKEN="..."    # FlipsideCrypto repos
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `terraform-sync.yml` | Push to main (terraform/**) | Apply repository configuration |
| `terraform-sync.yml` | Daily at 2 AM UTC | Detect configuration drift |
| `sync.yml` | Daily schedule | Sync secrets to public repos |
| `sync.yml` | Push to main | Sync files & rulesets to public repos |

## Quick Start

### Terraform Repository Management

```bash
# View current configuration
cd terraform
terraform init
terraform plan

# Make changes
vim variables.tf  # Update settings
terraform plan    # Preview changes
terraform apply   # Apply changes
```

### File Sync

Edit files in `repository-files/` and push to main. Changes sync automatically.

### Secret Sync

Secrets are synced daily. To trigger manually:
```bash
gh workflow run sync.yml
```

---

## Documentation

- **[Terraform Repository Management](docs/TERRAFORM-REPOSITORY-MANAGEMENT.md)** - Active configuration management
- **[FSC Infrastructure](docs/FSC-INFRASTRUCTURE.md)** - FlipsideCrypto production infrastructure
- **[Token Management](docs/TOKEN-MANAGEMENT.md)** - GitHub token configuration
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Environment configuration
