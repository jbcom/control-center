# Claude Code Instructions

## Project Overview

This is the **jbcom-control-center** - a monorepo managing the jbcom Python library ecosystem.

## Key Rules

1. **CalVer**: `YYYY.MM.BUILD` - never manual
2. **Package manager**: uv
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
```

## Wiki Access

```bash
# Read
wiki-cli read "Memory-Bank-Active-Context"

# Write
wiki-cli write "Memory-Bank-Progress" "content"

# Append
wiki-cli append "Memory-Bank-Progress" "## New session"
```

## DO NOT

- ❌ Change versions manually
- ❌ Use semantic-release
- ❌ Add duplicate utilities
- ❌ Skip tests

## Available Commands

- `/label-issue` - Triage and label issues
- `/review-pr` - Review pull requests
- `/fix-ci` - Fix CI failures
- `/ecosystem-sync` - Check ecosystem health
