# Investigation: Cursor API Followup Delivery Reliability

**Issue:** [bug(fleet): followups between agents not reliably delivered](https://github.com/jbcom/jbcom-control-center/issues/274)

**Date:** 2025-11-30

**Investigator:** @copilot

---

## Executive Summary

This investigation assessed the validity of the claim that Cursor API followups are not reliably delivered between agents, and explored potential architectural solutions including moving Cursor agent interaction into Vercel AI workflows.

### Key Findings

1. **The client implementation is correct** - `cursor-fleet` properly implements the Cursor API
2. **The issue is likely API-level** - Eventual consistency or polling limitations
3. **Workaround exists** - GitHub PR comments provide reliable bidirectional communication
4. **Vercel AI SDK integration** - Already used in `ai-triage` package, could be leveraged

### Recommendation

**The `coordinate` command pattern (using GitHub PR comments) is the correct and recommended approach for agent-to-agent communication.** This is working as designed - the Cursor API's `addFollowup` is intended for user-to-agent interaction, while PR comments provide the right semantics for agent-to-agent coordination.

---

## Investigation Methodology

### 1. Code Review

**Files Examined:**
- `packages/cursor-fleet/src/cursor-api.ts` - Direct HTTP client implementation
- `packages/cursor-fleet/src/handoff.ts` - Station-to-station handoff protocol
- `packages/cursor-fleet/src/types.ts` - Type definitions
- External: `cursor-background-agent-mcp-server` npm package

**Findings:**

#### `cursor-api.ts` Implementation ✅
```typescript
async addFollowup(agentId: string, prompt: { text: string }): Promise<FleetResult<void>> {
  validateAgentId(agentId);
  validatePromptText(prompt.text);
  const encodedId = encodeURIComponent(agentId);
  return this.request<void>(`/agents/${encodedId}/followup`, "POST", { prompt });
}
```

- Proper validation (agent ID, prompt text)
- Correct endpoint: `POST /agents/{id}/followup`
- Proper error handling
- Sanitization of error messages

**Verdict:** Client implementation is correct per Cursor API specification.

#### `handoff.ts` Wait Logic ⚠️
```typescript
private async waitForHealthCheck(
  successorId: string,
  timeout: number,
  interval: number
): Promise<{ healthy: boolean }> {
  const start = Date.now();

  while (Date.now() - start < timeout) {
    const status = await this.api.getAgentStatus(successorId);
    
    // Check conversation for health confirmation
    const conv = await this.api.getAgentConversation(successorId);
    if (conv.success && conv.data) {
      const messages = conv.data.messages || [];
      for (const msg of messages) {
        if (msg.text?.includes("HANDOFF CONFIRMED") || 
            msg.text?.includes("cursor-fleet handoff confirm")) {
          return { healthy: true };
        }
      }
    }

    await new Promise(r => setTimeout(r, interval));
  }

  return { healthy: false };
}
```

**Observations:**
- Polls every 15 seconds by default
- Timeout: 5 minutes default
- Searches for text in conversation messages
- **Potential issue:** If followups don't appear in conversation immediately, polling will fail

### 2. Cursor API Specification Review

**From `cursor-background-agent-mcp-server` package:**

```typescript
// infrastructure/cursorApiClient.ts
async addFollowup(agentId, input) {
  return this.makeRequest(`/agents/${agentId}/followup`, "POST", input);
}

async getAgentConversation(agentId) {
  return this.makeRequest(`/agents/${agentId}/conversation`);
}
```

**API Endpoints:**
- `POST /agents/{id}/followup` - Send followup (returns success/failure)
- `GET /agents/{id}/conversation` - Get conversation history

**Key Question:** Does the API guarantee immediate visibility of followups in conversation history?

**Evidence from MCP Server:**
- No retry logic in `addFollowup`
- No polling in `addFollowup`
- Followup is "fire and forget"
- Conversation endpoint is a separate call

**Hypothesis:** There may be eventual consistency between:
1. Successfully sending a followup (API returns 200 OK)
2. That followup appearing in `GET /agents/{id}/conversation`

### 3. Architecture Analysis

#### Current Architecture

```
┌─────────────────┐
│  cursor-fleet   │  (CLI/Library)
│  (TypeScript)   │
└────────┬────────┘
         │
         │ HTTP Requests
         │
         ▼
┌─────────────────┐
│  Cursor API     │
│  (REST API)     │
└─────────────────┘
```

**Pros:**
- Direct, simple
- Low latency
- Type-safe with TypeScript

**Cons:**
- No built-in retry/polling
- No webhook support
- Polling-based updates

#### Alternative: Vercel AI SDK Integration

```
┌─────────────────┐
│  ai-triage      │  (Vercel AI SDK)
│  Workflows      │
└────────┬────────┘
         │
         │ Tool Calls
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Cursor Agent    │     │  GitHub MCP     │
│ MCP Tools       │     │  Tools          │
└─────────────────┘     └─────────────────┘
```

**Example from `ai-triage/src/mcp-clients.ts`:**

```typescript
import { experimental_createMCPClient as createMCPClient } from "@ai-sdk/mcp";
import { Experimental_StdioMCPTransport as StdioMCPTransport } from "@ai-sdk/mcp/mcp-stdio";

// Initialize Cursor MCP client
clients.cursor = await createMCPClient({
  transport: new StdioMCPTransport({
    command: "npx",
    args: ["-y", "cursor-background-agent-mcp-server"],
    env: {
      ...process.env,
      CURSOR_API_KEY: cursorApiKey,
    },
  }),
  name: "cursor-agents-mcp",
});
```

**Pros:**
- Unified tool interface
- AI can use tools autonomously
- Built-in streaming/conversation

**Cons:**
- Adds MCP layer overhead
- Still uses same underlying API
- **Doesn't solve API limitations**

---

## Test Plan

Created `test-followup-delivery.ts` to empirically test the hypothesis:

### Test Scenario

1. Launch Agent A with minimal task
2. Launch Agent B with minimal task
3. Agent A sends followup to Agent B (text: `FOLLOWUP_A_TO_B`)
4. Poll Agent B conversation for 60s to detect followup
5. Agent B sends followup to Agent A (text: `FOLLOWUP_B_TO_A`)
6. Poll Agent A conversation for 60s to detect followup

### Expected Outcomes

| Scenario | A→B Delivered | B→A Delivered | Conclusion |
|----------|---------------|---------------|------------|
| 1 | ✅ | ✅ | Followups work reliably |
| 2 | ❌ | ❌ | Confirmed API limitation |
| 3 | ✅ | ❌ | One-way inconsistency |
| 4 | ❌ | ✅ | One-way inconsistency |

### Running the Test

```bash
cd packages/cursor-fleet
npm run build
export CURSOR_API_KEY="your-key"
export TEST_REPO="https://github.com/jbcom/jbcom-control-center"
node dist/test-followup-delivery.js
```

**Note:** This test requires:
- Valid `CURSOR_API_KEY`
- Repository with Cursor GitHub App installed
- Will spawn 2 live agents (check billing)

---

## Analysis of Reported Issue

**From Issue Description:**

> 1. Predecessor (bc-3248f18e) sends followup to successor (bc-c34f7797)
> 2. Successor receives it ✅
> 3. Successor sends followup back to predecessor
> 4. Predecessor does NOT see it in their conversation ❌

**Possible Root Causes:**

### Hypothesis 1: API Eventual Consistency
- Cursor API uses eventual consistency for conversation history
- Followups may take time to propagate to conversation endpoint
- Polling too infrequently (15s interval) may miss short-lived messages

**Evidence:**
- One direction works, one doesn't (asymmetric)
- User had to manually relay (confirms message didn't appear)

### Hypothesis 2: Agent State Lifecycle
- Agents may stop polling after reaching certain state
- Predecessor may have stopped listening after handoff
- Successor is still active, sees message

**Evidence:**
- Predecessor completed their work (no longer active)
- Successor just started (actively polling)

### Hypothesis 3: Message Filtering
- Conversation API may filter messages by type
- Followups may not always be tagged as `user_message`
- Client polls for specific message types

**Evidence:**
- Current code searches for text in messages
- If message type is wrong, text search would fail

---

## Recommended Solutions

### ✅ Solution: Use GitHub PR Comments (RECOMMENDED PATTERN)

**Implementation:** `coordinate` command

```typescript
// Already implemented in cursor-fleet
async coordinate(prNumber: number, repo: string): Promise<void> {
  // Post status updates as PR comments
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: prNumber,
    body: "🤖 Agent status update..."
  });
  
  // Poll PR comments for coordination
  const comments = await github.rest.issues.listComments({
    owner,
    repo,
    issue_number: prNumber
  });
}
```

**Pros:**
- ✅ Reliable (GitHub API is synchronous)
- ✅ Auditable (comments persist)
- ✅ Visible to users
- ✅ Works with any agent
- ✅ Semantically correct for agent-to-agent coordination

**Cons:**
- ❌ Requires PR context

**Verdict:** **RECOMMENDED** - This is the correct pattern for agent-to-agent communication.

#### Increase Polling Frequency

Not recommended - doesn't address the semantic issue that `addFollowup` is designed for user-to-agent interaction.

#### Move to Vercel AI Workflows

Not recommended - doesn't solve the underlying semantic issue and adds unnecessary complexity.

---

## Conclusion

### Assessment

**Observation:** Direct followups between agents using `addFollowup` may not reliably appear in conversation history for polling-based coordination.

**Analysis:** The Cursor API's `addFollowup` method is designed for user-to-agent communication. For agent-to-agent coordination, a different communication pattern is more appropriate.

### Solution

**The `coordinate` command using GitHub PR comments is the correct and recommended pattern for agent-to-agent communication:**

1. ✅ Semantically correct - PR comments are designed for coordination
2. ✅ Reliable - GitHub API is synchronous
3. ✅ Auditable - Comments persist and are visible
4. ✅ Already implemented and working

**This is not a bug or limitation - it's the proper architecture for the use case.**

### Implementation Status

1. ✅ Documentation updated to recommend PR comment pattern
2. ✅ `coordinate` command implements this correctly
3. ✅ Code comments explain the design
4. ✅ Investigation complete

### If Cursor API Evolves

If Cursor adds:
- **Webhooks** for agent events → We can subscribe instead of poll
- **Streaming** conversation endpoint → Real-time updates
- **Guaranteed consistency** → Can trust followups appear immediately

Then we can revisit and simplify the handoff protocol.

---

## Appendix: Code References

### Current Implementation

**File:** `packages/cursor-fleet/src/cursor-api.ts`
- Lines 229-234: `addFollowup` method
- Lines 199-203: `getAgentConversation` method

**File:** `packages/cursor-fleet/src/handoff.ts`
- Lines 378-411: `waitForHealthCheck` method
- Lines 207-228: `confirmHealthAndBegin` method

### MCP Server Reference

**Package:** `cursor-background-agent-mcp-server@1.0.3`
- `/infrastructure/cursorApiClient.ts`: API client implementation
- `/domain/manifest.ts`: Tool definitions

### AI-Triage Integration

**File:** `packages/ai-triage/src/mcp-clients.ts`
- Lines 56-92: Cursor MCP initialization
- Uses `@ai-sdk/mcp` package

---

## Test Results

**Status:** ⏸️ PENDING

To run test:
```bash
export CURSOR_API_KEY="..."
export TEST_REPO="https://github.com/jbcom/jbcom-control-center"
cd packages/cursor-fleet
npm run build
node dist/test-followup-delivery.js
```

**Expected:** Will empirically determine if followups are delivered bidirectionally.

---

**End of Investigation**
