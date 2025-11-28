# Claude Code Project Instructions

> **📚 Full documentation**: https://github.com/jbcom/jbcom-control-center/wiki/Agent-Instructions-Claude

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

## Wiki Access

```bash
# Read current context
wiki-cli read "Memory-Bank-Active-Context"

# Read guidelines
wiki-cli read "Agentic-Rules-Core-Guidelines"

# Update progress
wiki-cli append "Memory-Bank-Progress" "## Update"
```

## GitHub Auth

```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...
```

For full instructions, see the [wiki](https://github.com/jbcom/jbcom-control-center/wiki/Agent-Instructions-Claude).
