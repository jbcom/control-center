# PR Ownership and AI-to-AI Collaboration

**THIS IS A CRITICAL WORKFLOW RULE - READ FIRST WHEN ENGAGING WITH PULL REQUESTS**

## Core Principle: First Agent Owns the PR

When you are the **first AI agent** to engage with a pull request (whether creating it, reviewing it, or responding to feedback), you are the **PR OWNER** and have full responsibility for that PR until it's merged or closed.

## PR Owner Responsibilities

### 1. Full Lifecycle Ownership

As PR owner, you are responsible for:
- ✅ **All feedback**: Address every comment from humans AND other AI agents
- ✅ **All CI failures**: Fix lint, test, and build issues
- ✅ **All requested changes**: Implement feedback from any source
- ✅ **Collaboration**: Engage directly with other AI agents for reviews
- ✅ **Final merge**: Execute the merge when ready (or explicitly hand off)

**User should NOT be involved** unless:
- A decision requires product/business judgment
- There's a hard blocker you cannot resolve
- Explicit approval is needed for breaking changes

### 2. Recognizing PR Ownership

**You are the PR owner if you:**
- Created the PR (via background agent or interactive session)
- Are the first agent to respond to PR feedback
- Are explicitly tagged as owner in PR description
- Are continuing work from a previous session (check PR author)

**Check PR ownership:**
```bash
gh pr view <NUM> --json author,comments,reviews
```

If you're the author or first AI responder → **You own it**

## AI-to-AI Collaboration Protocol

### Identifying Other AI Agents

Common AI agents in PR reviews:
- **@gemini-code-assist[bot]** - Google's Gemini Code Assist
- **@copilot** - GitHub Copilot
- **@chatgpt-codex-connector[bot]** - ChatGPT/Codex
- **Other Cursor agents** - May appear as PR author or commenter
- **Automated bots** - Dependabot, security scanners, etc.

### Engaging With AI Agent Feedback

When another AI agent leaves feedback on YOUR PR:

#### Step 1: Parse and Categorize
```markdown
Agent: @gemini-code-assist
Priority: HIGH
Issue: "Curl-to-shell is security risk"
Type: Security vulnerability
Actionable: YES
```

#### Step 2: Evaluate Against Project Rules
- Check if feedback contradicts project rules (`.cursor/rules/*.mdc`)
- Our python-semantic-release SemVer workflow is intentional → politely decline manual versioning suggestions
- Security issues → ALWAYS address, no exceptions
- Style preferences → defer to our ruff configuration

#### Step 3: Respond Directly (AI-to-AI)

**Template for accepting feedback:**
```markdown
@gemini-code-assist Thank you for the security review. I've addressed your HIGH priority concern:

✅ Replaced curl-to-shell with versioned binary download
✅ Pinned process-compose to v1.27.0
✅ Download from official GitHub releases

Changes committed in <commit-hash>. Please verify the fix addresses your concern.
```

**Template for declining feedback:**
```markdown
@gemini-code-assist Thank you for the suggestion to bump versions manually. 

However, this project uses automated versioning through CI/CD. Manual version changes are not needed.

Our approach:
- ✅ SemVer via python-semantic-release
- ✅ Version detection from scoped conventional commits
- ✅ Auto-release on every main push
- ✅ Battle-tested in production

See the project's cursor rules for more details.
```

**Template for requesting clarification:**
```markdown
@gemini-code-assist Could you clarify your suggestion about "moving install-deps into the main apt layer"?

Current approach:
- apt-get install (line 9): Base system packages
- playwright install-deps (line 146): Playwright-specific deps

Are you suggesting we run `playwright install-deps --dry-run` to extract the dependency list and add them to line 9?

If so, I'm concerned about:
1. Maintenance burden (Playwright deps change between versions)
2. Layer cache invalidation (apt layer would rebuild on Playwright version bump)

Would appreciate your thoughts before proceeding.
```

#### Step 4: Implement Valid Feedback

**For security issues** (HIGH/CRITICAL):
- Fix immediately
- Commit with clear message: `security: fix <issue> (addresses @agent feedback)`
- Verify fix resolves the concern
- Tag the agent in commit comment

**For code quality** (MEDIUM):
- Evaluate against project standards
- Implement if it improves code
- Politely decline if it conflicts with our patterns
- Explain reasoning

**For nitpicks** (LOW):
- Batch with other changes
- Or acknowledge but defer to future PR
- Don't block PR merge on nitpicks

#### Step 5: Mark Resolved

After addressing feedback:
```bash
# GitHub CLI to resolve conversation (if you have permissions)
gh pr comment <NUM> --body "✅ Resolved: <brief description>"

# Or in commit message
git commit -m "fix: address @gemini-code-assist feedback on security

- Replace curl-to-shell with versioned binary
- Pin process-compose to v1.27.0

Resolves feedback from @gemini-code-assist in PR review."
```

### Proactive AI Agent Engagement

**Before merging**, actively seek AI review:

```bash
# Trigger Gemini review
gh pr comment <NUM> --body "@gemini-code-assist review"

# Request specific review
gh pr comment <NUM> --body "@gemini-code-assist Please review the security changes in .cursor/Dockerfile"

# Tag multiple agents
gh pr comment <NUM> --body "@copilot @gemini-code-assist This PR updates Docker environment. Please review for best practices."
```

## Handling Conflicting AI Feedback

When multiple AI agents give conflicting advice:

### Priority Order
1. **Project rules** (`.cursor/rules/*.mdc`) - ALWAYS highest priority
2. **Security concerns** - Always address, regardless of source
3. **Performance issues** - Evaluate based on profiling/evidence
4. **Style preferences** - Defer to ruff/mypy/project config
5. **Subjective opinions** - Use judgment, explain choice

### Resolving Conflicts

**Example: Agent A says "use X", Agent B says "use Y"**

```markdown
@agent-a @agent-b Thank you both for the feedback. I see conflicting recommendations:

- @agent-a suggests: Use approach X for reason R1
- @agent-b suggests: Use approach Y for reason R2

Based on project requirements:
- We need: <specific requirement>
- Constraint: <specific constraint>

I'm choosing **approach X** because:
1. Aligns with project rules in `.cursor/rules/`
2. Consistent with existing pattern in <file>
3. Better performance characteristics for our use case

@agent-b While approach Y has merit for R2, our project context prioritizes R1.

Both agents, please let me know if you see issues with this reasoning.
```

## PR Lifecycle Management

### Creating a PR

When you create a PR:

```bash
# Create with clear ownership signal
gh pr create \
  --title "feat: <description>" \
  --body "$(cat <<'EOF'
## Summary
<description>

## Changes
- <change 1>
- <change 2>

## Testing
- <test approach>

## AI Agent Notes
🤖 **PR Owner**: @cursor (Background Agent)
🤖 **Status**: Ready for AI review
🤖 **Request**: @gemini-code-assist @copilot please review

## Checklist
- [x] Tests pass
- [x] Lint checks pass
- [x] Documentation updated
- [x] Follows project standards
EOF
)"
```

### Monitoring PR Status

**Daily check** (if PR open > 24h):
```bash
# Check for new feedback
gh pr view <NUM> --comments

# Check CI status
gh pr checks <NUM>

# Check reviews
gh pr reviews <NUM>
```

**Respond to feedback within 24 hours** of it being posted.

### Merging the PR

When all feedback addressed and CI passes:

```bash
# Final verification
gh pr checks <NUM>  # All green?
gh pr reviews <NUM>  # All approved or acknowledged?

# Merge
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch --auto
```

**Post-merge:**
- Verify CI release succeeds (if main branch)
- Close related issues
- Update ConPort with decision logs

## Examples

### Example 1: Security Fix from Gemini

**Scenario**: Gemini flags HIGH priority security issue

```markdown
AGENT ACTION LOG:
1. Parse feedback: "curl-to-shell is security risk"
2. Severity: HIGH → immediate action required
3. Research: Find official binary download method
4. Implement: Replace with versioned download
5. Verify: Check binary verification possible
6. Commit: "security: replace curl-to-shell with versioned binary"
7. Respond: "@gemini-code-assist Fixed in <commit>. Please verify."
8. Wait: 4 hours for re-review
9. If no response: Tag again "@gemini-code-assist Could you re-review the security fix?"
10. If approved or no response after 24h: Proceed to merge
```

### Example 2: Style Preference from Copilot

**Scenario**: Copilot suggests different comment format

```markdown
AGENT ACTION LOG:
1. Parse feedback: "Consider clarifying comment..."
2. Severity: LOW (nitpick)
3. Evaluate: Does it improve clarity? YES
4. Check: Conflicts with project rules? NO
5. Implement: Update comment
6. Commit: "docs: clarify comment per @copilot feedback"
7. Respond: "@copilot Updated. Better?"
8. Continue: Don't block PR on response
```

### Example 3: Conflicting Feedback

**Scenario**: Gemini wants dependencies in apt layer, you're concerned about maintenance

```markdown
AGENT ACTION LOG:
1. Parse feedback: "Move playwright deps to apt layer"
2. Severity: MEDIUM (optimization)
3. Evaluate: Pros/cons analysis
4. Concern: Maintenance burden, cache invalidation
5. Respond: Ask for clarification (see template above)
6. Wait: 12 hours for response
7. If no response: Document decision, proceed with current approach
8. Commit: "docs: add comment explaining playwright deps layer choice"
9. Explain: In commit message or PR comment
```

### Example 4: Rule Violation Suggestion

**Scenario**: Agent suggests manual version bumps (contradicts our PSR SemVer workflow)

```markdown
AGENT ACTION LOG:
1. Parse feedback: "Add semantic-release"
2. Check rules: Project uses automated versioning via CI/CD
3. Severity: N/A (contradicts project rules)
4. Respond: Politely decline with explanation (see template above)
5. Reference: Link to specific documentation
6. Educate: Help agent understand project context
7. No implementation: Don't implement contradictory suggestions
8. Move on: Continue with PR
```

## Handoff Protocol

If you need to hand off PR ownership:

### To Another Agent
```markdown
🤖 **PR HANDOFF**

@cursor-agent-v2 Taking over this PR due to <reason>

Status:
- ✅ Completed: <items>
- ⏳ In Progress: <items>
- ❌ Blocked: <items>

Outstanding feedback:
- @gemini-code-assist: Waiting for re-review on security fix
- @copilot: Clarification requested, awaiting response

Next actions:
1. <next action>
2. <next action>

You are now PR owner. Please acknowledge.
```

### To Human
```markdown
🤖 **HUMAN INTERVENTION REQUIRED**

@user This PR requires your decision on:
<specific question or blocker>

Context:
<relevant context>

Options:
1. <option 1>: <pros/cons>
2. <option 2>: <pros/cons>

AI agents have reached the limit of autonomous decision-making here.
Please provide direction, and I'll execute.
```

## Metrics & Accountability

Track your PR ownership:
- ⏱️ **Response time**: < 24h to any feedback
- 🎯 **Resolution rate**: > 90% of feedback addressed
- 🤝 **Collaboration**: Engage with every AI agent comment
- 🚀 **Merge time**: < 7 days from creation to merge
- ✅ **CI success**: > 95% CI pass rate

## Anti-Patterns (DON'T Do This)

❌ **Ignoring AI agent feedback**
- Even if you disagree, always respond and explain

❌ **Asking user to resolve AI conflicts**
- Handle AI-to-AI disagreements yourself

❌ **Merging with unresolved feedback**
- Address or explicitly defer each comment

❌ **Silent fixes without communication**
- Always tag the agent when fixing their concern

❌ **Defensive responses**
- Be collaborative, not defensive with AI agents

❌ **Abandoning PRs**
- If blocked, explicitly hand off or close

## Special Cases

### Dependabot PRs
- NOT your responsibility unless you created/modified
- Can assist if requested by user

### Security Alerts
- High priority, immediate action
- Ownership: First agent to respond

### User-Created PRs
- You're a collaborator, not owner
- Unless user explicitly hands off: "@cursor take over this PR"

### Draft PRs
- Ownership rules still apply
- Can be more experimental
- Still respond to feedback

## Summary

As the first agent on a PR:
1. **Own it completely** - All feedback, all issues, all decisions
2. **Collaborate actively** - Engage with every AI agent
3. **Free the user** - Handle everything that doesn't need human judgment
4. **Be responsive** - 24h turnaround on feedback
5. **Communicate clearly** - Tag agents, explain decisions, document choices
6. **Ship it** - Merge when ready, or hand off explicitly

**The user should only be involved when you truly need them.**

---

**Version**: 1.0.0
**Last Updated**: 2025-11-27
**Status**: ACTIVE RULE - Applies to ALL PRs
