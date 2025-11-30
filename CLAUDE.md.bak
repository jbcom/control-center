# Claude Code Project Instructions

> **📚 Full documentation**: `.ruler/AGENTS.md`

## Quick Reference

- **Versioning**: `YYYYMM.MINOR.PATCH` via python-semantic-release
- **Commits**: Conventional commits with scopes (`edt`, `logging`, `dic`, `connectors`)
- **Package manager**: uv
- **Lint**: `ruff check --fix && ruff format`
- **Type check**: `mypy src/`
- **Test**: `pytest`

## Conventional Commit Scopes

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

## Session Context

Use GitHub Issues for session tracking:
```bash
# Check active work
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue list --label "agent-session"

# Create session context
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue create --label "agent-session" --title "🤖 Agent Session: ..."
```

## GitHub Auth

```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...
```

## Agent Rules

All rules are in `.ruler/`:
- `AGENTS.md` - Core guidelines
- `cursor.md` - Cursor-specific
- `fleet-coordination.md` - Multi-agent coordination
- `ruler.toml` - MCP server config

Run `ruler apply` to regenerate agent instruction files.
