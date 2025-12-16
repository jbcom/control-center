# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

jbcom Control Center is a unified hub that:
1. **Manages all repository configuration** via shell scripts + gh CLI
2. **Syncs files** to all managed repos (Cursor rules, workflows, etc.)
3. **Holds FSC infrastructure** (Terraform modules, SAM Lambda apps, Python utilities)

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
│   └── terraform/           # Terraform/HCL language rules
├── scripts/                 # Shell scripts for repo management
│   ├── sync-files           # Rsync files to repos
│   ├── configure-repos      # Configure repo settings via gh CLI
│   └── sync-secrets         # Sync secrets to repos
├── .github/workflows/
│   └── repo-sync.yml        # Orchestrates all syncing
├── ecosystems//  # FSC infrastructure
│   ├── terraform/           # Modules + workspaces
│   ├── sam/                 # Lambda applications
│   └── lib/                 # Python utilities
├── docs/                    # Documentation
├── memory-bank/             # Agent session context
└── packages/                # Local packages
```

## Authentication

A unified GitHub token is used for all operations:

| Variable | Use Case |
|----------|----------|
| `GITHUB_TOKEN` | All GitHub API operations (gh CLI) |
| `CI_GITHUB_TOKEN` | Same token, used in CI workflows |

```bash
# All repos use the same token - gh CLI auto-uses GITHUB_TOKEN
gh pr list --repo jbcom/jbcom-control-center
gh pr list --repo /terraform-modules
```

## Repository Management

### Configuration
All repo settings are defined in `repo-config.json`:
- Merge settings (squash only, delete branch on merge)
- Features (issues, projects, wiki, discussions, pages)
- Security (Dependabot, secret scanning)
- Rulesets (branch protection)
- Labels

### Scripts

```bash
# Sync files to all repos
./scripts/sync-files --all

# Configure repo settings
./scripts/configure-repos --all

# Sync secrets
./scripts/sync-secrets --all

# Preview without making changes
./scripts/sync-files --dry-run --all
./scripts/configure-repos --dry-run --all
```

## Session Start/End Protocol

### Start of Session
```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md
```

### End of Session
```bash
cat >> memory-bank/activeContext.md << EOF

## Session: $(date +%Y-%m-%d)

### Completed
- [x] Task description

### For Next Agent
- [ ] Follow-up task
EOF

git add memory-bank/
git commit -m "docs: update memory bank for handoff"
```

## Sync Behavior

| Directory | Behavior | Purpose |
|-----------|----------|---------|
| `always-sync/` | Always overwrite | Cursor rules, workflows |
| `initial-only/` | Sync once | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/`, `terraform/` | Always overwrite | Language-specific rules |

## Managed Repositories

Defined in `repo-config.json`:

**Python:** agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors

**Node.js:** agentic-control, agentic-triage, strata, otter-river-rush, otterfall, rivermarsh, pixels-pygame-palace

**Go:** port-api, vault-secret-sync, secretsync

**Terraform:** terraform-github-markdown, terraform-repository-automation

## FSC Infrastructure (ecosystems//)

### Terraform
- Modules in `terraform/modules/`
- Workspaces in `terraform/workspaces/`
- Standard workflow: `terraform init`, `plan`, `apply`

### SAM Lambda Apps
Located in `sam/`:
- `secrets-config/` - Configuration handler
- `secrets-merging/` - Merge secrets
- `secrets-syncing/` - Sync secrets

### Python Utilities
`lib/terraform_modules/` - Utilities for Terraform data sources

## Workflow Triggers

| Event | Actions |
|-------|---------|
| Push to main (repository-files/**) | Sync files to all repos |
| Daily schedule | Sync secrets |
| Manual dispatch | Selective sync with dry-run |

## Rules

### Don't
- Push to main without PR
- Manually edit versions (use conventional commits)
- Skip tests

### Do
- Use PRs for changes
- Update memory-bank on session end
- Use conventional commits with scopes

## Documentation

- Token management: `docs/TOKEN-MANAGEMENT.md`
- FSC infrastructure: `docs/FSC-INFRASTRUCTURE.md`
- Environment variables: `docs/ENVIRONMENT_VARIABLES.md`
