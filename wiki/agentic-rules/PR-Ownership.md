# PR Ownership Protocol

> **First agent on PR = PR Owner** with full responsibility until merge.

## You Own the PR If

- You created the PR
- You're the first agent to respond to PR feedback
- You're continuing work from a previous session

## Responsibilities

1. **Address ALL feedback** - Human AND AI agents (@gemini-code-assist, @copilot, etc.)
2. **Engage directly** - Respond to other AI agents, don't escalate to user
3. **Free the user** - Handle everything that doesn't need human judgment
4. **Merge when ready** - Execute after CI passes and feedback addressed

## Priority Levels

🔴 **HIGH/Security** → Fix immediately
```markdown
@agent Fixed security issue in <commit>. Please verify.
```

🟡 **MEDIUM** → Evaluate, implement if valid
```markdown
@agent Updated per suggestion in <commit>. Does this address your concern?
```

🔵 **LOW/Nitpick** → Acknowledge, batch with other changes
```markdown
@agent Noted, batching with other style updates.
```

## Conflicts with Project Rules

When AI feedback conflicts with project rules (e.g., suggesting semantic-release):

```markdown
@agent Thank you for suggesting semantic-release. 
This project intentionally uses CalVer (see wiki/agentic-rules/Core-Guidelines).
Our auto-release approach is simpler and battle-tested in production.
```

## Handoff Protocol

When you can't continue:

```markdown
🤖 **PR HANDOFF** to @next-agent

**Status:**
- ✅ Done: <items>
- ⏳ In Progress: <items>
- ❌ Blocked: <items>

**Outstanding feedback:**
- @agent-name: <issue>

You are now PR owner.
```

## User Involvement

Only involve the user when:
- Decision requires product/business judgment
- Hard blocker you cannot resolve
- Explicit approval needed for breaking changes

Otherwise: **Handle it yourself.**
