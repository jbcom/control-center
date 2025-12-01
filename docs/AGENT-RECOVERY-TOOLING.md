# Agentic Diff & Recovery Protocol

## Overview

When agents crash, error out, or expire, their work can be lost. This protocol uses **aider** (AI pair programming tool) combined with **agent conversation history** and **GitHub MCP** to perform forensic recovery.

## The Problem

Agents can fail in ways that leave work incomplete:
- ❌ **ERROR state** - Crashed before committing work
- ❌ **EXPIRED** - Timed out mid-task
- ❌ **Uncommitted changes** - Work done but not pushed
- ❌ **Lost context** - Next agent doesn't know what was done

Traditional recovery requires:
1. User manually reviewing conversation
2. User figuring out what was lost
3. User briefing next agent
4. Wasted time and context loss

## The Solution: Agentic Diff

Use **aider** to programmatically compare:
- What the agent **SAID** they did (from conversation)
- What **ACTUALLY** exists (in repositories)
- What's **MISSING** (uncommitted, lost, incomplete)

```
Agent Conversation (SAID)  ←→  Repository State (ACTUAL)  =  Diff (MISSING)
        ↓                            ↓                           ↓
   "I created X"               git log shows...          Recovery plan
   "I fixed Y"                 File doesn't exist         
   "I committed Z"             PR wasn't created          
```

---

## Installation

### In Dockerfile (for future cloud agents)
```dockerfile
RUN uv tool install aider-chat && aider --version
```

### In Current Environment
```bash
uv tool install aider-chat
export PATH="/root/.local/bin:$PATH"
aider --version
```

---

## Recovery Workflow

### Phase 1: Detect Recovery Scenario

When starting a new agent session, check for handoff:

```bash
# Check for handoff PR
gh pr list --label handoff --state open

# If no handoff PR exists, check for recent ERROR/EXPIRED agents
cursor-agents list | jq '.agents[] | 
  select(.source.repository == "github.com/jbcom/jbcom-control-center") |
  select(.status == "ERROR" or .status == "EXPIRED") |
  {id, status, name, branch: .target.branchName}'
```

**Scenarios:**
- ✅ **Handoff PR exists** → Clean handoff, follow normal process
- ⚠️ **No handoff, recent ERROR/EXPIRED** → **DELEGATE to forensic recovery sub-agent**

### Phase 1.5: Sub-Agent Delegation (PREFERRED METHOD)

**Instead of running aider yourself**, delegate forensic recovery to a specialized sub-agent:

```bash
# Launch a sub-agent for forensic recovery
FAILED_AGENT_ID="bc-2f734412-e52c-4c56-b34d-03cf35ad67f0"

# Get their conversation first
cursor-agents conversation $FAILED_AGENT_ID > /tmp/failed_agent.json
MSG_COUNT=$(jq '.messages | length' /tmp/failed_agent.json)

# Create comprehensive recovery task
RECOVERY_TASK="Forensic Recovery: Agent $FAILED_AGENT_ID

SITUATION:
- Agent $FAILED_AGENT_ID ended in ERROR/EXPIRED state
- They had $MSG_COUNT messages of conversation
- Their conversation is saved at /tmp/failed_agent.json

YOUR TASK:
1. Read their full conversation from /tmp/failed_agent.json
2. Extract all files, branches, and PRs they mentioned
3. Use aider with claude-opus-4 to compare what they SAID vs what EXISTS
4. Check git history: git log --all --oneline
5. Check branches: git branch -a
6. Check PRs: gh pr list --limit 50
7. Generate a structured recovery report:
   ✅ COMPLETED - Work that was finished
   ⚠️ PARTIAL - Work started but incomplete  
   ❌ LOST - Work claimed but not found
   🔧 RECOVERY PLAN - Specific steps to restore

OUTPUT:
Create a file: /workspace/RECOVERY_REPORT_${FAILED_AGENT_ID}.md

Use aider extensively for the forensic analysis."

# Launch recovery sub-agent (returns immediately, agent runs in background)
cursor-agents create "$RECOVERY_TASK"

# Monitor the sub-agent
cursor-agents list | grep -i "forensic"

# When complete, retrieve their findings
ls -la /workspace/RECOVERY_REPORT_*.md
```

**Why Sub-Agent Delegation is Superior:**
- ✅ **Specialized focus** - Recovery agent only does recovery
- ✅ **Parallel execution** - You continue your work while they investigate
- ✅ **Clean separation** - Their aider usage doesn't interfere with yours
- ✅ **Persistent results** - They create files you can read
- ✅ **Fault tolerance** - If they fail, you can try different approach

### Phase 2: Retrieve Agent Conversation

```bash
# Get the failed agent's conversation
FAILED_AGENT_ID="bc-2f734412-e52c-4c56-b34d-03cf35ad67f0"
cursor-agents conversation $FAILED_AGENT_ID > /tmp/failed_agent.json

# Check message count
jq '.messages | length' /tmp/failed_agent.json

# If only 1-2 messages → agent crashed immediately
# If 50+ messages → agent did work before failing
```

### Phase 3: Reverse Chronological Analysis

Work **backwards** from the agent's last messages to understand what they were doing:

```bash
# Get last 10 messages
jq '.messages[-10:] | .[] | {
  type,
  preview: .text[0:300]
}' /tmp/failed_agent.json

# Extract file paths mentioned
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '\S+\.(py|ts|md|yml|toml|json)' | \
  sort -u > /tmp/mentioned_files.txt

# Extract branches mentioned
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '(feat|fix|docs|refactor)/[a-z0-9-]+' | \
  sort -u > /tmp/mentioned_branches.txt

# Extract PRs mentioned
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '#[0-9]+' | \
  sort -u > /tmp/mentioned_prs.txt
```

### Phase 4: Build Agentic Diff with Aider

Use aider to systematically check what exists vs what the agent claimed:

```bash
cd /workspace

# Create aider recovery prompt
cat > /tmp/recovery_prompt.txt << 'EOF'
FORENSIC RECOVERY ANALYSIS

Previous agent (ID: $FAILED_AGENT_ID) was in ERROR/EXPIRED state.

From their conversation, they claimed to work on:
- Files: $(cat /tmp/mentioned_files.txt | tr '\n' ', ')
- Branches: $(cat /tmp/mentioned_branches.txt | tr '\n' ', ')
- PRs: $(cat /tmp/mentioned_prs.txt | tr '\n' ', ')

For EACH file mentioned:
1. Check if it exists in the repository
2. Check git history: git log --all --oneline -- <file>
3. If it exists: Compare to what they said they'd do
4. If missing: Note it as LOST WORK

For EACH branch mentioned:
1. Check if branch exists: git branch -a | grep <branch>
2. If exists: Check commit history since their start time
3. If missing: Note as UNCOMMITTED or DELETED

For EACH PR mentioned:
1. Check if PR exists and status
2. Check if it was merged or closed
3. Check commit count vs their claims

Output a structured recovery report:
- ✅ COMPLETED: Work that was finished
- ⚠️ PARTIAL: Work started but incomplete
- ❌ LOST: Work claimed but not found
- 🔧 RECOVERY PLAN: Steps to restore state
EOF

# Run aider with the prompt (requires ANTHROPIC_API_KEY or OPENAI_API_KEY)
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
aider --message "$(cat /tmp/recovery_prompt.txt)" \
      --no-auto-commits \
      --yes \
      --model claude-opus-4-20250514 \
      > /tmp/aider_recovery_report.txt
```

### Phase 5: Use GitHub MCP for Repository State

Cross-reference aider's findings with GitHub MCP:

```bash
# Check all branches in repo
github-mcp list_branches '{"owner": "jbcom", "repo": "jbcom-control-center"}'

# Check specific files in branches mentioned
for branch in $(cat /tmp/mentioned_branches.txt); do
  echo "=== Checking branch: $branch ==="
  github-mcp get_file_contents "{
    \"owner\": \"jbcom\",
    \"repo\": \"jbcom-control-center\",
    \"path\": \"path/to/file.py\",
    \"ref\": \"$branch\"
  }"
done

# Check PR status
for pr in $(cat /tmp/mentioned_prs.txt | tr -d '#'); do
  echo "=== Checking PR #$pr ==="
  gh pr view $pr --json state,commits,files
done
```

### Phase 6: Generate Recovery Plan

Based on aider's analysis and GitHub MCP verification:

```bash
cat > /tmp/recovery_plan.md << 'EOF'
# Recovery Plan for Agent $FAILED_AGENT_ID

## Work Completed ✅
- [List of files/changes that are committed and match their claims]

## Work Partial ⚠️
- [List of files that exist but differ from what they said]
- [Branches that exist with fewer commits than expected]

## Work Lost ❌
- [Files they said they created but don't exist]
- [Branches they mentioned but don't exist]
- [PRs they said they created but weren't opened]

## Recovery Actions 🔧
1. [Specific git commands to restore lost work if recoverable]
2. [Files to recreate from conversation context]
3. [PRs to open based on their intent]
4. [Tests to run to verify state]

## Conversation Excerpts
[Paste relevant messages showing what they THOUGHT they did]
EOF
```

---

## Example: Recovering from ERROR Agent

### Scenario
Agent bc-2f734412-e52c-4c56-b34d-03cf35ad67f0 shows ERROR status with minimal conversation.

### Recovery Steps

```bash
# 1. Get conversation
cursor-agents conversation bc-2f734412-e52c-4c56-b34d-03cf35ad67f0 > /tmp/error_agent.json

# 2. Check message count
jq '.messages | length' /tmp/error_agent.json
# Output: 1 (only error message)

# 3. Get status details
cursor-agents status bc-2f734412-e52c-4c56-b34d-03cf35ad67f0

# 4. Analysis
# - Created: 2025-11-27T03:02:28.132Z
# - Branch: feat/cursor-background-agent-environment
# - Status: ERROR immediately
# - Conversation: Only internal error message

# 5. Conclusion
# This agent crashed on startup before doing any work.
# Recovery: NOT NEEDED - no work was done
```

### Scenario 2: Long-Running Agent That Expired

```bash
# 1. Get conversation from finished agent for demonstration
AGENT_ID="bc-c1254c3f-ea3a-43a9-a958-13e921226f5d"
cursor-agents conversation $AGENT_ID > /tmp/long_agent.json

# 2. Extract last 10 assistant messages (what they said they did)
jq '.messages[] | 
  select(.type == "assistant_message") |
  .text' /tmp/long_agent.json | tail -10 > /tmp/agent_claims.txt

# 3. Extract file paths they mentioned
grep -oE '\S+\.(py|yml|md|toml|js|ts)' /tmp/agent_claims.txt | \
  sort -u > /tmp/files_mentioned.txt

# 4. Check if those files exist
cat /tmp/files_mentioned.txt | while read file; do
  if [ -f "$file" ]; then
    echo "✅ EXISTS: $file"
    git log --oneline -5 -- "$file"
  else
    echo "❌ MISSING: $file"
  fi
done

# 5. Use aider to analyze discrepancies
aider --message "Compare the files in /tmp/agent_claims.txt with actual repository state. 
For each file mentioned:
- Check if it exists
- Check git history
- Identify if their description matches reality
- Flag any discrepancies

Generate a recovery report." \
  --no-auto-commits \
  --yes
```

---

## Integration with Handoff Protocol

### Enhanced Handoff Checklist

When creating station-to-station handoff, include aider validation:

```bash
# Before creating handoff PR, run self-validation with aider
aider --message "Review all changes I made in this session.
Compare my conversation (cursor-agents conversation $MY_AGENT_ID) 
with actual git commits on branch $BRANCH_NAME.

Verify:
1. Every file I said I modified is actually modified
2. Every commit I mentioned exists
3. Every PR I claimed to create exists
4. No uncommitted work remains

Flag any discrepancies for handoff document." \
  --no-auto-commits \
  --yes \
  > /tmp/self_validation_report.txt

# Include this in AGENT_HANDOFF.md
cat /tmp/self_validation_report.txt >> AGENT_HANDOFF.md
```

### Pre-Merge Self-Audit

```bash
# Final check before merging
aider --message "Audit my work:
1. List all files I modified this session
2. Verify all tests pass
3. Check for any TODOs or FIXMEs I left
4. Confirm documentation is complete
5. Verify all my claims in conversation match reality

Generate GO/NO-GO recommendation for merge." \
  --no-auto-commits \
  --yes
```

---

## Aider Configuration for Agents

### Recommended `.aider.conf.yml`

```yaml
# Agent-optimized aider configuration
model: claude-opus-4-20250514
edit-format: diff
no-auto-commits: true
yes: true
dark-mode: true
show-diffs: true
attribute-author: false
attribute-committer: false
```

### Environment Variables

```bash
# In Dockerfile or .bashrc
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
export AIDER_MODEL="claude-opus-4-20250514"
export AIDER_NO_AUTO_COMMITS="true"
```

---

## CLI Wrapper: `agent-recover`

### Version 1: Direct Analysis (Quick)

For immediate analysis without launching sub-agent:

```bash
#!/bin/bash
# /workspace/.cursor/scripts/agent-recover-quick
# Quick forensic analysis without sub-agent delegation

FAILED_AGENT_ID="$1"

if [ -z "$FAILED_AGENT_ID" ]; then
  echo "Usage: agent-recover-quick <failed-agent-id>"
  exit 1
fi

echo "=== Starting Recovery for Agent: $FAILED_AGENT_ID ==="

# 1. Get conversation
cursor-agents conversation $FAILED_AGENT_ID > /tmp/failed_agent.json
MSG_COUNT=$(jq '.messages | length' /tmp/failed_agent.json)
echo "Messages: $MSG_COUNT"

if [ "$MSG_COUNT" -lt 3 ]; then
  echo "⚠️  Agent crashed immediately, no work to recover"
  exit 0
fi

# 2. Extract metadata
jq -r '.messages[0].text' /tmp/failed_agent.json > /tmp/initial_prompt.txt
jq '.messages[-10:]' /tmp/failed_agent.json > /tmp/last_messages.json

# 3. Extract files/branches/PRs mentioned
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '\S+\.(py|ts|md|yml|toml|json)' | sort -u > /tmp/files.txt
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '(feat|fix|docs)/[a-z0-9-]+' | sort -u > /tmp/branches.txt
jq -r '.messages[].text' /tmp/failed_agent.json | \
  grep -oE '#[0-9]+' | sort -u > /tmp/prs.txt

# 4. Run aider analysis
echo "=== Running Aider Forensic Analysis ==="
aider --message "FORENSIC RECOVERY

Agent $FAILED_AGENT_ID failed with $MSG_COUNT messages.

Files mentioned: $(cat /tmp/files.txt | tr '\n' ', ')
Branches mentioned: $(cat /tmp/branches.txt | tr '\n' ', ')
PRs mentioned: $(cat /tmp/prs.txt | tr '\n' ', ')

For each:
1. Check existence
2. Verify git history
3. Compare to agent's claims
4. Identify missing work

Generate recovery report with:
- ✅ Completed work
- ⚠️ Partial work
- ❌ Lost work
- 🔧 Recovery steps" \
  --no-auto-commits \
  --yes \
  > /tmp/recovery_report.txt

# 5. Display report
cat /tmp/recovery_report.txt

echo ""
echo "=== Recovery Report Saved ==="
echo "Location: /tmp/recovery_report.txt"
echo ""
echo "Next steps:"
echo "1. Review recovery report above"
echo "2. Execute recovery steps manually or with new agent"
echo "3. Update ConPort with recovery status"
```

Make it executable:
```bash
chmod +x /workspace/.cursor/scripts/agent-recover
```

---

## Best Practices

### For Current Agent (Pre-Handoff)
1. **Self-validate with aider** before creating handoff
2. **Include aider report** in handoff document
3. **Commit frequently** so recovery is easier if you crash
4. **Document intent** in commit messages (helps aider understand)

### For Next Agent (Post-Handoff)
1. **Check for handoff PR first** (clean scenario)
2. **If no handoff**, run `agent-recover <prev-agent-id>`
3. **Review aider report** before starting work
4. **Continue or recover** based on findings

### For Recovery Scenarios
1. **Don't trust agent claims blindly** - verify with aider
2. **Use git history** as source of truth
3. **Cross-reference** conversation + repository state
4. **Document gaps** for user if recovery impossible

---

## Metrics

Track recovery success rate:

```bash
# Log to ConPort
conport log_custom_data \
  category="AgentRecovery" \
  key="recovery_$(date +%s)" \
  value="{
    \"failed_agent_id\": \"$FAILED_AGENT_ID\",
    \"messages_recovered\": $MSG_COUNT,
    \"work_completed\": \"75%\",
    \"work_lost\": \"25%\",
    \"recovery_time_minutes\": 15
  }"
```

---

## Sub-Agent Delegation Patterns

### Pattern 1: Forensic Recovery Sub-Agent
```bash
# Delegate recovery to specialized agent
agent-recover-delegate bc-2f734412-e52c-4c56-b34d-03cf35ad67f0

# Monitor their progress
cursor-agents list | grep -i "forensic"

# Retrieve their report when done
cat RECOVERY_REPORT_bc-2f734412.md
```

### Pattern 2: Validation Sub-Agent
```bash
# Before creating handoff, delegate self-validation
cursor-agents create "Validate Agent bc-6886f54c Work

Review my conversation and verify:
1. Every file I modified is committed
2. Every PR I claimed to create exists
3. All tests pass
4. Documentation is complete
5. No uncommitted work remains

Generate: VALIDATION_REPORT_bc-6886f54c.md"
```

### Pattern 3: Parallel Testing Sub-Agent
```bash
# Delegate testing while you continue main work
cursor-agents create "Test PR #169 Comprehensively

1. Checkout PR #169
2. Run all tests: pytest, mypy, ruff
3. Build Docker image
4. Test MCP proxy services
5. Verify all CLI wrappers work

Generate: TEST_REPORT_PR169.md"
```

### Pattern 4: Documentation Sub-Agent
```bash
# Delegate doc updates while you code
cursor-agents create "Update Documentation for PR #169

Review changes in PR #169 and:
1. Update relevant docs/ files
2. Add examples for new features
3. Update CHANGELOG.md
4. Check for broken links
5. Ensure consistency

Commit changes to PR #169 branch."
```

### Pattern 5: Cross-Repo Sync Sub-Agent
```bash
# Delegate ecosystem coordination
cursor-agents create "Sync Package Changes Across Ecosystem

PR #169 added new MCP tooling to control-center.

Your task:
1. Identify which packages need updates
2. Create PRs in each package
3. Update dependencies
4. Test integration
5. Report back with PR links

Repositories:
- extended-data-types
- lifecyclelogging
- vendor-connectors"
```

## Benefits of Sub-Agent Delegation

### For Primary Agent (You)
- ✅ **Stay focused** on main task
- ✅ **Parallel execution** of sub-tasks
- ✅ **Delegate expertise** (recovery, testing, docs)
- ✅ **Fault isolation** - Their failures don't affect you

### For Sub-Agents
- ✅ **Clear scope** - Single responsibility
- ✅ **Specialized tools** - Use what they need (aider, etc.)
- ✅ **Time-boxed** - Finish and exit
- ✅ **Persistent output** - Create files for primary agent

### For User
- ✅ **No coordination needed** - Agents self-organize
- ✅ **Faster completion** - Parallel work
- ✅ **Better quality** - Specialized agents do better work
- ✅ **Less interruption** - Only intervene on blockers

## Future Enhancements

### Automated Sub-Agent Spawning
```bash
# Auto-detect need for recovery and spawn sub-agent
if [ "$NO_HANDOFF" = true ] && [ "$PREV_AGENT_ERROR" = true ]; then
  agent-recover-delegate $PREV_AGENT_ID --auto
fi
```

### Sub-Agent Orchestration
```yaml
# .cursor/agent-orchestra.yml
on_new_session:
  - check_for_handoff
  - if_no_handoff:
      spawn:
        - forensic_recovery_agent
        - validation_agent
  - await_reports:
      timeout: 5min
  - synthesize_findings
  - continue_primary_work

on_pre_merge:
  spawn:
    - validation_agent
    - test_agent
    - documentation_agent
  - await_all
  - if_all_pass:
      create_handoff_pr
```

### Agent Communication Protocol
```bash
# Primary agent → Sub-agent
cursor-agents followup $SUB_AGENT_ID "Check branch feat/xyz too"

# Sub-agent → Primary agent (via file)
echo "Recovery complete. 3 files lost, recovery plan in report." > \
  /workspace/.cursor/agent_messages/to_primary_$(date +%s).txt

# Primary agent reads messages
ls -t /workspace/.cursor/agent_messages/to_primary_*.txt | head -1 | xargs cat
```

---

---

## CRITICAL UPDATE: Direct Cursor API Access (2025-11-28)

### The Reality of `cursor-agents` CLI

The `cursor-agents` CLI referenced above requires:
1. MCP proxy running on port 3011
2. `process-compose` to manage services
3. Pre-configured environment

**In many environments, this infrastructure is NOT pre-configured.**

### Self-Bootstrapping Alternative

You can access the Cursor API directly WITHOUT the CLI infrastructure:

```bash
# Install mcp-proxy (one-time)
pip install mcp-proxy
export PATH="/home/ubuntu/.local/bin:$PATH"

# Use MCP protocol directly
(
  echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"agent","version":"1.0"}}}'
  sleep 2
  echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listAgents","arguments":{}}}'
  sleep 5
) | timeout 20 npx -y cursor-background-agent-mcp-server | tail -1 | jq '.result.content[0].text | fromjson'
```

### Critical Limitation Discovered

**EXPIRED agents have PURGED conversations!**

When you try to retrieve an expired agent's conversation:
```json
{"error": {"code": -32603, "message": "Cursor API error: 409 Conflict", "details": {"error": "Agent is deleted"}}}
```

**Implication**: You can only recover summaries (from `listAgents`) for expired agents. Full conversations must be archived BEFORE expiration.

### Archive Your Own Conversation

To preserve your conversation for future recovery:

```bash
export PATH="/home/ubuntu/.local/bin:$PATH"
MY_AGENT_ID="<your-agent-id>"  # Find via listAgents

(
  echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"agent","version":"1.0"}}}'
  sleep 2
  echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"getAgentConversation\",\"arguments\":{\"agentId\":\"$MY_AGENT_ID\"}}}"
  sleep 10
) | timeout 30 npx -y cursor-background-agent-mcp-server | tail -1 | jq -r '.result.content[0].text' > memory-bank/recovery/conversation-${MY_AGENT_ID}.json
```

### Environment Variables Available

These are set in your environment but undocumented:
- `CURSOR_API_KEY` - API key for Cursor services
- `CURSOR_AGENT=1` - Indicates background agent context
- `HOSTNAME=cursor` - Container hostname

See `.cursor/rules/02-cursor-api-access.mdc` for full documentation.

---

**Last Updated**: 2025-11-28  
**Status**: Active protocol (updated with direct API access patterns)  
**Dependencies**: mcp-proxy (installable), cursor-background-agent-mcp-server (via npx)
