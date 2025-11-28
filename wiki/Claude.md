# Claude Code Instructions

## Key Rules

1. **Versioning**: `YYYYMM.MINOR.PATCH` via python-semantic-release
2. **Commits**: Conventional commits with scopes (`edt`, `logging`, `dic`, `connectors`)
3. **Package manager**: `uv`
4. **Lint**: `ruff check --fix && ruff format`
5. **Type check**: `mypy src/`
6. **Test**: `pytest`

## Commit Scopes

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

## Packages

| Package | Location |
|---------|----------|
| extended-data-types | `packages/extended-data-types/` |
| lifecyclelogging | `packages/lifecyclelogging/` |
| vendor-connectors | `packages/vendor-connectors/` |
| directed-inputs-class | `packages/directed-inputs-class/` |

## GitHub Auth

```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...
```

## Custom Commands

- `/label-issue` - Triage and label issues
- `/review-pr` - Review pull requests
- `/fix-ci` - Fix CI failures
- `/ecosystem-sync` - Check ecosystem health

## DO NOT

- ❌ Change versions manually
- ❌ Remove Git tags (they track release state)
- ❌ Use non-conventional commit messages
- ❌ Add duplicate utilities
- ❌ Skip tests
