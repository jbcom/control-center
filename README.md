# jbcom Control Center

**Monorepo for the jbcom Python ecosystem.**

## Architecture

All Python packages live in `packages/`:

```
packages/
├── extended-data-types/    → PyPI: extended-data-types
├── lifecyclelogging/       → PyPI: lifecyclelogging
├── directed-inputs-class/  → PyPI: directed-inputs-class
└── vendor-connectors/      → PyPI: cloud-connectors
```

## How It Works

1. **Develop here** - Edit code in `packages/`
2. **PR to main** - CI runs tests, lint, review
3. **Merge** - Sync workflow pushes to public repos
4. **Release** - pycalver bumps version, publishes to PyPI

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
| `pyproject.toml` | uv workspace + pycalver config |
| `packages/ECOSYSTEM.toml` | Package metadata, dependencies, release order |
| `.github/workflows/release.yml` | PyPI publishing with pycalver |
| `.github/workflows/sync-packages.yml` | Sync to public repos |
| `.ruler/` | Agent instructions (source of truth) |

## Versioning

Uses [pycalver](https://github.com/mbarkhau/pycalver) at workspace level:
- Format: `YYYYMM.NNNN` (e.g., `202511.0042`)
- Config in root `pyproject.toml`
- Bumps all packages simultaneously

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
| vendor-connectors | [cloud-connectors](https://pypi.org/project/cloud-connectors/) | Cloud integrations |

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
