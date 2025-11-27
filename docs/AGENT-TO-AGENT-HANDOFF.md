# Agent-to-Agent Handoff Protocol

## Overview

Background agents in this control center have the capability to **retrieve full conversation history** from previous agents, enabling seamless "station-to-station" handoffs without human intervention.

## The Living Memory Pattern

### Core Principle
Each agent becomes the **living memory** of the previous agent by:
1. Retrieving their full conversation (via `cursor-background-agent-mcp-server`)
2. Chronologically reviewing their work
3. Understanding context, decisions, and patterns
4. Continuing their work seamlessly

### Why This Matters
- ✅ **No context loss** between agent sessions
- ✅ **No human bottleneck** for handoffs
- ✅ **Living history** that agents can replay
- ✅ **Learn from success** and avoid repeating mistakes
- ✅ **Continuity** across long-running initiatives

---

## Retrieving Previous Agent Conversations

### Find Active and Recent Agents

```bash
# List all agents (running, error, finished, expired)
cursor-agents list

# Filter for specific states
cursor-agents list | jq '.agents[] | select(.status == "FINISHED")'
```

### Get Full Conversation

```bash
# Get conversation by agent ID
cursor-agents conversation bc-6886f54c-f4d9-4391-a0b9-83d112ca204a

# Get conversation stats
cursor-agents conversation bc-c1254c3f-ea3a-43a9-a958-13e921226f5d | \
  jq '{
    totalMessages: (.messages | length),
    userMessages: ([.messages[] | select(.type == "user_message")] | length),
    assistantMessages: ([.messages[] | select(.type == "assistant_message")] | length)
  }'

# Save full conversation for analysis
cursor-agents conversation bc-abc123 > /tmp/previous_agent_conversation.json
```

### Chronologically Review Work

```bash
# Extract messages in order with timestamps
jq '.messages[] | {
  type,
  text: .text[0:200],
  id
}' /tmp/previous_agent_conversation.json | less

# Filter for user instructions only
jq '.messages[] | select(.type == "user_message") | .text' \
  /tmp/previous_agent_conversation.json
```

---

## Station-to-Station Handoff Protocol

### When to Initiate Handoff

Handoff should be initiated when:
- ✅ Your work is substantially complete
- ✅ All documentation is updated
- ✅ GitHub issues/projects are current
- ✅ ConPort memory is reconciled
- ✅ CI/CD is green
- ✅ Ready for next phase of work

### Pre-Handoff Checklist

Before creating handoff PR, ensure:

#### 1. Documentation is Complete
- [ ] All new features documented
- [ ] Architecture decisions recorded
- [ ] API changes documented
- [ ] Examples provided
- [ ] README updated

#### 2. Code is Clean
- [ ] No commented-out code
- [ ] No TODOs left unaddressed
- [ ] Linting passes
- [ ] Tests pass
- [ ] Type checking passes

#### 3. GitHub is Current
- [ ] All issues updated
- [ ] Projects reflect current state
- [ ] PRs have clear descriptions
- [ ] Related PRs linked

#### 4. Memory is Reconciled
- [ ] ConPort active context updated
- [ ] Decisions logged
- [ ] Progress tracked
- [ ] Patterns documented

#### 5. Handoff Materials Ready
- [ ] Summary of work completed
- [ ] Open issues/blockers identified
- [ ] Next steps clearly defined
- [ ] Links to all relevant docs/PRs
- [ ] Context for any in-progress work

---

## Creating the Handoff PR

### Step 1: Create Hold-Open Branch

```bash
# Create branch that will stay open for next agent
git checkout main
git pull
git checkout -b handoff/agent-$(date +%Y%m%d-%H%M)-to-next

# Create handoff document
cat > AGENT_HANDOFF.md << 'EOF'
# Agent Handoff: [AGENT_ID] → Next Agent

**From**: Agent bc-6886f54c-f4d9-4391-a0b9-83d112ca204a
**Date**: YYYY-MM-DD
**Duration**: X hours/days
**Status**: Ready for handoff

## Summary of Work Completed
[Bullet points of major accomplishments]

## Current State
[Description of where things are now]

## Open Issues/Blockers
[Any unresolved items]

## Next Steps
[Clear action items for next agent]

## Key Documentation
- [Link to doc 1]
- [Link to doc 2]

## Related PRs
- #123 - Description
- #124 - Description

## ConPort State
- Active Context: [Summary]
- Recent Decisions: [Links]
- Open Issues: [Count]

## How to Continue My Work
1. Read this handoff document
2. Review my conversation: `cursor-agents conversation bc-abc123`
3. Check ConPort memory: [instructions]
4. Continue with [specific next steps]

---

**@cursor** - Next background agent, this is your starting point.
EOF

git add AGENT_HANDOFF.md
git commit -m "docs: Agent handoff preparation"
git push -u origin handoff/agent-$(date +%Y%m%d-%H%M)-to-next
```

### Step 2: Create Handoff PR

```bash
gh pr create \
  --title "🔄 Agent Handoff: [Your Task Name]" \
  --body "$(cat << 'BODY'
## Station-to-Station Handoff

This PR is a **hold-open handoff** from the current background agent to the next.

### Purpose
- Provides complete context for next agent
- Documents all work completed
- Identifies next steps
- Ensures no gaps in continuity

### For Next Agent
1. **Read**: `AGENT_HANDOFF.md` in this PR
2. **Review**: My full conversation via `cursor-agents conversation [MY_ID]`
3. **Check**: ConPort memory state
4. **Continue**: Following the next steps outlined

### Current Agent Info
- **ID**: bc-6886f54c-f4d9-4391-a0b9-83d112ca204a
- **Task**: [Task description]
- **Branch**: [Current branch]
- **Status**: Work complete, ready for handoff

---

**@cursor** - This is your comprehensive handoff. Everything you need is linked above.

**DO NOT MERGE THIS PR** - It's a reference point for next agent.
BODY
)" \
  --label "handoff" \
  --label "documentation"
```

### Step 3: Final Merge and Closeout

ONLY after handoff PR is created:

```bash
# Merge your actual work PR
gh pr merge [WORK_PR_NUMBER] --squash --delete-branch

# Update handoff PR with final state
gh pr comment [HANDOFF_PR_NUMBER] --body "✅ Work PR merged. Handoff complete."

# Session will close automatically after final merge
```

---

## For Next Agent: How to Pick Up

### Step 1: Find Previous Agent

```bash
# List recent finished agents on this repo
cursor-agents repos | grep jbcom/jbcom-control-center

cursor-agents list | jq '.agents[] | 
  select(.source.repository == "github.com/jbcom/jbcom-control-center") |
  select(.status == "FINISHED") |
  {id, name, branch: .target.branchName, prUrl: .target.prUrl}' | head -5
```

### Step 2: Retrieve Full Context

```bash
# Get their conversation
PREV_AGENT_ID="bc-6886f54c-f4d9-4391-a0b9-83d112ca204a"
cursor-agents conversation $PREV_AGENT_ID > /tmp/previous_agent.json

# Review chronologically
jq '.messages[] | {
  type,
  preview: .text[0:300]
}' /tmp/previous_agent.json | less
```

### Step 3: Check for Handoff PR

```bash
# Look for handoff PR
gh pr list --label handoff --state open

# Read the handoff document
gh pr view [HANDOFF_PR] --json body | jq -r '.body'
```

### Step 4: Load ConPort Memory

```bash
# Check previous agent's context
conport get_active_context

# Review their decisions
conport search_decisions --limit 10

# Check progress
conport get_progress --status IN_PROGRESS
```

### Step 5: Continue Work

Now you have:
- ✅ Full conversation history (what they did)
- ✅ Handoff document (what they recommend)
- ✅ ConPort memory (decisions and context)
- ✅ GitHub state (PRs, issues, projects)

**You are now the living memory of the previous agent.**

---

## Example: Learning from Previous Agent

### Case Study: Agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d

**Task**: "Fix all ci/cd issues and improve release process"
**Messages**: 287 total (43 user, 244 assistant)
**Status**: FINISHED

**What This Agent Taught Me:**
1. **Hold-open PR pattern** for long-running work
2. **Interim PRs** for fixes while keeping main session alive
3. **CalVer versioning** across monorepo
4. **Secrets sync** via SOPS + JavaScript action
5. **SSH → HTTPS** authentication transitions

**Key Quote from User:**
> "You need to FIRST open ONE PR THEN go back to main and open ANOTHER where you get your actual work done or else you'll end up MERGING the PR you were doing your FIXES in and then you won't be able to WORK more because your background agent will close out."

**Lesson Applied:**
This is WHY we create handoff PRs BEFORE merging final work.

---

## Anti-Patterns (What NOT to Do)

### ❌ Bad Handoff
- Merging work PR without creating handoff
- No documentation of current state
- Assuming user will brief next agent
- Leaving TODOs without context
- No clear next steps

### ✅ Good Handoff
- Handoff PR created BEFORE final merge
- Comprehensive documentation
- Clear next steps
- All context linked
- ConPort memory current
- GitHub state clean

---

## Metrics for Successful Handoff

A successful handoff means the next agent can:
- [ ] Understand what was done and why
- [ ] Continue work without asking basic questions
- [ ] Access all relevant context
- [ ] Know what's complete vs in-progress
- [ ] Identify blockers and workarounds
- [ ] Execute next steps immediately

---

## Future Improvements

### Automated Handoff Generation
```bash
# Future: AI-generated handoff from conversation
cursor-agents generate-handoff bc-abc123 > AGENT_HANDOFF.md
```

### Conversation Search
```bash
# Future: Search across agent conversations
cursor-agents search "secrets sync pattern" --across-agents
```

### Handoff Templates
- Standard handoff checklist
- Auto-populated from conversation
- ConPort integration
- GitHub project sync

---

**Last Updated**: 2025-11-27
**Status**: Active protocol
**Next Review**: After 5 successful handoffs
