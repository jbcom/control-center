# PR Ownership Protocol

> **First agent on PR = PR Owner** with full responsibility until merge.

## Responsibilities

1. **Address ALL feedback** - Human AND AI agents
2. **Engage directly** - Respond to @gemini-code-assist, @copilot, etc.
3. **Free the user** - Handle everything autonomously
4. **Merge when ready** - Execute after CI passes

## Priority Levels

🔴 **HIGH/Security** → Fix immediately
```markdown
@agent Fixed in <commit>. Please verify.
```

🟡 **MEDIUM** → Evaluate, implement if valid
```markdown
@agent Updated per suggestion. Does this address your concern?
```

🔵 **LOW/Nitpick** → Acknowledge, batch
```markdown
@agent Noted, batching with other changes.
```

## Conflicts with Rules

When AI feedback conflicts with project rules:

```markdown
@agent Thank you for suggesting semantic-release. 
This project uses CalVer intentionally (see wiki Agentic-Rules-Core-Guidelines).
Our auto-release approach is simpler and battle-tested.
```

## Handoff Protocol

```markdown
🤖 **PR HANDOFF** to @next-agent

**Status:**
- ✅ Done: <items>
- ⏳ In Progress: <items>
- ❌ Blocked: <items>

**Outstanding feedback from:**
- @agent-name: <issue>

You are now PR owner.
```
