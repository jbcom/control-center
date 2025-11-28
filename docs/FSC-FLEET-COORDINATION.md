# FSC Fleet Coordination

## Overview

jbcom Control Center operates as a **counterparty** to FSC Control Center. When FSC needs ecosystem changes (package releases, features, fixes), it spawns a jbcom Control Center agent to coordinate.

## The Diamond Pattern

```
FSC Control Center (Control Manager)
    │
    ├── spawn → terraform-modules agent
    ├── spawn → terraform-aws-* agents
    │
    └── spawn → jbcom Control Center Agent (YOU)
                    │
                    ├── spawn → EDT agent
                    ├── spawn → vendor-connectors agent
                    └── spawn → lifecyclelogging agent
                            │
                            └── addFollowup → FSC agents (direct)
```

## When You Are Spawned by FSC

FSC Control Center will spawn you with context like:

```markdown
TASK: Release vendor-connectors 202511.7 with feature X

FSC AGENTS IN FLIGHT:
- bc-11111: terraform-modules (waiting for VC update)
- bc-22222: terraform-aws-secretsmanager (waiting for VC update)

COORDINATION:
- Notify FSC agents directly when release complete
- Report back to FSC Control Center agent: bc-xxxxx
```

## Your Responsibilities

### 1. Parse the Context

Understand:
- What FSC needs
- Which FSC agents are waiting
- The FSC control manager agent ID

### 2. Decompose the Task

Break into jbcom sub-tasks:
```
FSC Request: "Release vendor-connectors with timeout feature"

Decomposition:
├── extended-data-types: Add TimeoutConfig type
├── vendor-connectors: Implement timeout, release
└── Notify FSC agents
```

### 3. Spawn Sub-Agents

```bash
# Use the fleet manager
/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/jbcom/extended-data-types \
    "Add TimeoutConfig type for vendor-connectors" main

/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/jbcom/vendor-connectors \
    "Implement timeout feature, release as 202511.7" main
```

### 4. Notify FSC Agents Directly

When releases complete:
```bash
# Notify each FSC agent
for agent in bc-11111 bc-22222; do
    /workspace/scripts/fleet-manager.sh followup $agent \
        "✅ vendor-connectors 202511.7 released. Update your deps."
done
```

### 5. Report to FSC Control Manager

```bash
/workspace/scripts/fleet-manager.sh followup $FSC_CONTROL_MANAGER \
    "✅ ECOSYSTEM RELEASE COMPLETE
    - extended-data-types: 202511.5.0
    - vendor-connectors: 202511.7
    - FSC agents notified directly"
```

## Fleet Manager Commands

```bash
# List all agents
/workspace/scripts/fleet-manager.sh list

# Spawn agent
/workspace/scripts/fleet-manager.sh spawn <repo-url> <task> [ref]

# Send followup
/workspace/scripts/fleet-manager.sh followup <agent-id> <message>

# Check status
/workspace/scripts/fleet-manager.sh status <agent-id>
```

## Token Access

You have access to:
- `GITHUB_JBCOM_TOKEN` - jbcom repos (default)
- `CURSOR_API_KEY` - Cursor agent API (auto-set)

For FSC repos, use the gh CLI with appropriate tokens or ask FSC to handle FSC-side changes.

## Communication Protocol

| Direction | Method | Example |
|-----------|--------|---------|
| FSC CC → You | launchAgent | Task assignment with context |
| You → jbcom agents | launchAgent | Sub-task delegation |
| jbcom agent → FSC agent | addFollowup | "Package released" |
| You → FSC CC | addFollowup | Summary report |

## Best Practices

### DO
- ✅ Include FSC agent IDs in all coordination context
- ✅ Notify FSC agents directly when work completes
- ✅ Report summary to FSC control manager
- ✅ Archive your conversation before session ends

### DON'T
- ❌ Work in isolation without FSC awareness
- ❌ Forget to notify waiting FSC agents
- ❌ Assume FSC will poll for status
- ❌ Let conversations expire without archiving

---

**Counterparty**: FSC Control Center (`/fsc-control-center`)
**Last Updated**: 2025-11-28
