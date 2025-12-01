# Agent-to-Agent Handoff Protocol

## Overview

This protocol enables seamless station-to-station handoffs between background agents, ensuring:
- No context loss between sessions
- No human bottleneck for handoffs
- Living memory across agent sessions
- Continuity across long-running initiatives

## The Living Memory Pattern

Each agent becomes the **living memory** of the previous agent by:
1. Reviewing memory bank files
2. Understanding current context and decisions
3. Continuing work without re-briefing

## Memory Bank Structure

```
memory-bank/
├── activeContext.md     # Current focus and state
├── progress.md          # Session-by-session progress log
├── projectbrief.md      # Project overview (rarely changes)
├── systemPatterns.md    # Architecture patterns
└── techContext.md       # Technical details
```

### activeContext.md

**Update at**: Start and end of every session

```markdown
# Active Context

## Current Status: <STATUS>

### Focus
<what you're working on>

### Recent Changes
- <change 1>
- <change 2>

### Blocking Issues
- <blocker if any>

### For Next Agent
<specific instructions>

### jbcom Coordination State
- Last sync: <date>
- Pending items: <list>
```

### progress.md

**Update at**: End of every session

```markdown
## Session: YYYY-MM-DD

### Agent ID
<agent-id if known>

### Completed
- [x] Task 1
- [x] Task 2

### In Progress
- [ ] Task 3 (at step X)

### Blocked
- Task 4: <reason>

### Decisions Made
- Decision 1: <rationale>

### Next Steps
1. <step 1>
2. <step 2>
```

## Pre-Handoff Checklist

Before ending your session, verify:

### 1. Documentation Complete
- [ ] activeContext.md updated
- [ ] progress.md updated
- [ ] New decisions documented
- [ ] README updated if needed

### 2. Code is Clean
- [ ] No uncommitted changes
- [ ] No broken CI
- [ ] Linting passes
- [ ] Tests pass

### 3. GitHub State Clean
- [ ] Open PRs have clear status
- [ ] Issues updated
- [ ] Labels current

### 4. Memory Reconciled
- [ ] Active context reflects reality
- [ ] Progress log current
- [ ] Decisions logged

### 5. Handoff Materials Ready
- [ ] Summary of work done
- [ ] Open items identified
- [ ] Next steps clear
- [ ] All links documented

## Creating Handoff

### Quick Handoff (Same Day)

For short sessions:

```bash
# Update memory bank
cat >> memory-bank/progress.md << 'EOF'

## Session: $(date +%Y-%m-%d %H:%M)

### Completed
- [x] <what you did>

### For Next Agent
<instructions>
EOF

# Update active context
cat > memory-bank/activeContext.md << 'EOF'
# Active Context

## Current Status: <status>

<current state description>

## For Next Agent
<specific instructions>
EOF

# Commit
git add memory-bank/
git commit -m "docs: update memory bank for handoff"
git push
```

### Full Handoff (End of Major Work)

For significant work completion:

```bash
# 1. Create AGENT_HANDOFF.md
cat > AGENT_HANDOFF.md << 'EOF'
# Agent Handoff: <agent-id> → Next Agent

**Date**: $(date +%Y-%m-%d)
**Task**: <task description>
**Duration**: <X hours>
**Status**: ✅ Ready for handoff

---

## Summary of Work Completed

### Major Accomplishments
- <accomplishment 1>
- <accomplishment 2>

### Files Changed
- `path/to/file1`: <description>
- `path/to/file2`: <description>

### PRs Created/Updated
- #X: <description> - <status>

### Issues Resolved
- #Y: <description>

---

## Current State

### Repository State
- Branch: <current branch>
- CI Status: <passing/failing>
- Open PRs: <count>

### jbcom Coordination
- Last sync: <date>
- Pending updates: <list>
- Open handoffs: <list>

---

## Open Items / Blockers

### In Progress
- [ ] <item 1> - at step X
- [ ] <item 2> - awaiting Y

### Blocked
- <blocker 1>: <reason>

---

## Next Steps for Next Agent

### Immediate (Do First)
1. <step 1>
2. <step 2>

### Short Term (This Week)
1. <step 3>
2. <step 4>

### Background (When Time Permits)
- <background task>

---

## Key Documentation

- [AGENTS.md](.ruler/AGENTS.md) - Agent instructions
- [COUNTERPARTY-COORDINATION.md](docs/COUNTERPARTY-COORDINATION.md) - jbcom coordination
- [memory-bank/activeContext.md](memory-bank/activeContext.md) - Current state

---

## How to Continue My Work

1. **Read this handoff** - You're doing it now ✅
2. **Check memory bank** - `cat memory-bank/activeContext.md`
3. **Review open PRs** - `gh pr list --state open`
4. **Check CI status** - `gh run list --limit 5`
5. **Start next task** - See "Next Steps" above

---

@cursor - Next background agent, start here. Everything you need is documented above.

**Handoff Protocol Version**: 1.0
**Status**: ✅ Complete
EOF

# 2. Update memory bank
cat > memory-bank/activeContext.md << 'EOF'
# Active Context

## Current Status: HANDOFF COMPLETE

See AGENT_HANDOFF.md for full context.

## For Next Agent
1. Read AGENT_HANDOFF.md
2. Follow "Next Steps" section
3. Update this file when you begin
EOF

# 3. Commit and push
git add AGENT_HANDOFF.md memory-bank/
git commit -m "docs: create comprehensive agent handoff

Work completed: <summary>
Next steps: <summary>
See AGENT_HANDOFF.md for full details."
git push
```

## Receiving Handoff

### Finding Previous Context

```bash
# 1. Check for handoff document
if [ -f "AGENT_HANDOFF.md" ]; then
  cat AGENT_HANDOFF.md
fi

# 2. Review memory bank
cat memory-bank/activeContext.md
cat memory-bank/progress.md

# 3. Check recent git history
git log --oneline -20

# 4. Check open PRs
gh pr list --state open

# 5. Check open issues
gh issue list --state open
```

### Starting Your Session

```bash
# 1. Update active context to show you're active
cat > memory-bank/activeContext.md << 'EOF'
# Active Context

## Current Status: IN PROGRESS

**Session Started**: $(date +%Y-%m-%d %H:%M)
**Picking up from**: <previous handoff summary>

## Current Focus
<what you're working on>

## Plan
1. <first task>
2. <second task>
EOF

# 2. Commit your start
git add memory-bank/activeContext.md
git commit -m "docs: begin new session, picking up from previous handoff"

# 3. Begin work
```

## Cross-Control-Center Handoff

### Handing Off to jbcom

When work requires jbcom control center:

```bash
# 1. Document in FSC
cat >> memory-bank/activeContext.md << 'EOF'

## Handoff to jbcom Control Center
**Date**: $(date +%Y-%m-%d)
**Reason**: <reason>
**jbcom Issue/PR**: <to be created>
**Expected Return**: <timeframe>
EOF

# 2. Create jbcom issue
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create \
  --repo jbcom/jbcom-control-center \
  --title "🔄 Handoff from FSC: <task>" \
  --body "## Station-to-Station Handoff

**From**: FSC Control Center
**Repository**: FlipsideCrypto/fsc-control-center
**Date**: $(date +%Y-%m-%d)

## Context
<full context from FSC side>

## Requested Action
<what jbcom agent should do>

## Return Protocol
After completion:
1. Comment on this issue with results
2. FSC agent will detect and continue

---
*Station-to-station handoff*
*FSC Control Center → jbcom Control Center*"

# 3. Track locally
gh issue create \
  --title "🔗 Tracking jbcom handoff: <task>" \
  --body "Tracking jbcom/jbcom-control-center#<issue_number>"
```

### Receiving from jbcom

When jbcom hands off to FSC:

```bash
# 1. Check for jbcom handoffs
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list \
  --repo jbcom/jbcom-control-center \
  --search "Handoff to FSC in:title"

# 2. Review the handoff
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue view <NUM> \
  --repo jbcom/jbcom-control-center

# 3. Acknowledge receipt
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue comment <NUM> \
  --repo jbcom/jbcom-control-center \
  --body "✅ Received by FSC Control Center. Beginning work."

# 4. Document locally
cat >> memory-bank/activeContext.md << 'EOF'

## Received Handoff from jbcom
**Date**: $(date +%Y-%m-%d)
**jbcom Issue**: #<NUM>
**Task**: <description>
EOF
```

## Lessons Learned Log

Document learnings for future agents:

```markdown
## Lessons (Add to progress.md)

### Session: YYYY-MM-DD

**What Worked**:
- <pattern that worked>

**What Didn't Work**:
- <pattern to avoid>

**Key Learning**:
- <insight for future agents>
```

## Anti-Patterns

### ❌ Bad Handoff
- No documentation of current state
- Assuming user will brief next agent
- Leaving TODOs without context
- No clear next steps
- Uncommitted changes

### ✅ Good Handoff
- Memory bank updated
- Comprehensive handoff document (for major work)
- Clear next steps
- All context documented
- GitHub state clean

## Success Criteria

A successful handoff means the next agent can:
- [ ] Understand what was done and why
- [ ] Continue without basic questions
- [ ] Access all relevant context
- [ ] Know complete vs in-progress items
- [ ] Identify blockers and workarounds
- [ ] Execute next steps immediately

---

**Last Updated**: 2025-11-28  
**Protocol Version**: 1.0
