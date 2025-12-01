# Contributing to Unified Control Center

## Overview

This repository manages two ecosystems:

| Ecosystem | Path | Output |
|-----------|------|--------|
| jbcom | `packages/` | PyPI + npm |
| FlipsideCrypto | `ecosystems/flipside-crypto/` | AWS/GCP infrastructure |

## Quick Start

```bash
# Clone
git clone https://github.com/jbcom/jbcom-control-center.git
cd jbcom-control-center

# Python packages
uv sync

# Node.js packages
pnpm install
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b <type>/<description>
```

Branch types:
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions

### 2. Make Changes

Follow the standards for each ecosystem:

**Python packages:**
- Type hints required
- Google-style docstrings
- Tests for new functions

**Node.js (agentic-control):**
- TypeScript strict mode
- JSDoc comments
- Vitest tests

**Terraform:**
- Module documentation
- Variable descriptions
- Output descriptions

### 3. Commit with Conventional Commits

```bash
git commit -m "<type>(<scope>): <description>"
```

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `bridge` | python-terraform-bridge |
| `connectors` | vendor-connectors |
| `agentic-control` | agentic-control |
| `fsc` | FlipsideCrypto infrastructure |

Examples:
```bash
feat(edt): add new utility function
fix(connectors): handle null response
docs(agentic-control): update CLI reference
```

### 4. Create Pull Request

```bash
git push -u origin <branch>
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "<type>(<scope>): <description>"
```

### 5. Request AI Review

Post as PR comment:
```
/gemini review
/q review
```

### 6. Address Feedback

- Fix all critical/high severity issues
- Respond to every comment
- Re-request review if significant changes

### 7. Merge

After CI passes and reviews addressed:
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <number> --squash --delete-branch
```

## Token Configuration

### For jbcom repos
```bash
export GITHUB_JBCOM_TOKEN="ghp_..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>
```

### For FlipsideCrypto repos
```bash
export GITHUB_FSC_TOKEN="ghp_..."
GH_TOKEN="$GITHUB_FSC_TOKEN" gh <command>
```

### Automatic (via agentic-control)
```bash
agentic github pr create --repo <org/repo>  # Token selected automatically
```

## Testing

### Python
```bash
# All packages
tox

# Single package
tox -e extended-data-types

# Lint
tox -e lint
```

### Node.js
```bash
cd packages/agentic-control
pnpm test
```

### Terraform
```bash
cd ecosystems/flipside-crypto/terraform/workspaces/<workspace>
terraform validate
terraform plan
```

## CI/CD

CI runs automatically on:
- Push to `main`
- Pull requests

Jobs:
- Build all packages
- Test (Python 3.9 + 3.13)
- Lint (Ruff)
- agentic-control build + test

On merge to `main`:
- python-semantic-release bumps versions
- Publishes to PyPI/npm
- Syncs to public repos
- Deploys docs

## Code of Conduct

Be respectful. Focus on the code, not the person. Assume good intent.

## Questions?

Open an issue or check:
- `ECOSYSTEM.toml` - Package manifest
- `.ruler/AGENTS.md` - Agent guidelines
- `docs/` - Process documentation
