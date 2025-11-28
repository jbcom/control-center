# Contributing

## Development Setup

```bash
# Clone
git clone https://github.com/jbcom/jbcom-control-center
cd jbcom-control-center

# Install (uses uv workspace)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Making Changes

1. Create a branch: `git checkout -b fix/description`
2. Make changes in `packages/`
3. Run tests: `cd packages/<package> && pytest`
4. Run lint: `ruff check packages/`
5. Commit using conventional format (see below)
6. Push: `git push -u origin fix/description`
7. Create PR: `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create`

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning via python-semantic-release.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Effect | Description |
|------|--------|-------------|
| `feat` | Minor bump | New feature |
| `fix` | Patch bump | Bug fix |
| `perf` | Patch bump | Performance improvement |
| `feat!` or `BREAKING CHANGE:` | Major bump | Breaking change |
| `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build` | No bump | Maintenance |

### Package Scopes

Use these scopes to target specific packages:

| Scope | Package | Example |
|-------|---------|---------|
| `edt` | extended-data-types | `feat(edt): add utility` |
| `logging` | lifecyclelogging | `fix(logging): handle error` |
| `dic` | directed-inputs-class | `perf(dic): optimize parsing` |
| `connectors` | vendor-connectors | `feat(connectors): add provider` |

### Examples

```bash
# Minor version bump for extended-data-types
git commit -m "feat(edt): add new serialization utility"

# Patch bump for lifecyclelogging
git commit -m "fix(logging): handle edge case in formatter"

# Breaking change (major bump)
git commit -m "feat(edt)!: rename core API function

BREAKING CHANGE: `old_function` renamed to `new_function`"

# No version bump (documentation)
git commit -m "docs: update README examples"
```

## Code Style

- **Linting**: ruff (configured in pyproject.toml)
- **Type hints**: Required for public APIs
- **Docstrings**: Google style
- **Tests**: pytest, aim for good coverage

## Versioning

We use python-semantic-release with CalVer-compatible format (`YYYYMM.MINOR.PATCH`):
- Version bumps happen automatically based on conventional commits
- Each package is versioned independently via Git tags
- Never edit `__version__` manually - PSR handles it

## Pull Requests

- Clear title using conventional commit format
- Brief description of what and why
- Tests for new features
- CI must pass before merge

## Questions?

Check `.cursor/agents/jbcom-ecosystem-manager.md` or the [wiki](https://github.com/jbcom/jbcom-control-center/wiki).
