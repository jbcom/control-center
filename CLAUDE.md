# Claude Code Project Instructions

This is the **jbcom-control-center** - a monorepo managing the jbcom Python library ecosystem.

## Project Overview

This repository contains:
- **packages/extended-data-types** - Foundation library with utilities and re-exports
- **packages/lifecyclelogging** - Structured lifecycle logging
- **packages/directed-inputs-class** - Declarative input validation
- **packages/vendor-connectors** - Unified vendor connectors (AWS, GCP, GitHub, etc.)

## Key Rules

### 1. Versioning (CRITICAL)
- **CalVer**: `YYYY.MM.BUILD` (e.g., `2025.11.164`)
- **Automatic**: Versions are auto-generated on CI push to main
- **NEVER manually edit** `__version__` in any `__init__.py`
- **NEVER suggest** semantic-release, git tags, or manual versioning

### 2. Release Process
- Every push to main = automatic PyPI release
- No conditional releases, no skipping
- PyPI is the source of truth (no git tags needed)

### 3. Code Style
- **Type hints required** on all public functions (Python 3.9+ style)
- **Docstrings** in Google format
- **Ruff** for linting/formatting (`ruff check --fix && ruff format`)
- **Mypy** for type checking (`mypy src/`)
- **Pytest** for testing

### 4. Dependencies
- Use **uv** as package manager (`uv pip install`, `uv run`)
- Check `extended-data-types` before adding new dependencies (it re-exports many common packages)

## Directory Structure

```
/workspace/
├── packages/              # All Python packages
│   ├── extended-data-types/
│   ├── lifecyclelogging/
│   ├── vendor-connectors/
│   └── directed-inputs-class/
├── .github/
│   ├── workflows/         # CI/CD workflows
│   └── actions/           # Custom actions
├── .cursor/               # Agent tooling
│   ├── scripts/           # CLI tools
│   └── recovery/          # Agent session recovery
├── .ruler/                # Agent instructions source
├── memory-bank/           # Agent memory and context
└── docs/                  # Documentation
```

## Common Commands

```bash
# Run tests
cd packages/<package> && pytest

# Type check
cd packages/<package> && mypy src/

# Lint and format
ruff check --fix . && ruff format .

# Install package locally
uv pip install -e packages/<package>

# Check CI status
gh run list --limit 5

# Create PR
gh pr create --title "..." --body "..."
```

## GitHub Authentication

For jbcom repositories, use:
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>
```

## Ecosystem Repos

| Package | PyPI | Public Repo |
|---------|------|-------------|
| extended-data-types | extended-data-types | jbcom/extended-data-types |
| lifecyclelogging | lifecyclelogging | jbcom/lifecyclelogging |
| directed-inputs-class | directed-inputs-class | jbcom/directed-inputs-class |
| vendor-connectors | vendor-connectors | jbcom/vendor-connectors |

## Dependency Order

1. extended-data-types (foundation - no ecosystem deps)
2. lifecyclelogging (depends on #1)
3. directed-inputs-class (depends on #1)
4. vendor-connectors (depends on #1, #2, #3)

## PR Guidelines

- Clear, descriptive title
- Explain what and why
- Include tests for new features
- Run `ruff` and `mypy` before pushing
- CI must pass before merge

## What NOT to Do

❌ Manually edit version numbers
❌ Suggest semantic-release or git tags
❌ Add dependencies without checking extended-data-types first
❌ Push directly to main (use PRs)
❌ Use outdated type hint syntax (typing.List, typing.Dict)

## Custom Commands

This repo has custom Claude commands in `.claude/commands/`:
- `/label-issue` - Triage and label GitHub issues
- `/review-pr` - Comprehensive PR review
- `/fix-ci` - Auto-fix CI failures
- `/ecosystem-sync` - Check ecosystem health

## Agent Memory

Check `memory-bank/` for:
- `activeContext.md` - Current work focus
- `progress.md` - Session history
- `agenticRules.md` - Behavioral guidelines
