# Fleet Coordination Channel

> **Control Manager**: bc-7f35d6f6-a052-4f88-9dba-252d359b8395  
> **Coordination PR**: #251 (this branch)  
> **Last Updated**: 2025-11-29

## Purpose

This file and its associated PR serve as the **bidirectional coordination channel** for the Cursor agent fleet.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Control Manager                             │
│                                                                 │
│  ┌──────────────┐                      ┌──────────────────┐    │
│  │ OUTBOUND     │                      │ INBOUND          │    │
│  │ Fan-out loop │                      │ PR Comment poll  │    │
│  │ (30s cycle)  │                      │ (15s cycle)      │    │
│  └──────┬───────┘                      └────────▲─────────┘    │
│         │                                       │              │
└─────────┼───────────────────────────────────────┼──────────────┘
          │                                       │
          ▼                                       │
    Sub-Agents ───────────────────────────────────┘
         Comment on coordination PR with @cursor
```

## Message Protocol

Sub-agents report by commenting on the coordination PR:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `@cursor ✅ DONE:` | Task completed | `@cursor ✅ DONE: bc-abc123 PR #247 merged` |
| `@cursor ⚠️ BLOCKED:` | Needs intervention | `@cursor ⚠️ BLOCKED: bc-abc123 CI failing` |
| `@cursor 📊 STATUS:` | Progress update | `@cursor 📊 STATUS: bc-abc123 50% complete` |
| `@cursor 🔄 HANDOFF:` | Ready for next step | `@cursor 🔄 HANDOFF: bc-abc123 PR ready for review` |

## Active Fleet

| Agent ID | Task | PR | Status | Last Check |
|----------|------|-----|--------|------------|
| bc-d28321ca | Fix py3.9 CI for directed-inputs-class | #247 | 🔄 Running | - |
| bc-8e620589 | Fix critical issues in python-terraform-bridge | #250 | 🔄 Running | - |

## Coordination Log

### 2025-11-29 22:45 UTC
- Control manager (bc-7f35d6f6) initialized fleet coordination channel
- Sent status check follow-ups to active agents
- Branch protection rules configured for main branch

---

## Running the Coordinator

```bash
# Via CLI
cursor-fleet coordinate --pr 251 --agents bc-d28321ca,bc-8e620589

# Or via process-compose
COORDINATION_PR=251 AGENT_IDS=bc-d28321ca,bc-8e620589 process-compose up fleet-coordinator
```

## API

The coordination is built into the `Fleet` class:

```typescript
import { Fleet } from "@jbcom/cursor-fleet";

const fleet = new Fleet();

// Run bidirectional coordination
await fleet.coordinate({
  coordinationPr: 251,
  repo: "jbcom/jbcom-control-center",
  outboundInterval: 60000,  // Check agents every 60s
  inboundInterval: 15000,   // Poll PR comments every 15s
  agentIds: ["bc-d28321ca", "bc-8e620589"],
});

// Or use individual methods
const comments = fleet.fetchPRComments("jbcom/jbcom-control-center", 251);
fleet.postPRComment("jbcom/jbcom-control-center", 251, "Hello from coordinator!");
```
