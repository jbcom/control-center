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
│   ├── agents/              # Custom AI agent configurations
│   └── workflows/
│       └── terraform-sync.yml  # Repository config management (all-in-one)
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

All repository configuration is managed via Terragrunt in a single workflow:

- Repository settings (merge strategies, features)
- Branch protection rules
- Security settings (secret scanning, Dependabot)
- GitHub Pages configuration
- File synchronization (Cursor rules, workflows)
- **GitHub Actions secrets** (CI_GITHUB_TOKEN, NPM_TOKEN, PYPI_TOKEN, etc.)
- State: Terraform Cloud remote backend (one workspace per repository)

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
export GITHUB_TOKEN="..."       # All GitHub API operations
export CI_GITHUB_TOKEN="..."    # Same token (for CI workflows)
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `terraform-sync.yml` | Push to main (terragrunt-stacks/**, repository-files/**) | Apply all repository configuration (Terraform Cloud backend) |
| `terraform-sync.yml` | Pull request | Plan and preview changes |
| `terraform-sync.yml` | Daily at 2 AM UTC | Detect configuration drift |
| `terraform-sync.yml` | Manual dispatch | Plan or apply on demand |
| `unlock-tfc-workspaces.yml` | Manual dispatch | Unlock Terraform Cloud workspaces that are stuck in locked state |

## Quick Start

### Terragrunt Repository Management (Terraform Cloud backend)

```bash
# Authenticate with HCP Terraform: `terraform login` for interactive use, or `export TF_API_TOKEN` for CI
terraform login

# Plan changes for all repositories (uses HCP Terraform remote state)
cd terragrunt-stacks
terragrunt run-all plan

# Apply changes to all repositories
terragrunt run-all apply

# Plan/apply single repository
cd terragrunt-stacks/python/agentic-crew
terragrunt plan
terragrunt apply
```

### File Sync

Edit files in `repository-files/` and push to main. Changes sync automatically via Terragrunt.

### Secrets

Secrets are synced via Terragrunt using `github_actions_secret` resources. Add secrets to GitHub Actions secrets in this repository, and they'll be synced to all managed repos automatically.

To trigger manually:
```bash
gh workflow run terraform-sync.yml -f apply=true
```

### Troubleshooting: Locked Workspaces

If the `terraform-sync` workflow fails due to locked Terraform Cloud workspaces:

1. **Automatic unlock**: The workflow now automatically checks for and unlocks locked workspaces before running Terraform
2. **Manual unlock**: Use the dedicated unlock workflow:
   ```bash
   gh workflow run unlock-tfc-workspaces.yml -f dry_run=false
   ```
3. **Script**: Run the unlock script directly (requires TFC token):
   ```bash
   export TF_API_TOKEN="your-token"
   ./scripts/unlock-tfc-workspaces.sh --dry-run  # List locked workspaces
   ./scripts/unlock-tfc-workspaces.sh             # Unlock all
   ```

See [Unlocking TFC Workspaces](docs/UNLOCKING-TFC-WORKSPACES.md) for detailed documentation.

---

## Documentation

- **[Terraform Repository Management](docs/TERRAFORM-REPOSITORY-MANAGEMENT.md)** - Active configuration management
- **[Unlocking TFC Workspaces](docs/UNLOCKING-TFC-WORKSPACES.md)** - Complete guide to unlock locked Terraform Cloud workspaces
- **[Quick Unlock Guide](docs/QUICK-UNLOCK-GUIDE.md)** - Quick reference for unlocking workspaces
- **[FSC Infrastructure](docs/FSC-INFRASTRUCTURE.md)** - FlipsideCrypto production infrastructure
- **[Token Management](docs/TOKEN-MANAGEMENT.md)** - GitHub token configuration
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Environment configuration
