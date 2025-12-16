# jbcom Control Center

Central control surface for managing jbcom public repositories and FlipsideCrypto infrastructure.

## What This Repo Does

1. **Manages repository configuration** via shell scripts + gh CLI
2. **Syncs secrets** to all jbcom public repos
3. **Syncs repository files** to all jbcom public repos (Cursor rules, workflows, etc.)
4. **Holds FSC infrastructure** (Terraform modules, SAM, Python libs)

## Structure

```
.
├── repo-config.json         # Repository configuration (source of truth)
├── repository-files/        # Files synced to target repos
│   ├── always-sync/         # Always overwrite (Cursor rules, workflows)
│   ├── initial-only/        # Sync once, repos customize after
│   ├── python/              # Python language rules
│   ├── nodejs/              # Node.js/TypeScript rules
│   ├── go/                  # Go language rules
│   └── terraform/           # Terraform/HCL rules
├── scripts/                 # Shell scripts for repo management
│   ├── sync-files           # Rsync files to repos
│   ├── configure-repos      # Configure repo settings via gh CLI
│   └── sync-secrets         # Sync secrets to repos
├── .github/workflows/
│   └── repo-sync.yml        # Orchestrates all syncing
├── ecosystems/flipside-crypto/  # FSC infrastructure
│   ├── terraform/           # Modules + workspaces
│   ├── sam/                 # Lambda apps
│   └── lib/                 # Python utilities
├── docs/                    # Documentation
└── memory-bank/             # Agent context
```

## Managed Repositories

All configuration, secrets, and files managed across:

**Python** (8): agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors

**Node.js** (7): agentic-control, agentic-triage, strata, otter-river-rush, otterfall, rivermarsh, pixels-pygame-palace

**Go** (3): port-api, vault-secret-sync, secretsync

**Terraform** (2): terraform-github-markdown, terraform-repository-automation

## Quick Start

### Sync Files to Repos

```bash
# Preview what would be synced
./scripts/sync-files --dry-run --all

# Sync files to all repos
./scripts/sync-files --all

# Sync to specific repo
./scripts/sync-files strata
```

### Configure Repository Settings

```bash
# Preview configuration changes
./scripts/configure-repos --dry-run --all

# Apply configuration to all repos
./scripts/configure-repos --all

# Show configuration diff
./scripts/configure-repos --diff --all
```

### Sync Secrets

```bash
# Check which secrets are available
./scripts/sync-secrets --status

# Sync secrets to all repos
./scripts/sync-secrets --all
```

### File Sync Behavior

| Directory | Behavior | Contents |
|-----------|----------|----------|
| `always-sync/` | Always overwrite | Cursor rules, workflows |
| `initial-only/` | Sync once | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/`, `terraform/` | Always overwrite | Language-specific rules |

## Token Configuration

```bash
export GITHUB_TOKEN="..."       # All GitHub API operations
export CI_GITHUB_TOKEN="..."    # Same token (for CI workflows)
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `repo-sync.yml` | Push to main (repository-files/**) | Sync files to all repos |
| `repo-sync.yml` | Daily at 6 AM UTC | Update submodules, sync secrets |
| `repo-sync.yml` | Manual dispatch | Selective sync with options |

## FSC Production Repos

These consume jbcom packages:
- `FlipsideCrypto/terraform-modules`
- `fsc-platform/cluster-ops`
- `fsc-internal-tooling-administration/terraform-organization-administration`

---

## Documentation

- **[FSC Infrastructure](docs/FSC-INFRASTRUCTURE.md)** - FlipsideCrypto production infrastructure
- **[Token Management](docs/TOKEN-MANAGEMENT.md)** - GitHub token configuration
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** - Environment configuration
