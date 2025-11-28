# PR Ownership Protocol

> **First agent on PR = PR Owner** with full responsibility until merge.

## Responsibilities

1. **Address ALL feedback** - Human AND AI agents
2. **Engage directly** - Respond to @gemini-code-assist, @copilot, etc.
3. **Free the user** - Handle everything autonomously
4. **Merge when ready** - Execute after CI passes

## Priority Levels

🔴 **HIGH/Security** → Fix immediately, tag agent in commit
🟡 **MEDIUM** → Evaluate, implement if valid
🔵 **LOW/Nitpick** → Acknowledge, batch with other changes

## Conflicts with Project Rules

```markdown
@agent Thank you for suggesting semantic-release. 
This project uses CalVer intentionally (see Core-Guidelines).
```

## Handoff Protocol

```markdown
🤖 **PR HANDOFF** to @next-agent

**Status:**
- ✅ Done: <items>
- ⏳ In Progress: <items>

You are now PR owner.
```
