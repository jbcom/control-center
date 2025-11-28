# Agent Recovery Guide

## Overview

When agents crash, error out, or expire, work can be recovered using the tools in this repository.

## Recovery Locations

### Cursor Agent Sessions
- **Recovery Directory**: `.cursor/recovery/<agent-id>/`
- **Conversation Export**: `conversation.json`
- **Extracted Artifacts**: `branches.txt`, `prs.txt`, `files.txt`, `repos.txt`

### Recovery Scripts
| Script | Location | Purpose |
|--------|----------|---------|
| `agent-recover` | `.cursor/scripts/` | Full forensic recovery |
| `agent-triage-local` | `.cursor/scripts/` | Offline analysis |
| `triage-pipeline` | `.cursor/scripts/` | Batch processing |
| `replay_agent_session.py` | `scripts/` | Memory bank update |

## Recovery Workflow

### Step 1: Get Agent ID

From Cursor URL: `https://cursor.com/agents?selectedBcId=bc-7d1997bf-56b0-4e1f-9f6d-2ba4382d3ac4`
Agent ID: `bc-7d1997bf-56b0-4e1f-9f6d-2ba4382d3ac4`

### Step 2: Check for Existing Recovery

```bash
ls -la .cursor/recovery/bc-7d1997bf-56b0-4e1f-9f6d-2ba4382d3ac4/
```

### Step 3: If conversation.json Exists

```bash
python scripts/replay_agent_session.py \
  --conversation .cursor/recovery/bc-7d1997bf-56b0-4e1f-9f6d-2ba4382d3ac4/conversation.json \
  --session-label "recovery-session"
```

### Step 4: If No conversation.json

User must export from Cursor web UI:
1. Go to https://cursor.com/agents
2. Select the agent
3. Export conversation
4. Save to `.cursor/recovery/<agent-id>/conversation.json`

Then run Step 3.

## Replay Script Output

The `replay_agent_session.py` script generates:

1. **Chronological History** (`memory-bank/recovery/<label>-chronological-history.md`)
   - Total message count
   - Extracted PRs, branches, repos, commits, files
   - Key events timeline
   - User instructions summary

2. **Condensed Timeline** (`memory-bank/recovery/<label>-replay.md`)
   - Last N messages formatted

3. **Delegation Plan** (`memory-bank/recovery/<label>-delegation.md`)
   - Actionable next steps
   - CLI invocation examples

4. **Progress Entry** (appended to `memory-bank/progress.md`)
   - Session summary
   - Delegation inputs

5. **Active Context** (updates `memory-bank/activeContext.md`)
   - Current focus
   - Next actions

## Manual Analysis

If scripts fail, manually analyze:

```bash
# Extract PRs
jq -r '.messages[].text' conversation.json | grep -oE '#[0-9]+' | sort -u

# Extract branches
jq -r '.messages[].text' conversation.json | grep -oE '(feat|fix|docs)/[a-z0-9-]+' | sort -u

# Extract files
jq -r '.messages[].text' conversation.json | grep -oE '\S+\.(py|md|yml|yaml)' | sort -u

# Last 5 messages
jq '.messages[-5:]' conversation.json
```

## Creating Handoff from Recovery

After analyzing a failed session:

1. **Document Completed Work**
   - What PRs were created/merged
   - What files were modified
   - What tests passed

2. **Document Incomplete Work**
   - What was attempted but not finished
   - What errors occurred
   - What was the agent trying to do last

3. **Document Next Steps**
   - Clear actionable items
   - Dependencies and blockers
   - Links to relevant PRs/issues

## Example Recovery Session

```bash
# 1. Create recovery directory
mkdir -p .cursor/recovery/bc-example-id/

# 2. User exports conversation.json to that directory

# 3. Run replay
python scripts/replay_agent_session.py \
  --conversation .cursor/recovery/bc-example-id/conversation.json \
  --session-label "example-recovery" \
  --timeline-limit 50

# 4. Check output
cat memory-bank/recovery/example-recovery-chronological-history.md

# 5. Create handoff based on findings
```

## Troubleshooting

### "Memory bank directory not found"
```bash
mkdir -p memory-bank/recovery
```

### "jq: command not found"
Use Python instead:
```bash
python -c "import json; print(json.load(open('conversation.json'))['messages'][-5:])"
```

### "No significant work to recover"
Agent crashed immediately (< 3 messages). No recovery needed.

---

**Last Updated**: 2025-11-28
