# Fleet Coordination

## cursor-fleet Package

The `@jbcom/cursor-fleet` package in `packages/cursor-fleet/` provides Cursor Background Agent management.

### Building

```bash
cd /workspace/packages/cursor-fleet
npm install
npm run build
```

### CLI Commands

```bash
# List all agents
node dist/cli.js list

# Get agent status
node dist/cli.js status <agent-id>

# Get agent conversation
node dist/cli.js conversation <agent-id>

# Replay/recover agent (with splitting)
node dist/cli.js replay <agent-id> -o <output-dir> -v

# Split existing conversation.json
node dist/cli.js split <conversation.json> -o <output-dir>

# Spawn new agent
node dist/cli.js spawn --repo owner/repo --task "Task description"

# Send followup message
node dist/cli.js followup <agent-id> "Message"

# Archive agent data
node dist/cli.js archive <agent-id> -o <output-dir>
```

### Replay Features

The `replay` command provides comprehensive conversation recovery:

```bash
node dist/cli.js replay bc-7f35d6f6-a052-4f88-9dba-252d359b8395 \
  -o /workspace/.cursor/recovery/bc-7f35d6f6-a052-4f88-9dba-252d359b8395 \
  -v
```

**Output structure:**
```
<output-dir>/
├── conversation.json    # Full conversation
├── agent.json           # Agent metadata
├── analysis.json        # Extracted tasks/PRs
├── metadata.json        # Split metadata
├── INDEX.md             # Message index with links
├── REPLAY_SUMMARY.md    # Human-readable summary
├── messages/            # Individual message files
│   ├── 0001-USER.md
│   ├── 0001-USER.json
│   └── ...
└── batches/             # Batch files (10 messages each)
    ├── batch-001.md
    ├── batch-001.json
    └── ...
```

**Analysis extracts:**
- Completed tasks (✅ patterns)
- Outstanding tasks (⏳ patterns)
- PRs created/merged
- Blockers identified
- Key decisions

## Hold-Open PR Pattern

For multi-merge sessions, create a **draft PR** as a coordination channel:

```bash
# 1. Create holding branch
git checkout -b agent/holding-session-$(date +%Y%m%d-%H%M%S)
echo "# Session Notes" >> .cursor/agents/session.md
git add -A && git commit -m "chore: agent holding PR"
git push -u origin HEAD

# 2. Create as DRAFT to avoid AI reviewers
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --draft \
  --title "[HOLDING] Agent session (DO NOT MERGE)" \
  --body "Communication channel. DO NOT MERGE until complete."

# 3. Work via interim PRs
git checkout main && git pull
git checkout -b fix/specific-issue
# ... make fix ...
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch

# 4. When done, close holding PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr close <HOLDING_PR_NUM>
```

**Why draft?** Prevents Amazon Q, Gemini, CodeRabbit from reviewing the holding PR.

## Agent Reporting Protocol

Sub-agents can report status via PR comments:

| Format | Meaning |
|--------|---------|
| `@cursor ✅ DONE: [summary]` | Task completed |
| `@cursor ⚠️ BLOCKED: [issue]` | Needs intervention |
| `@cursor 📊 STATUS: [progress]` | Progress update |

## API Classes

### CursorAPI (Direct)

```typescript
import { CursorAPI } from "@jbcom/cursor-fleet";

const api = new CursorAPI(process.env.CURSOR_API_KEY);

// List agents
const agents = await api.listAgents();

// Get status
const agent = await api.getAgentStatus("bc-xxx");

// Get conversation
const conversation = await api.getAgentConversation("bc-xxx");

// Launch agent
const newAgent = await api.launchAgent({
  prompt: { text: "Fix the CI" },
  source: { repository: "jbcom/vendor-connectors" }
});

// Send followup
await api.addFollowup("bc-xxx", { text: "Check PR feedback" });
```

### Fleet (High-level)

```typescript
import { Fleet } from "@jbcom/cursor-fleet";

const fleet = new Fleet({ apiKey: process.env.CURSOR_API_KEY });

// Replay with splitting
const result = await fleet.replay("bc-xxx", {
  outputDir: "/path/to/output",
  verbose: true
});

// Split existing conversation
await fleet.splitExisting("/path/to/conversation.json", "/path/to/output");

// Load previous replay
const data = await fleet.loadReplay("/path/to/archive");
```

## Environment Variables

```bash
export CURSOR_API_KEY="..."  # Required for API calls
export GITHUB_JBCOM_TOKEN="..." # For GitHub operations
```

## process-compose Integration

Add to `process-compose.yml` for long-running coordination:

```yaml
fleet-watcher:
  command: |
    node /workspace/packages/cursor-fleet/dist/cli.js list --json | \
    jq -r '.[] | select(.status == "RUNNING") | .id'
  depends_on: []
```

---

**Package:** @jbcom/cursor-fleet
**Location:** packages/cursor-fleet/
**Last Updated:** 2025-11-30
