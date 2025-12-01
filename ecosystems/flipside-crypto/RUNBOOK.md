# FlipsideCrypto Management Runbook

## Quick Start for New Agents

You are managing FlipsideCrypto infrastructure from the unified jbcom control center. Everything you need is here.

## Token Usage

```bash
# FlipsideCrypto repos - ALWAYS use FSC token
GH_TOKEN="$GITHUB_FSC_TOKEN" gh <command> --repo FlipsideCrypto/<repo>

# jbcom repos - ALWAYS use JBCOM token  
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command> --repo jbcom/<repo>
```

## Key Repositories

| Repo | Purpose | Token |
|------|---------|-------|
| `FlipsideCrypto/terraform-modules` | Terraform modules + Python lib | `GITHUB_FSC_TOKEN` |
| `jbcom/jbcom-control-center` | This control center | `GITHUB_JBCOM_TOKEN` |
| `jbcom/vendor-connectors` | Cloud connectors (FSC uses this) | `GITHUB_JBCOM_TOKEN` |

## Managing terraform-modules

### Check Status
```bash
# Open issues
GH_TOKEN="$GITHUB_FSC_TOKEN" gh issue list --repo FlipsideCrypto/terraform-modules

# Open PRs
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr list --repo FlipsideCrypto/terraform-modules

# CI status
GH_TOKEN="$GITHUB_FSC_TOKEN" gh run list --repo FlipsideCrypto/terraform-modules --limit 5
```

### Merge a PR
```bash
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr merge <number> --repo FlipsideCrypto/terraform-modules --squash
```

### Create Issue
```bash
GH_TOKEN="$GITHUB_FSC_TOKEN" gh issue create --repo FlipsideCrypto/terraform-modules \
  --title "Title" --body "Body"
```

## Using agentic-control CLI

```bash
# List running agents
node /workspace/packages/agentic-control/dist/cli.js fleet list

# Analyze an agent's work
node /workspace/packages/agentic-control/dist/cli.js triage analyze <agent-id> \
  -o /workspace/memory-bank/report.md --model claude-sonnet-4-20250514

# Create issues from analysis
node /workspace/packages/agentic-control/dist/cli.js triage analyze <agent-id> --create-issues

# Spawn agent in FSC repo
node /workspace/packages/agentic-control/dist/cli.js fleet spawn \
  --repo FlipsideCrypto/terraform-modules --task "Fix CI" --ref main
```

## Using fleet-manager.sh (Alternative)

```bash
cd /workspace/ecosystems/flipside-crypto/scripts

# List agents
./fleet-manager.sh list

# Spawn agent
./fleet-manager.sh spawn https://github.com/FlipsideCrypto/terraform-modules "Task description" main

# Send followup
./fleet-manager.sh followup <agent-id> "Message"
```

## Local Code

The terraform-modules content is absorbed into this repo at:
```
/workspace/ecosystems/flipside-crypto/terraform/
├── modules/     # 30 module categories
└── workspaces/  # 44 workspace configurations
```

## Key Config Files

| File | Purpose |
|------|---------|
| `/workspace/ECOSYSTEM.toml` | Unified ecosystem manifest |
| `/workspace/agentic.config.json` | Agent token/model config |
| `/workspace/ecosystems/flipside-crypto/config/state-paths.yaml` | Terraform state keys (IMMUTABLE) |
| `/workspace/ecosystems/flipside-crypto/config/pipelines.yaml` | Pipeline definitions |

## Memory Bank

- **jbcom**: `/workspace/memory-bank/`
- **FSC**: `/workspace/ecosystems/flipside-crypto/memory-bank/`

## Current Outstanding Work

Check GitHub issues:
```bash
GH_TOKEN="$GITHUB_FSC_TOKEN" gh issue list --repo FlipsideCrypto/terraform-modules --state open
```

Key issues:
- #224: Rebuild terraform-modules using jbcom packages
- #220: Migration verification
- #202: Remove Vault/AWS wrappers

---
*This runbook is the entry point for any agent managing FlipsideCrypto infrastructure.*
