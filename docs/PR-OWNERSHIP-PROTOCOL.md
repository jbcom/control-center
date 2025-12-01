# PR Ownership and AI-to-AI Collaboration Protocol

## Core Principle: First Agent Owns the PR

When you are the **first AI agent** to engage with a pull request (creating, reviewing, or responding), you become the **PR OWNER** with full responsibility until merge or close.

## PR Owner Responsibilities

### 1. Full Lifecycle Ownership

As PR owner, you handle:
- ✅ **All feedback**: From humans AND other AI agents
- ✅ **All CI failures**: Fix lint, test, and build issues
- ✅ **All requested changes**: Implement feedback from any source
- ✅ **Collaboration**: Engage directly with AI reviewers
- ✅ **Final merge**: Execute when ready

**User involvement only when**:
- Decision requires product/business judgment
- Hard blocker you cannot resolve
- Explicit approval needed for breaking changes

### 2. Recognizing Ownership

**You are the PR owner if you:**
- Created the PR
- Are the first agent to respond to feedback
- Are explicitly tagged as owner
- Are continuing work from a previous session

**Check ownership:**
```bash
gh pr view <NUM> --json author,comments,reviews
```

## AI-to-AI Collaboration

### Identifying AI Agents

Common AI reviewers:
- **@gemini-code-assist[bot]** - Google Gemini
- **@copilot** - GitHub Copilot
- **@amazon-q[bot]** - Amazon Q
- **Other Cursor agents** - May appear as author or commenter

### Engaging with AI Feedback

#### Step 1: Parse and Categorize

```markdown
Agent: @gemini-code-assist
Priority: HIGH
Issue: "Security vulnerability in X"
Type: Security
Actionable: YES
```

#### Step 2: Evaluate Against Project Rules

- Check if feedback contradicts `.ruler/AGENTS.md`
- Security issues → ALWAYS address
- Style preferences → Defer to project config (ruff, etc.)

#### Step 3: Respond Directly

**Accepting feedback:**
```markdown
@gemini-code-assist Thank you for the security review. I've addressed your concern:

✅ Fixed: <description>
✅ Committed: <commit-hash>

Please verify the fix addresses your concern.
```

**Declining feedback:**
```markdown
@gemini-code-assist Thank you for the suggestion. However, this conflicts with our project approach:

**Our approach**: <description>
**Why**: <rationale>
**Reference**: See `.ruler/AGENTS.md`

Happy to discuss if you see issues with this approach.
```

**Requesting clarification:**
```markdown
@gemini-code-assist Could you clarify your suggestion about X?

Current approach:
- <current implementation>

Your suggestion seems to imply Y. Before proceeding, I'd like to understand:
1. <question 1>
2. <question 2>

Would appreciate your thoughts.
```

#### Step 4: Implement Valid Feedback

**Security issues (HIGH/CRITICAL)**:
- Fix immediately
- Commit: `security: fix <issue> (addresses @agent feedback)`
- Tag agent in response
- Don't block on re-review if urgent

**Code quality (MEDIUM)**:
- Evaluate against project standards
- Implement if improves code
- Decline with explanation if conflicts

**Nitpicks (LOW)**:
- Batch with other changes
- Or acknowledge and defer
- Don't block PR on nitpicks

#### Step 5: Mark Resolved

```bash
# Comment when resolved
gh pr comment <NUM> --body "✅ Resolved: <brief description>"
```

## Handling Conflicting AI Feedback

### Priority Order

1. **Project rules** (`.ruler/AGENTS.md`) - ALWAYS highest
2. **Security concerns** - Always address
3. **Performance issues** - Evaluate with evidence
4. **Style preferences** - Defer to project config
5. **Subjective opinions** - Use judgment, explain choice

### Resolving Conflicts

When Agent A says "use X" and Agent B says "use Y":

```markdown
@agent-a @agent-b Thank you both for the feedback. I see conflicting recommendations:

- @agent-a suggests: Approach X for reason R1
- @agent-b suggests: Approach Y for reason R2

Based on project requirements:
- We need: <specific requirement>
- Constraint: <specific constraint>

I'm choosing **approach X** because:
1. Aligns with project rule in `.ruler/AGENTS.md`
2. Consistent with existing patterns
3. <additional reason>

@agent-b While approach Y has merit, our project context prioritizes R1.

Both agents, please let me know if you see issues with this reasoning.
```

## PR Lifecycle

### Creating a PR

```bash
gh pr create \
  --title "feat: <description>" \
  --body "## Summary
<description>

## Changes
- <change 1>
- <change 2>

## Testing
- <test approach>

## AI Agent Notes
🤖 **PR Owner**: @cursor (Background Agent)
🤖 **Status**: Ready for AI review
🤖 **Request**: @gemini-code-assist please review

## Checklist
- [x] Tests pass
- [x] Lint passes
- [x] Documentation updated"
```

### Monitoring Status

**Daily check (if PR > 24h):**
```bash
# Check for new feedback
gh pr view <NUM> --comments

# Check CI status
gh pr checks <NUM>

# Check reviews
gh pr reviews <NUM>
```

**Response time**: < 24h for any feedback

### Merging

```bash
# Final verification
gh pr checks <NUM>  # All green?

# Merge
gh pr merge <NUM> --squash --delete-branch

# Post-merge verification
gh run list --limit 3  # CI release success?
```

## Cross-Control-Center PRs

### PRs in jbcom Repos

When creating PRs in jbcom:

```bash
# Always use jbcom token
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create \
  --repo jbcom/jbcom-control-center \
  --title "feat(edt): <description>" \
  --body "## Summary
<description>

## From FSC Control Center
This addresses a need identified in FlipsideCrypto infrastructure.

## Test Plan
- [ ] Tests pass
- [ ] Lint passes (ruff)
- [ ] Type check passes (mypy)

---
*Contributed by FSC Control Center background agent*"

# Monitor with jbcom token
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr view <NUM> --repo jbcom/jbcom-control-center
```

### Following jbcom Conventions

When contributing to jbcom, follow their conventions:
- **Commits**: Conventional format with scopes (edt, logging, dic, connectors)
- **Versioning**: CalVer-compatible (YYYYMM.MINOR.PATCH)
- **PR ownership**: jbcom may have their own AI agents reviewing

## Handoff Protocol

### To Another Agent

```markdown
🤖 **PR HANDOFF**

@cursor-agent-v2 Taking over this PR due to <reason>

**Status:**
- ✅ Completed: <items>
- ⏳ In Progress: <items>
- ❌ Blocked: <items>

**Outstanding feedback:**
- @gemini-code-assist: Waiting for re-review
- @copilot: Clarification requested

**Next actions:**
1. <action 1>
2. <action 2>

You are now PR owner. Please acknowledge.
```

### To Human

```markdown
🤖 **HUMAN INTERVENTION REQUIRED**

@user This PR requires your decision on:
<specific question or blocker>

**Context:**
<relevant context>

**Options:**
1. <option 1>: <pros/cons>
2. <option 2>: <pros/cons>

AI agents have reached the limit of autonomous decision-making.
Please provide direction, and I'll execute.
```

## Metrics

Track PR ownership effectiveness:
- ⏱️ **Response time**: < 24h to feedback
- 🎯 **Resolution rate**: > 90% feedback addressed
- 🤝 **Collaboration**: Engage with every AI comment
- 🚀 **Merge time**: < 7 days creation to merge
- ✅ **CI success**: > 95% pass rate

## Anti-Patterns

❌ **Ignoring AI feedback** - Always respond, even if declining
❌ **Escalating AI conflicts to user** - Resolve yourself
❌ **Merging with unresolved feedback** - Address or explicitly defer
❌ **Silent fixes** - Tag agent when fixing their concern
❌ **Defensive responses** - Be collaborative
❌ **Abandoning PRs** - Hand off or close if blocked

---

**Last Updated**: 2025-11-28  
**Status**: Active Protocol
