# Fleet Coordination

## cursor-fleet Package

The `@jbcom/cursor-fleet` package in `packages/cursor-fleet/` provides agent orchestration.

### Commands

```bash
# List agents
cursor-fleet list [--running]

# Spawn agent
cursor-fleet spawn --repo owner/repo --task "Task description"

# Send follow-up message
cursor-fleet followup <agent-id> "Message"

# Monitor specific agents until done
cursor-fleet monitor <agent-id1> <agent-id2>

# Watch fleet for state changes
cursor-fleet watch --poll 30000

# Run bidirectional coordinator
cursor-fleet coordinate --pr <number> --agents <id1,id2>
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
import { Fleet } from "@jbcom/cursor-fleet";

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
const comments = fleet.fetchPRComments("owner/repo", 251);
fleet.postPRComment("owner/repo", 251, "Update");
```

## process-compose Integration

Add to `process-compose.yml`:

```yaml
fleet-coordinator:
  command: "node packages/cursor-fleet/dist/cli.js coordinate --pr ${COORDINATION_PR} --agents ${AGENT_IDS}"
  environment:
    - "GITHUB_JBCOM_TOKEN=${GITHUB_JBCOM_TOKEN}"
    - "CURSOR_API_KEY=${CURSOR_API_KEY}"
```

Run with:
```bash
COORDINATION_PR=251 AGENT_IDS=bc-xxx,bc-yyy process-compose up fleet-coordinator
```
