# jbcom Control Center Fleet Integration

## Purpose

This document defines how jbcom Control Center should participate in the **FSC Fleet Management Pattern**. When FSC spawns a jbcom Control Center agent, that agent must understand:

1. Its role in the diamond pattern
2. How to spawn its own sub-agents
3. How to communicate back to FSC agents
4. What tokens and access it needs

---

## The Diamond Pattern (jbcom Perspective)

```
                    FSC Control Center
                    (Spawns jbcom CC Agent)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────────────┐
    │ FSC      │    │ FSC      │    │ jbcom Control    │
    │ Agent A  │    │ Agent B  │    │ Center Agent     │
    │ tf-mod   │    │ tf-aws   │    │ (YOU)            │
    └────┬─────┘    └────┬─────┘    └────────┬─────────┘
         │               │                   │
         │               │          ┌────────┴────────┐
         │               │          │                 │
         │               │          ▼                 ▼
         │               │    ┌──────────┐     ┌──────────┐
         │               │    │ jbcom    │     │ jbcom    │
         │               │    │ Agent C  │     │ Agent D  │
         │               │    │ EDT      │     │ VC       │
         │               │    └────┬─────┘     └────┬─────┘
         │               │         │                │
         └───────────────┴─────────┴────────────────┘
                    CROSS-AGENT COMMUNICATION
```

**When spawned by FSC, you (jbcom CC Agent):**
1. Receive a task from FSC Control Center
2. May receive IDs of FSC agents working in parallel
3. Should spawn your own agents in jbcom repos as needed
4. Must communicate completion/updates back to FSC agents directly

---

## Token Requirements

### jbcom Control Center Must Have

| Token | Purpose | Usage |
|-------|---------|-------|
| `GITHUB_JBCOM_TOKEN` | jbcom org access | Default in jbcom context |
| `GITHUB_FSC_TOKEN` |  org access | **REQUIRED for diamond pattern** |
| `CURSOR_API_KEY` | Cursor agent API | Auto-set in Cursor environment |

### Setting Up FSC Token

For bidirectional communication, jbcom-control-center needs `GITHUB_FSC_TOKEN`:

```bash
# In jbcom-control-center's environment/secrets:
# Add a GitHub token with read access to  repos
GITHUB_FSC_TOKEN=ghp_xxxx...
```

This enables jbcom agents to:
- Read FSC repository state
- Send followups to FSC agents (via API, not direct GitHub access)
- Verify FSC PR status

---

## Spawning Context from FSC

When FSC Control Center spawns a jbcom CC agent, the prompt will include:

```markdown
# Task Assignment from FSC Control Center

## Requesting Agent
- Agent ID: bc-a95ea075-a47a-482f-bf69-5d16b78a2c4c
- Control Center: FSC Control Center
- Repository: /fsc-control-center

## Your Task
[Specific task - e.g., "Release vendor-connectors 202511.7 with feature X"]

## FSC Agents in Flight
[List of agent IDs working in FSC repos]
- bc-xxxxx: terraform-modules (updating dependencies)
- bc-yyyyy: terraform-aws-secretsmanager (updating dependencies)

## Coordination Required
When your work is complete:
1. Send followup to FSC agents listed above
2. Include package name and version released
3. They will update their PRs accordingly

## Communication Pattern
Use addFollowup API to notify FSC agents directly.
```

---

## jbcom CC Agent Responsibilities

### 1. Understand the Task

Parse the spawning context to understand:
- What FSC needs
- What FSC agents are waiting
- What the deadline/urgency is

### 2. Decompose Locally

Break the task into jbcom sub-tasks:
```
FSC Request: "Release vendor-connectors with new feature"

Decomposition:
├── extended-data-types
│   └── Add new type if needed
├── vendor-connectors
│   └── Implement feature, release
└── Notify FSC agents
```

### 3. Spawn Sub-Agents

```bash
# Spawn in extended-data-types
/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/jbcom/extended-data-types \
    "Add new type for vendor-connectors feature" main

# Spawn in vendor-connectors
/workspace/scripts/fleet-manager.sh spawn \
    https://github.com/jbcom/vendor-connectors \
    "Implement feature X, wait for EDT if needed" main
```

### 4. Communicate Back to FSC

When releases are complete:
```bash
# Notify each FSC agent
FSC_AGENT_IDS="bc-xxxxx bc-yyyyy"
for agent in $FSC_AGENT_IDS; do
    /workspace/scripts/fleet-manager.sh followup $agent \
        "✅ vendor-connectors 202511.7 released. Update your dependencies."
done
```

---

## What jbcom-control-center Needs

### Documentation Updates

Add to jbcom-control-center:

1. **`.ruler/AGENTS.md`** - Add FSC counterparty section
2. **`docs/FSC-FLEET-INTEGRATION.md`** - This document
3. **`.cursor/rules/fsc-coordination.mdc`** - FSC coordination rules

### Environment Setup

1. Add `GITHUB_FSC_TOKEN` to secrets
2. Ensure `CURSOR_API_KEY` is available
3. Install fleet management tooling

### Fleet Manager Script

Copy or adapt `/workspace/scripts/fleet-manager.sh` to jbcom-control-center.

---

## Communication Protocol

### FSC → jbcom CC

```
Method: launchAgent
Context: Task + FSC agent IDs
Expected: jbcom CC spawns sub-agents, coordinates, notifies FSC
```

### jbcom CC → jbcom Sub-Agents

```
Method: launchAgent
Context: Sub-task + parent ID + FSC agent IDs
Expected: Sub-agent completes, notifies parent
```

### jbcom Sub-Agent → FSC Agent

```
Method: addFollowup
Context: Completion status, version info
Expected: FSC agent updates its work
```

### jbcom CC → FSC CC

```
Method: addFollowup (to FSC CC agent)
Context: Summary of all work completed
Expected: FSC CC tracks overall progress
```

---

## Example Full Flow

### 1. FSC CC Spawns jbcom CC

```bash
# FSC Control Center executes:
fleet-manager.sh spawn \
    https://github.com/jbcom/jbcom-control-center \
    "TASK: Release vendor-connectors 202511.7 with new timeout feature.
    
    FSC AGENTS IN FLIGHT:
    - bc-11111: terraform-modules (waiting for new VC)
    - bc-22222: terraform-aws-secretsmanager (waiting for new VC)
    
    COORDINATION: Notify these agents directly when released." \
    main
```

### 2. jbcom CC Decomposes and Spawns

```bash
# jbcom CC Agent executes:
# Spawn EDT agent
EDT_AGENT=$(fleet-manager.sh spawn \
    https://github.com/jbcom/extended-data-types \
    "Add TimeoutConfig type for VC timeout feature" main | jq -r '.id')

# Spawn VC agent (will wait for EDT)
VC_AGENT=$(fleet-manager.sh spawn \
    https://github.com/jbcom/vendor-connectors \
    "Implement timeout feature using EDT TimeoutConfig.
    Wait for EDT agent $EDT_AGENT to complete first." main | jq -r '.id')
```

### 3. EDT Agent Completes

```bash
# EDT agent notifies jbcom CC
fleet-manager.sh followup $JBCOM_CC_AGENT \
    "✅ TimeoutConfig added to EDT. Released as 202511.5.0"
```

### 4. jbcom CC Notifies VC Agent

```bash
# jbcom CC forwards to VC agent
fleet-manager.sh followup $VC_AGENT \
    "EDT 202511.5.0 released with TimeoutConfig. Proceed with timeout feature."
```

### 5. VC Agent Completes and Notifies FSC

```bash
# VC agent notifies FSC agents directly
for fsc_agent in bc-11111 bc-22222; do
    fleet-manager.sh followup $fsc_agent \
        "✅ vendor-connectors 202511.7 released with timeout feature. Update deps."
done

# VC agent notifies jbcom CC
fleet-manager.sh followup $JBCOM_CC_AGENT \
    "✅ vendor-connectors 202511.7 released. FSC agents notified."
```

### 6. jbcom CC Reports to FSC CC

```bash
# jbcom CC reports completion to FSC CC
fleet-manager.sh followup $FSC_CC_AGENT \
    "✅ ECOSYSTEM RELEASE COMPLETE
    - extended-data-types: 202511.5.0
    - vendor-connectors: 202511.7
    - FSC agents bc-11111, bc-22222 notified directly"
```

---

## Anti-Patterns to Avoid

### ❌ Don't

- Forget to notify FSC agents when releases complete
- Spawn agents without coordination context
- Let sub-agents work in isolation
- Assume FSC CC will poll for status

### ✅ Do

- Include FSC agent IDs in all coordination
- Enable direct agent-to-agent communication
- Report completion proactively
- Maintain the diamond pattern

---

**Last Updated**: 2025-11-28
**For**: jbcom-control-center agents spawned by FSC
**Counterparty**: FSC Control Center
