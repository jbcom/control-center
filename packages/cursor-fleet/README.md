# @jbcom/cursor-fleet

Unified Cursor Background Agent fleet management for control centers.

## Installation

```bash
pnpm add @jbcom/cursor-fleet
# or
npm install @jbcom/cursor-fleet
```

Requires `cursor-background-agent-mcp-server` as a peer dependency:

```bash
pnpm add -D cursor-background-agent-mcp-server
```

## Environment

```bash
export CURSOR_API_KEY="your-cursor-api-key"

# Optional: if running mcp-proxy
export MCP_PROXY_CURSOR_AGENTS_URL="http://localhost:3011"
```

## CLI Usage

```bash
# List all agents
cursor-fleet list
cursor-fleet list --running
cursor-fleet list --json

# Spawn an agent
cursor-fleet spawn https://github.com/org/repo "Fix the authentication bug"
cursor-fleet spawn https://github.com/org/repo "Update dependencies" --ref feature-branch

# Send follow-up
cursor-fleet followup bc-xxxx "Also check the test coverage"

# Broadcast to all running agents
cursor-fleet broadcast "Status update: PR merged" --running

# Get conversation
cursor-fleet conversation bc-xxxx
cursor-fleet conversation bc-xxxx --json --last 50

# Archive before expiration
cursor-fleet archive bc-xxxx
cursor-fleet archive bc-xxxx --output ./recovery/important-session.json

# Fleet summary
cursor-fleet summary

# Diamond pattern orchestration
cursor-fleet diamond \
  --targets '[{"repository":"https://github.com/org/repo1","task":"Update package"},{"repository":"https://github.com/org/repo2","task":"Update package"}]' \
  --counterparty '{"repository":"https://github.com/jbcom/jbcom-control-center","task":"Coordinate updates"}' \
  --control-center "FSC Control Center"

# Wait for agent completion
cursor-fleet wait bc-xxxx --timeout 600000
```

## Programmatic Usage

```typescript
import { Fleet } from "@jbcom/cursor-fleet";

const fleet = new Fleet({
  // Optional configuration
  apiKey: process.env.CURSOR_API_KEY,
  archivePath: "./memory-bank/recovery",
});

// List agents
const agents = await fleet.list();
const running = await fleet.running();

// Spawn with context
const result = await fleet.spawn({
  repository: "https://github.com/FlipsideCrypto/terraform-modules",
  task: "Add secrets wrapper for new provider",
  ref: "main",
  context: {
    controlManagerId: "bc-my-agent-id",
    controlCenter: "FSC Control Center",
    relatedAgents: ["bc-other-agent"],
    metadata: { priority: "high" },
  },
});

if (result.success) {
  console.log(`Spawned: ${result.data.id}`);
}

// Follow-up communication
await fleet.followup(result.data.id, "Remember to add tests");

// Broadcast to multiple
await fleet.broadcast(
  ["bc-agent-1", "bc-agent-2"],
  "Dependency update complete, please rebase"
);

// Archive before expiration (CRITICAL!)
await fleet.archive(result.data.id);

// Diamond pattern for counterparty coordination
const diamond = await fleet.createDiamond({
  targetRepos: [
    { repository: "https://github.com/org/repo1", task: "Update X" },
    { repository: "https://github.com/org/repo2", task: "Update Y" },
  ],
  counterparty: {
    repository: "https://github.com/jbcom/jbcom-control-center",
    task: "Coordinate ecosystem package release",
  },
  controlCenter: "FSC Control Center",
});

// Wait for completion
const final = await fleet.waitFor(diamond.data.counterpartyAgent.id, {
  timeout: 300000,
  pollInterval: 15000,
});
```

## Architecture

### MCP Communication

The package communicates with Cursor's agent API via the Model Context Protocol (MCP):

1. **Proxy mode** (preferred): If `mcp-proxy` is running, uses HTTP
2. **Direct mode** (fallback): Spawns `cursor-background-agent-mcp-server` via stdio

### Diamond Pattern

For cross-organization coordination:

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Manager                          │
│                  (FSC Control Center)                       │
└──────────────┬────────────────────────┬────────────────────┘
               │                        │
               ▼                        ▼
┌──────────────────────┐  ┌──────────────────────────────────┐
│   Target Agents      │  │      Counterparty Agent          │
│  (terraform-modules, │  │   (jbcom-control-center)         │
│   other FSC repos)   │  │                                  │
└──────────────────────┘  └───────────────┬──────────────────┘
                                          │
                                          ▼
                          ┌──────────────────────────────────┐
                          │   Counterparty's Sub-Agents      │
                          │  (vendor-connectors, etc.)       │
                          └──────────────────────────────────┘
```

The counterparty agent receives IDs of target agents and can communicate directly with them.

## Critical Limitations

⚠️ **Conversation Expiration**: Agent conversations are purged after ~24-48 hours. Archive important sessions promptly!

```typescript
// Archive your own session periodically
const myId = (await fleet.running()).data?.[0]?.id;
if (myId) {
  await fleet.archive(myId);
}
```

## Integration with Control Centers

Both FSC and jbcom control centers should use this package as their single source of truth for agent management. This eliminates duplicate shell scripts and ensures consistent behavior.

```typescript
// In FSC control center
import { Fleet } from "@jbcom/cursor-fleet";

// In jbcom control center  
import { Fleet } from "@jbcom/cursor-fleet";

// Same API, same behavior, coordinated fleet management
```
