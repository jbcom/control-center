# Fleet Management Protocol

## Overview

FSC Control Center operates as a **control manager** that decomposes tasks and delegates to spawned agents across repositories. This document defines the fleet management architecture and communication patterns.

## The Problem with Single-Agent Operations

Previously, one agent would:
- Check out multiple repositories sequentially
- Switch between branches repeatedly
- Lose context when switching
- Have no parallel execution

**This is inefficient.** The Cursor API allows:
- Spawning dedicated agents per repository
- Sending task updates to running agents
- Agent-to-agent communication
- Parallel execution across repos

---

## The Diamond Pattern

### Architecture

```
                    FSC Control Center (YOU)
                    [CONTROL MANAGER]
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────────────┐
    │ Agent A  │    │ Agent B  │    │ jbcom Control    │
    │ tf-mod   │    │ tf-aws   │    │ Center Agent     │
    └────┬─────┘    └────┬─────┘    └────────┬─────────┘
         │               │                   │
         │               │          ┌────────┴────────┐
         │               │          │                 │
         │               │          ▼                 ▼
         │               │    ┌──────────┐     ┌──────────┐
         │               │    │ Agent C  │     │ Agent D  │
         │               │    │ EDT      │     │ VC       │
         │               │    └────┬─────┘     └────┬─────┘
         │               │         │                │
         └───────────────┴─────────┴────────────────┘
                    CROSS-AGENT COMMUNICATION
```

### Key Principles

1. **Control Manager Decomposes** - Break task into repo-specific sub-tasks
2. **Spawn Dedicated Agents** - One agent per repository/branch
3. **Track Agent IDs** - Know who's working where
4. **Send Updates** - Use `addFollowup` for coordination
5. **Diamond Communication** - Agents can talk to each other directly

---

## API Tools for Fleet Management

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `launchAgent` | Spawn a new agent in a specific repo/branch |
| `listAgents` | See all agents and their status |
| `getAgentStatus` | Check specific agent's progress |
| `addFollowup` | Send message/instruction to running agent |
| `getAgentConversation` | Review agent's work |

### Launching an Agent

```bash
export PATH="/home/ubuntu/.local/bin:$PATH"

# Spawn agent in terraform-modules
(
  echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"control","version":"1.0"}}}'
  sleep 2
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"launchAgent","arguments":{
    "prompt": {"text": "TASK: Update vendor-connectors dependency to 202511.6.1\n\nCONTEXT: FSC Control Center has assigned you this task.\nCOORDINATION: Report completion via PR. Control manager agent ID: bc-a95ea075-a47a-482f-bf69-5d16b78a2c4c"},
    "source": {"repository": "https://github.com/FlipsideCrypto/terraform-modules", "ref": "main"}
  }}}'
  sleep 5
) | timeout 30 npx -y cursor-background-agent-mcp-server
```

### Sending a Followup to an Agent

```bash
AGENT_ID="bc-xxxxx"  # The spawned agent's ID

(
  echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"control","version":"1.0"}}}'
  sleep 2
  echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"addFollowup\",\"arguments\":{
    \"agentId\": \"$AGENT_ID\",
    \"prompt\": {\"text\": \"UPDATE: jbcom has released vendor-connectors 202511.6.2. Please update your PR accordingly.\"}
  }}}"
  sleep 5
) | timeout 30 npx -y cursor-background-agent-mcp-server
```

---

## Task Decomposition Pattern

### Step 1: Analyze Task

```
User Request: "Update all FSC repos to use latest jbcom packages"

Decomposition:
├── terraform-modules
│   └── Task: Update pyproject.toml with new versions
├── terraform-aws-secretsmanager
│   └── Task: Update requirements.txt
├── jbcom ecosystem (delegate to jbcom Control Center)
│   ├── extended-data-types: Verify latest release
│   ├── vendor-connectors: Verify latest release
│   └── lifecyclelogging: Verify latest release
```

### Step 2: Spawn Agents

```python
# Pseudocode for fleet management
agents = {}

# Spawn FSC repo agents
agents['tf-modules'] = spawn_agent(
    repo="FlipsideCrypto/terraform-modules",
    task="Update jbcom dependencies to latest versions",
    context=f"Control manager: {MY_AGENT_ID}"
)

agents['tf-aws-sm'] = spawn_agent(
    repo="FlipsideCrypto/terraform-aws-secretsmanager",
    task="Update jbcom dependencies to latest versions",
    context=f"Control manager: {MY_AGENT_ID}"
)

# Spawn jbcom Control Center agent
agents['jbcom-cc'] = spawn_agent(
    repo="jbcom/jbcom-control-center",
    task="Coordinate ecosystem releases for FSC update",
    context=f"""
    Control manager: {MY_AGENT_ID}
    FSC agents spawned: {agents['tf-modules']}, {agents['tf-aws-sm']}
    Please ensure packages are released and notify these agents directly.
    """
)
```

### Step 3: Monitor Fleet

```bash
# Check all agent statuses
(
  echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"control","version":"1.0"}}}'
  sleep 2
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listAgents","arguments":{}}}'
  sleep 5
) | timeout 20 npx -y cursor-background-agent-mcp-server | tail -1 | jq '.result.content[0].text | fromjson | .agents[] | select(.status == "RUNNING") | {id, name, repo: .source.repository}'
```

### Step 4: Coordinate Updates

When jbcom Control Center Agent has updates:
```bash
# jbcom CC Agent sends to FSC spawned agents
for agent_id in $FSC_AGENT_IDS; do
  send_followup $agent_id "Package vendor-connectors 202511.6.2 released. Update your PR."
done
```

---

## Counterparty Token Configuration

### FSC Control Center → jbcom

```bash
# FSC uses GITHUB_JBCOM_TOKEN to access jbcom repos
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh repo view jbcom/jbcom-control-center
```

### jbcom Control Center → FSC

```bash
# jbcom should have equivalent token for FSC repos
# This needs to be configured in jbcom-control-center
GH_TOKEN="$GITHUB_FSC_TOKEN" gh repo view FlipsideCrypto/terraform-modules
```

### Token Exchange Protocol

When spawning jbcom Control Center Agent, include token context:
```
TASK: Coordinate ecosystem releases

TOKENS AVAILABLE:
- Your GITHUB_JBCOM_TOKEN: Access to jbcom repos
- FSC expects you to have: GITHUB_FSC_TOKEN for FlipsideCrypto repos

COORDINATION:
- I am FSC Control Center agent: bc-a95ea075-a47a-482f-bf69-5d16b78a2c4c
- I have spawned these agents in FSC repos: [list]
- When you have updates, send followups to these agents directly
```

---

## Communication Patterns

### Pattern 1: Control Manager Broadcast

```
FSC CC → All FSC Agents: "Starting ecosystem update. Stand by."
```

### Pattern 2: Counterparty Delegation

```
FSC CC → jbcom CC Agent: "Need vendor-connectors 202511.7 with feature X"
jbcom CC Agent → jbcom EDT Agent: "Add feature X to EDT"
jbcom CC Agent → jbcom VC Agent: "Wait for EDT, then release VC"
jbcom CC Agent → FSC CC: "Release pipeline started. ETA 30 min."
```

### Pattern 3: Diamond Update

```
jbcom VC Agent → FSC tf-modules Agent: "vendor-connectors 202511.7 released"
jbcom VC Agent → FSC tf-aws-sm Agent: "vendor-connectors 202511.7 released"
```

### Pattern 4: Status Roll-up

```
FSC tf-modules Agent → FSC CC: "PR created: #210"
FSC tf-aws-sm Agent → FSC CC: "PR created: #45"
FSC CC → User: "All PRs created. Ready for review."
```

---

## Spawned Agent Instructions Template

When spawning an agent, include this context:

```markdown
# Agent Assignment

## Task
[Specific task for this agent]

## Repository
[Repo this agent is working in]

## Control Manager
- Agent ID: [your agent ID]
- Control Center: FSC Control Center
- Coordination channel: addFollowup API

## Sibling Agents
[List other agents working on related tasks]

## Counterparty
- jbcom Control Center Agent: [ID if spawned]
- Direct communication enabled: YES

## Reporting
1. Create PR when work complete
2. Send followup to control manager with PR link
3. If blocked, send followup requesting help

## Token Access
- You have: [tokens available to this agent]
- For jbcom repos: Ask control manager to spawn jbcom agent
```

---

## Implementation Checklist

### FSC Control Center (This Repo)

- [x] Document fleet management protocol
- [ ] Create spawn helper scripts
- [ ] Create fleet status dashboard
- [ ] Implement task decomposition templates
- [ ] Test agent spawning
- [ ] Test agent communication

### jbcom Control Center

- [ ] Add FSC token (GITHUB_FSC_TOKEN)
- [ ] Document counterparty relationship
- [ ] Enable agent-to-agent communication patterns
- [ ] Create reciprocal spawn capabilities

### Coordination

- [ ] Test cross-organization agent spawning
- [ ] Test diamond communication pattern
- [ ] Establish emergency escalation
- [ ] Document failure recovery

---

## Best Practices

### DO

- ✅ Spawn dedicated agents per repository
- ✅ Include control manager ID in spawn context
- ✅ Track all spawned agent IDs
- ✅ Use addFollowup for coordination
- ✅ Let agents communicate directly when appropriate

### DON'T

- ❌ Have one agent switch between repos repeatedly
- ❌ Forget to track spawned agent IDs
- ❌ Spawn agents without coordination context
- ❌ Ignore agent status (RUNNING/ERROR/EXPIRED)
- ❌ Let agents work in isolation

---

**Last Updated**: 2025-11-28
**Status**: Defining protocol
**Next Step**: Test agent spawning and communication
