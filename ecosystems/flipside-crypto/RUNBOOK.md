# FlipsideCrypto Management Runbook

> **Source of Truth**: `packages/agentic-control` + `agentic.config.json`

## Quick Start

```bash
# Check token status - confirms FSC access works
node packages/agentic-control/dist/cli.js tokens status

# List running agents
node packages/agentic-control/dist/cli.js fleet list

# Show current config
node packages/agentic-control/dist/cli.js config
```

## Token Configuration

Configured in `/workspace/agentic.config.json`:

```json
{
  "tokens": {
    "organizations": {
      "jbcom": { "tokenEnvVar": "GITHUB_JBCOM_TOKEN" },
      "FlipsideCrypto": { "tokenEnvVar": "GITHUB_FSC_TOKEN" }
    }
  }
}
```

The CLI automatically selects the right token based on repo organization.

## Managing FlipsideCrypto/terraform-modules

### Via agentic-control CLI (Recommended)

```bash
# Spawn agent to work on terraform-modules
node packages/agentic-control/dist/cli.js fleet spawn \
  --repo FlipsideCrypto/terraform-modules \
  --task "Fix failing CI" \
  --ref main

# Analyze what an agent did
node packages/agentic-control/dist/cli.js triage analyze <agent-id> \
  -o report.md --model claude-sonnet-4-20250514

# Create issues from outstanding tasks
node packages/agentic-control/dist/cli.js triage analyze <agent-id> --create-issues
```

### Via gh CLI (Direct)

```bash
# The token is auto-selected, but for gh you must set GH_TOKEN explicitly
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr list --repo FlipsideCrypto/terraform-modules
GH_TOKEN="$GITHUB_FSC_TOKEN" gh issue list --repo FlipsideCrypto/terraform-modules
GH_TOKEN="$GITHUB_FSC_TOKEN" gh run list --repo FlipsideCrypto/terraform-modules
```

## CLI Commands Reference

| Command | Purpose |
|---------|---------|
| `fleet list` | List all agents |
| `fleet spawn --repo X --task Y` | Spawn agent in repo |
| `fleet followup <id> <msg>` | Send message to agent |
| `triage analyze <id>` | AI analysis of agent work |
| `triage analyze <id> --create-issues` | Create GitHub issues from analysis |
| `triage review` | AI code review of git diff |
| `tokens status` | Show token availability |
| `config` | Show current configuration |

## Local Code Location

terraform-modules content is absorbed at:
```
/workspace/ecosystems/flipside-crypto/terraform/
├── modules/     # Terraform modules
└── workspaces/  # Workspace configurations
```

## Configuration Files

| File | Purpose |
|------|---------|
| `/workspace/agentic.config.json` | CLI configuration |
| `/workspace/ECOSYSTEM.toml` | Ecosystem manifest |
| `/workspace/ecosystems/flipside-crypto/config/state-paths.yaml` | Terraform state keys |

## Current Issues

```bash
# Check what needs work
GH_TOKEN="$GITHUB_FSC_TOKEN" gh issue list --repo FlipsideCrypto/terraform-modules --state open
```

## Legacy Scripts (DEPRECATED)

These scripts in `ecosystems/flipside-crypto/scripts/` are **LEGACY** and superseded by `agentic-control`:

| Legacy Script | Replaced By |
|--------------|-------------|
| `fleet-manager.sh` | `agentic fleet` commands |
| `fleet_manager.py` | `agentic fleet` commands |
| `replay_agent_session.py` | `agentic triage analyze` |

Use `agentic-control` CLI instead - it's the maintained implementation.

---
*Based on actual implementation in `packages/agentic-control`*
