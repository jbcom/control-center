# Fleet Coordination

## agentic-control Package

The `agentic-control` package in `packages/agentic-control/` provides unified agent orchestration with automatic token switching.

### Commands

```bash
# List agents
agentic fleet list [--running]

# Spawn agent (auto-selects token based on repo org)
agentic fleet spawn <repo-url> "<task>" --ref <branch>

# Send follow-up message
agentic fleet followup <agent-id> "Message"

# Get fleet summary
agentic fleet summary

# Run bidirectional coordinator
agentic fleet coordinate --pr <number> --repo <owner/repo>

# Check token configuration
agentic tokens status
agentic tokens for-repo <owner/repo>

# AI-powered triage
agentic triage analyze <agent-id> --output report.md
agentic triage review --base main --head HEAD
```

### Configuration

All configuration is in `agentic.config.json`:

```json
{
  "tokens": {
    "organizations": {
      "jbcom": {
        "name": "jbcom",
        "tokenEnvVar": "GITHUB_JBCOM_TOKEN"
      },
      "FlipsideCrypto": {
        "name": "FlipsideCrypto",
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      },
      "fsc-platform": {
        "name": "fsc-platform",
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      }
    },
    "defaultTokenEnvVar": "GITHUB_TOKEN"
  },
  "defaultModel": "claude-sonnet-4-5-20250929"
}
```

## Coordination Channel (Hold-Open PR)

For multi-agent work, create a **draft PR** as communication hub:

```bash
# Create coordination branch
git checkout -b fleet/coordination-channel
echo "# Fleet Coordination" > .cursor/agents/FLEET_COORDINATION.md
git add -A && git commit -m "feat(fleet): Add coordination channel"
git push -u origin fleet/coordination-channel

# Create as DRAFT to avoid triggering AI reviewers
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --draft \
  --title "🤖 Fleet Coordination Channel (HOLD OPEN)" \
  --body "Communication channel for agent fleet. DO NOT MERGE."
```

> **Important**: Use `--draft` to prevent Amazon Q, Gemini, CodeRabbit, etc. from reviewing

## Agent Reporting Protocol

Sub-agents report status by commenting on the coordination PR:

| Format | Meaning |
|--------|---------|
| `@cursor ✅ DONE: [agent-id] [summary]` | Task completed |
| `@cursor ⚠️ BLOCKED: [agent-id] [issue]` | Needs intervention |
| `@cursor 📊 STATUS: [agent-id] [progress]` | Progress update |
| `@cursor 🔄 HANDOFF: [agent-id] [info]` | Ready for next step |

## Bidirectional Coordination Loop

The `coordinate` command runs two concurrent loops:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fleet.coordinate()                          │
│                                                                 │
│  ┌──────────────────┐              ┌────────────────────────┐  │
│  │ OUTBOUND Loop    │              │ INBOUND Loop           │  │
│  │ (every 60s)      │              │ (every 15s)            │  │
│  │                  │              │                        │  │
│  │ - Check agents   │              │ - Poll PR comments     │  │
│  │ - Send followup  │              │ - Parse @cursor        │  │
│  │ - Remove done    │              │ - Dispatch actions     │  │
│  └────────┬─────────┘              └──────────▲─────────────┘  │
│           │                                   │                │
└───────────┼───────────────────────────────────┼────────────────┘
            │                                   │
            ▼                                   │
    ┌───────────────┐                  ┌────────┴────────┐
    │ Sub-Agents    │                  │ Coordination PR │
    │ (via MCP)     │──── comment ────▶│ (GitHub inbox)  │
    └───────────────┘                  └─────────────────┘
```

## Programmatic Usage

```typescript
import { Fleet } from "agentic-control";

const fleet = new Fleet();

// Run coordination
await fleet.coordinate({
  coordinationPr: 251,
  repo: "jbcom/jbcom-control-center",
  agentIds: ["bc-xxx", "bc-yyy"],
});

// Or individual methods
await fleet.spawn({ repository: "owner/repo", task: "Do something" });
await fleet.followup("bc-xxx", "Status check");
```

## process-compose Integration

Add to `process-compose.yml`:

```yaml
fleet-coordinator:
  command: "node packages/agentic-control/dist/cli.js fleet coordinate --pr ${COORDINATION_PR} --repo jbcom/jbcom-control-center"
  environment:
    - "GITHUB_JBCOM_TOKEN=${GITHUB_JBCOM_TOKEN}"
    - "GITHUB_FSC_TOKEN=${GITHUB_FSC_TOKEN}"
    - "CURSOR_API_KEY=${CURSOR_API_KEY}"
```

Run with:
```bash
COORDINATION_PR=251 process-compose up fleet-coordinator
```
