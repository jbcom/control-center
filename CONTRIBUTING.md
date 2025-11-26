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
5. Commit: `git commit -m "fix: description"`
6. Push: `git push -u origin fix/description`
7. Create PR: `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create`

## Code Style

- **Linting**: ruff (configured in pyproject.toml)
- **Type hints**: Required for public APIs
- **Docstrings**: Google style
- **Tests**: pytest, aim for good coverage

## Versioning

We use pycalver (`YYYYMM.NNNN`). Version bumps happen automatically at release time - never edit `__version__` manually.

## Pull Requests

- Clear title describing the change
- Brief description of what and why
- Tests for new features
- CI must pass before merge

## Questions?

Check `.cursor/agents/jbcom-ecosystem-manager.md` or `.ruler/AGENTS.md`.
