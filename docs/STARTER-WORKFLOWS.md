# Starter Workflows

This document describes the standardized GitHub Actions workflows synced to all jbcom repositories.

## Overview

Workflows are organized by scope:

| Directory | Sync Behavior | Description |
|-----------|---------------|-------------|
| `always-sync/` | Always overwrite | Core workflows for all repos |
| `python/` | Always overwrite | Python-specific workflows |
| `nodejs/` | Always overwrite | Node.js/TypeScript-specific workflows |
| `go/` | Always overwrite | Go-specific workflows |
| `terraform/` | Always overwrite | Terraform-specific workflows |
| `initial-only/` | Sync once | Templates repos can customize |

## Core Workflows (always-sync)

These workflows are synced to ALL repositories:

### CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `claude-code.yml` | Issue/PR comments | Claude AI assistance |
| `pr-review.yml` | PR opened/updated | AI code review |
| `auto-assign.yml` | Issue/PR opened | Auto-assign Copilot |
| `project-sync.yml` | Issue/PR events | Sync with GitHub Projects |

### Automation

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `stale.yml` | Daily schedule | Mark/close stale issues/PRs |
| `greetings.yml` | First contribution | Welcome new contributors |
| `labeler.yml` | PR opened | Auto-label based on file paths |

### Security

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `codeql.yml` | Push/PR/Schedule | Semantic code analysis |
| `dependency-review.yml` | PR opened | Check for vulnerable dependencies |
| `sbom.yml` | Push/Release | Generate Software Bill of Materials |

## Language-Specific Workflows

### Python Repositories

**CI Workflow** (`python/.github/workflows/ci.yml`):
- Matrix: Python 3.11, 3.12, 3.13
- Linting: ruff check + format
- Type checking: mypy
- Testing: pytest with coverage
- Coverage: Codecov upload

**Release Workflow** (`python/.github/workflows/release.yml`):
- Triggered on release publish
- Builds wheel and sdist
- Publishes to PyPI using trusted publishing

### Node.js Repositories

**CI Workflow** (`nodejs/.github/workflows/ci.yml`):
- Matrix: Node 20.x, 22.x
- Linting: `npm run lint`
- Type checking: `npm run typecheck`
- Build: `npm run build`
- Testing: `npm test`

**Release Workflow** (`nodejs/.github/workflows/release.yml`):
- Triggered on release publish
- Publishes to npm with provenance

### Go Repositories

**CI Workflow** (`go/.github/workflows/ci.yml`):
- Matrix: Go 1.22, 1.23
- Linting: golangci-lint
- Build: `go build`
- Testing: `go test` with race detection

**Release Workflow** (`go/.github/workflows/release.yml`):
- Uses GoReleaser for multi-platform binaries
- Docker image publishing to GHCR

### Terraform Repositories

**CI Workflow** (`terraform/.github/workflows/ci.yml`):
- Format check: `terraform fmt`
- Validation: `terraform validate`
- Linting: TFLint
- Security: tfsec + Checkov
- Docs: terraform-docs auto-generation

**Release Workflow** (`terraform/.github/workflows/release.yml`):
- Validates module
- Generates documentation
- Creates GitHub release

## Configuration Files

### `labeler.yml` (Root)

Configures automatic PR labeling based on file paths:

```yaml
# Labels added based on changed files
documentation:  # *.md, docs/
ci:            # .github/
dependencies:  # package.json, requirements.txt, go.mod
tests:         # **/test*, **/*_test.*
python:        # *.py
javascript:    # *.js, *.ts
go:            # *.go
terraform:     # *.tf
```

### `dependabot.yml` (initial-only)

Standard Dependabot configuration:

- Groups minor/patch updates
- Weekly schedule (Monday)
- Auto-labels PRs
- Covers npm, pip, GitHub Actions

## Customization

### Repository-Specific Overrides

Repos can customize by:

1. **Adding local workflows** in `.github/workflows/`
2. **Extending CI** with repo-specific steps
3. **Creating `copilot-instructions-local.md`** for local patterns

### Disabling Workflows

To disable a synced workflow:

```yaml
# .github/workflows/<workflow>.yml
name: Disabled

on: workflow_dispatch

jobs:
  disabled:
    runs-on: ubuntu-latest
    steps:
      - run: echo "This workflow is disabled in this repo"
```

## Source

Based on GitHub's official [starter-workflows](https://github.com/actions/starter-workflows) repository with customizations for jbcom standards.
