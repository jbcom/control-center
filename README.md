# jbcom Control Center

**Monorepo for the jbcom Python ecosystem.**

## Architecture

All Python packages live in `packages/`:

```
packages/
├── extended-data-types/    → PyPI: extended-data-types
├── lifecyclelogging/       → PyPI: lifecyclelogging
├── directed-inputs-class/  → PyPI: directed-inputs-class
└── vendor-connectors/      → PyPI: vendor-connectors
```

## How It Works

1. **Develop here** - Edit code in `packages/`
2. **PR to main** - CI runs tests, lint, review
3. **Merge** - python-semantic-release bumps version, creates Git tags, publishes to PyPI
4. **Sync** - Sync workflow pushes to public repos

## Quick Start

```bash
# Install dependencies (uv workspace)
uv sync

# Run tests for a package
cd packages/extended-data-types && pytest

# Lint
ruff check packages/

# Create PR
git checkout -b fix/something
# ... make changes ...
git add -A && git commit -m "fix: something"
git push -u origin fix/something
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "fix: something" --body "Details"
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | uv workspace + dev dependencies |
| `packages/*/pyproject.toml` | Per-package PSR config |
| `packages/ECOSYSTEM.toml` | Package metadata, dependencies, release order |
| `scripts/psr/monorepo_parser.py` | Monorepo commit parser for PSR |
| `.github/workflows/ci.yml` | CI, release, and PyPI publishing |

## Versioning

Uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) with per-package configuration:
- Format: `YYYYMM.MINOR.PATCH` (e.g., `202511.3.0`)
- Major version (`202511`) maintains CalVer backward compatibility
- Minor/patch follow SemVer semantics based on conventional commits
- Each package has independent versioning tracked via Git tags

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) with package scopes:

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

Examples:
```bash
feat(edt): add new utility function     # → extended-data-types minor bump
fix(logging): handle edge case          # → lifecyclelogging patch bump
feat!: breaking change                  # → major bump (new CalVer month)
```

## Authentication

**Always use `GITHUB_JBCOM_TOKEN` for jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge ...
```

## Packages

| Package | PyPI | Role |
|---------|------|------|
| extended-data-types | [extended-data-types](https://pypi.org/project/extended-data-types/) | Foundation utilities |
| lifecyclelogging | [lifecyclelogging](https://pypi.org/project/lifecyclelogging/) | Structured logging |
| directed-inputs-class | [directed-inputs-class](https://pypi.org/project/directed-inputs-class/) | Input validation |
| vendor-connectors | [vendor-connectors](https://pypi.org/project/vendor-connectors/) | Cloud integrations |

## Dependency Order

```
extended-data-types (foundation)
├── lifecyclelogging
├── directed-inputs-class
└── vendor-connectors (depends on both)
```

Always release in this order.

---

See `.cursor/agents/jbcom-ecosystem-manager.md` for detailed agent instructions.
