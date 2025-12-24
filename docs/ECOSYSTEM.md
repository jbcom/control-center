# Ecosystem Workflows

The **Ecosystem** is a unified family of GitHub Actions workflows powered by `@agentic/control`.

## Managed Organizations

| Organization | Domain | Purpose |
|--------------|--------|---------|
| `jbcom` | jonbogaty.com | Primary ecosystem - control center, games, portfolio |
| `strata-game-library` | strata.game | Procedural 3D graphics library for React Three Fiber |
| `agentic-dev-library` | agentic.dev | AI agent orchestration and fleet management |
| `extended-data-library` | extendeddata.dev | Enterprise data utilities and vendor connectors |

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
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  4 Organizations      │
                    │  jbcom                │
                    │  strata-game-library  │
                    │  agentic-dev-library  │
                    │  extended-data-library│
                    └───────────────────────┘
```

## Workflows

| Workflow | Purpose | Schedule | Uses |
|----------|---------|----------|------|
| `ecosystem-curator` | Nightly orchestration | Daily 00:00 UTC | `agentic-orchestrator` |
| `ecosystem-reviewer` | PR lifecycle | On PR events | `agentic-pr-review` |
| `ecosystem-fixer` | CI resolution | On workflow failure | `agentic-ci-resolution` |
| `ecosystem-delegator` | Issue delegation | On `/jules` `/cursor` | `agentic-issue-triage` |
| `ecosystem-harvester` | Agent monitoring | Every 15 min | Direct fleet API |
| `ecosystem-sage` | On-call advisor | On-demand | Ollama |
| `org-infrastructure` | Repo creation | Weekly | Direct GitHub API |

## Organization Infrastructure

Each organization gets:
- `.github` - Org-wide settings, profile README, FUNDING.yml
- `<org>.github.io` - Documentation site (Astro + Starlight)

The `org-infrastructure` workflow idempotently creates these repos and spawns Jules to build branded documentation sites derived from jbcom styling.

## Actions from @agentic/control

```yaml
# Fleet orchestration
- uses: jbcom/nodejs-agentic-control/actions/agentic-orchestrator@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    command: summary

# PR review
- uses: jbcom/nodejs-agentic-control/actions/agentic-pr-review@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    model: glm-4.6:cloud

# Issue triage
- uses: jbcom/nodejs-agentic-control/actions/agentic-issue-triage@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    issue_number: ${{ github.event.issue.number }}

# CI resolution
- uses: jbcom/nodejs-agentic-control/actions/agentic-ci-resolution@main
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    run_id: ${{ github.event.workflow_run.id }}
```

## Required Secrets

| Secret | Purpose |
|--------|---------|
| `CURSOR_API_KEY` | Cursor Cloud Agent API |
| `GOOGLE_JULES_API_KEY` | Google Jules API |
| `OLLAMA_API_KEY` | Ollama cloud API |

## Required Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `https://ollama.com` | Ollama API host |
| `OLLAMA_MODEL` | `glm-4.6:cloud` | Default AI model |

## Related Packages

| Package | Organization | Purpose |
|---------|--------------|---------|
| `@agentic/control` | agentic-dev-library | Orchestration and fleet management |
| `@agentic/triage` | agentic-dev-library | AI triage primitives (Zod, Vercel AI SDK) |
| `@agentic/crew` | agentic-dev-library | CrewAI integration |
| `vendor-connectors` | extended-data-library | Vendor API clients (Cursor, GitHub, etc.) |

## Domain Configuration

Each organization maintains its own domain:
- **jbcom**: jonbogaty.com (primary portfolio)
- **strata-game-library**: strata.game (3D graphics docs)
- **agentic-dev-library**: agentic.dev (AI agent docs)
- **extended-data-library**: extendeddata.dev (data utilities docs)

Documentation sites are built with Astro + Starlight and deploy to GitHub Pages with custom domain configuration.
