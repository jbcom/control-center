# Ruler Directory - AI Agent Instructions

This directory contains the **single source of truth** for all AI agent instructions.

## How Ruler Works

Ruler centralizes AI agent instructions in `.ruler/*.md` files and generates agent-specific configuration files.

### Processing Order

1. `AGENTS.md` - Core guidelines (always first)
2. Remaining `.md` files in sorted order

### Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Core guidelines, versioning, monorepo structure |
| `copilot.md` | GitHub Copilot patterns and quick reference |
| `cursor.md` | Cursor agent modes, hold-open PR pattern |
| `ecosystem.md` | Package relationships and coordination |
| `fleet-coordination.md` | cursor-fleet tooling documentation |
| `environment-setup.md` | Dev environment setup |
| `agent-self-sufficiency.md` | Tool availability and self-healing |

### Output Files (Generated - DO NOT edit)

- `.cursorrules` - Cursor AI
- `.claud` - Claude Code
- `.github/copilot-instructions.md` - GitHub Copilot
- `AGENTS.md` (root) - Aider and general AI agents

## Making Changes

### Update Agent Instructions

1. **Edit files in `.ruler/`:**
   ```bash
   vim .ruler/AGENTS.md
   vim .ruler/cursor.md
   ```

2. **Apply ruler:**
   ```bash
   pnpm exec ruler apply
   ```

3. **Review changes:**
   ```bash
   git diff .cursorrules AGENTS.md
   ```

4. **Commit:**
   ```bash
   git add .ruler/ .cursorrules .github/copilot-instructions.md AGENTS.md
   git commit -m "docs: update agent instructions"
   ```

### Configuration

Edit `.ruler/ruler.toml`:

```toml
default_agents = ["copilot", "cursor", "claude", "aider"]

[agents.copilot]
enabled = true
output_path = ".github/copilot-instructions.md"

[agents.cursor]
enabled = true
# Uses default .cursorrules

[agents.claude]
enabled = true
# Uses default .claud

[agents.aider]
enabled = true
output_path_instructions = "AGENTS.md"
```

## Key Content

### Versioning (AGENTS.md)
- Uses Python Semantic Release
- Per-package git tags
- Conventional commits required
- CalVer-style format: `YYYYMM.MINOR.PATCH`

### Fleet Tooling (fleet-coordination.md)
- cursor-fleet CLI for agent management
- Replay/recovery of conversations
- Hold-open PR pattern for long sessions

### Code Quality (copilot.md)
- Type hints required
- Google-style docstrings
- Ruff for linting

## Best Practices

1. **Be explicit** - Don't assume agents understand context
2. **Use examples** - Show both good and bad patterns
3. **Explain why** - Not just what to do
4. **Keep updated** - Revise based on agent behavior

---

**Ruler Version:** Compatible with @intellectronica/ruler latest
**Last Updated:** 2025-11-30
