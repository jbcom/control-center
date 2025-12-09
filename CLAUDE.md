# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

jbcom Control Center is a unified hub that:
1. **Manages repository configuration** via Terraform (settings, branch protection, security) using custom AI agent
2. **Syncs secrets** to jbcom public repos (daily via GitHub Actions)
3. **Syncs repository files** (Cursor rules, workflows, docs) to all jbcom repos
4. **Holds FSC infrastructure** (Terraform modules, SAM Lambda apps, Python utilities)

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
│   │   └── terraform-repository-manager.md  # Terraform MCP agent
│   ├── sync.yml             # File sync config (which files go where)
│   └── workflows/
│       ├── sync.yml         # Secrets + file sync
│       └── terraform-sync.yml  # Repository config management
├── repository-files/        # Files synced to target repos
│   ├── always-sync/         # Always overwrite (Cursor rules)
│   ├── initial-only/        # Sync once, repos customize after
│   ├── python/              # Python language rules
│   ├── nodejs/              # Node.js/TypeScript rules
│   ├── go/                  # Go language rules
│   └── terraform/           # Terraform/HCL language rules
├── ecosystems/flipside-crypto/  # FSC infrastructure
│   ├── terraform/           # Modules + workspaces
│   ├── sam/                 # Lambda applications
│   ├── lib/                 # Python utilities (terraform_modules package)
│   └── external/            # Terraform external data modules
├── docs/                    # Documentation
│   ├── TERRAFORM-REPOSITORY-MANAGEMENT.md  # Terraform approach
│   └── TERRAFORM-AGENT-QUICKSTART.md       # Agent quick start
├── scripts/                 # Helper scripts
├── memory-bank/             # Agent session context
└── packages/                # Local packages (agentic-control)
```

## Authentication

Two GitHub organizations require different tokens:

| Organization | Token Variable | Use Case |
|--------------|----------------|----------|
| jbcom | `GITHUB_JBCOM_TOKEN` | jbcom repos (default) |
| FlipsideCrypto | `GITHUB_FSC_TOKEN` | Enterprise infrastructure |

```bash
# jbcom repos
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr list --repo jbcom/jbcom-control-center

# FlipsideCrypto repos
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr list --repo FlipsideCrypto/terraform-modules
```

Token mapping is defined in `agentic.config.json`.

## Custom Agents

### terraform-repository-manager

**Purpose**: Actively manages all 18 jbcom repositories using Terraform MCP server.

**When to Use**:
- Changing repository settings (merge strategies, branch protection, etc.)
- Adding/removing repositories from management
- Detecting and fixing configuration drift
- Applying policy changes across all repos

**Invocation**:
```
@terraform-repository-manager <task description>
```

**Examples**:
```
@terraform-repository-manager Initialize Terraform and import all repositories
@terraform-repository-manager Enable wiki on agentic-control repository
@terraform-repository-manager Check for drift and reapply configuration
```

**What It Manages**:
- Repository settings (merge strategies, features)
- Branch protection (PR requirements, force push protection)
- Security settings (secret scanning, Dependabot)
- GitHub Pages (Actions workflow builds)

**State Storage**: Local state files (in each Terragrunt unit directory)

**Documentation**:
- Instructions: `.github/agents/terraform-repository-manager.md`
- Quick Start: `docs/TERRAFORM-AGENT-QUICKSTART.md`
- Full Guide: `docs/TERRAFORM-REPOSITORY-MANAGEMENT.md`

## Session Start/End Protocol

### Start of Session
```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md
```

### End of Session
Update memory bank before ending:
```bash
# Update context for next agent
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
| `always-sync/` | Always overwrite | Cursor rules must stay consistent |
| `initial-only/` | Sync once (`replace: false`) | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/`, `terraform/` | Always overwrite | Language-specific rules |

Target repos:

**Python:**
- `jbcom/agentic-crew`
- `jbcom/ai_game_dev`
- `jbcom/directed-inputs-class`
- `jbcom/extended-data-types`
- `jbcom/lifecyclelogging`
- `jbcom/python-terraform-bridge`
- `jbcom/rivers-of-reckoning`
- `jbcom/vendor-connectors`

**Node.js/TypeScript:**
- `jbcom/agentic-control`
- `jbcom/otter-river-rush`
- `jbcom/otterfall`
- `jbcom/pixels-pygame-palace`
- `jbcom/rivermarsh`
- `jbcom/strata`

**Go:**
- `jbcom/port-api`
- `jbcom/secretsync`

**Terraform/HCL:**
- `jbcom/terraform-github-markdown`
- `jbcom/terraform-repository-automation`

## FSC Infrastructure (ecosystems/flipside-crypto/)

### Terraform
- Modules in `terraform/modules/aws/`
- Workspaces in `terraform/workspaces/`
- Standard Terraform workflow: `terraform init`, `plan`, `apply`

### SAM Lambda Apps
Located in `sam/`:
- `secrets-config/` - Configuration handler
- `secrets-merging/` - Merge secrets
- `secrets-syncing/` - Sync secrets

### Python Utilities
`lib/terraform_modules/` - Utilities for Terraform data sources:
- AWS, Google, GitHub, Vault clients
- Doppler/Vault config management
- Terraform resource helpers

## Workflow Triggers

| Event | Actions |
|-------|---------|
| Push to main | Sync files + secrets + branch protection + Pages |
| Daily schedule | Sync secrets to all repos |
| Manual dispatch | Selective sync with dry-run option |

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
