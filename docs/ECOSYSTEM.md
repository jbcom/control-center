# Ecosystem Workflows

The **Ecosystem** is a unified family of GitHub Actions workflows powered by **control-center**.

## Architecture

```
                    ┌─────────────────────────┐
                    │   @agentic/control      │
                    │   (npm package)         │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ CursorAPI     │   │ Triage Tools  │   │ Fleet Manager │
│ (fleet/)      │   │ (triage/)     │   │ (fleet/)      │
└───────────────┘   └───────────────┘   └───────────────┘
```

## Workflows

| Workflow | Purpose | Uses |
|----------|---------|------|
| `triage.yml` | Issue/PR triage & health | `control-center curator` |
| `review.yml` | AI-assisted PR review | `control-center reviewer` |
| `autoheal.yml` | CI failure analysis | `control-center fixer` |
| `delegator.yml` | Command routing (@claude) | `control-center delegator` |

## Actions from control-center

```yaml
# PR review
- uses: jbcom/control-center/.github/workflows/review.yml@main
  with:
    pr_number: ${{ github.event.pull_request.number }}
    repository: ${{ github.repository }}
  secrets:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# CI resolution
- uses: jbcom/control-center/.github/workflows/autoheal.yml@main
  with:
    run_id: ${{ github.event.workflow_run.id }}
    repository: ${{ github.repository }}
  secrets:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `CURSOR_API_KEY` | Cursor Cloud Agent API |
| `GOOGLE_JULES_API_KEY` | Google Jules API |
| `OLLAMA_API_KEY` | Ollama cloud API |

## Related Packages

- `jbcom/control-center` - Central CLI + GitHub Actions workflows
