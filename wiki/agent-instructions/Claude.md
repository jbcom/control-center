# Claude Code Instructions

## Project Overview

**jbcom-control-center** - Monorepo managing the jbcom Python library ecosystem.

## Key Rules

1. **CalVer**: `YYYY.MM.BUILD` - never manual, auto-generated
2. **Package manager**: `uv`
3. **Lint**: `ruff check --fix && ruff format`
4. **Type check**: `mypy src/`
5. **Test**: `pytest`

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
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge ...
```

## Wiki Access

The wiki/ folder in the repo is the source of truth. Edit there, push to main.

```bash
# Edit wiki
vim wiki/memory-bank/Progress.md

# Commit and push - auto-syncs to wiki
git add wiki/
git commit -m "Update progress"
git push
```

## Custom Commands

- `/label-issue` - Triage and label issues
- `/review-pr` - Review pull requests
- `/fix-ci` - Fix CI failures
- `/ecosystem-sync` - Check ecosystem health

## DO NOT

- ❌ Change versions manually
- ❌ Use semantic-release
- ❌ Add duplicate utilities (check extended-data-types)
- ❌ Skip tests
- ❌ Edit wiki directly (edit wiki/ folder in repo)
