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
| `org-apps-audit` | App installation check | Weekly | Direct GitHub API |

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

## Required GitHub Apps

Each organization needs these apps installed for full automation:

| App | Priority | Purpose |
|-----|----------|---------|
| **Google Jules** | Critical | AI code generation, async refactoring |
| **Cursor** | Critical | AI code assistant, background agents |
| **Claude** | High | AI assistant, code review |
| **Gemini Code Assist** | High | AI code review |
| **Amazon Q Developer** | High | AI code review |
| **Renovate** | High | Automated dependency updates |
| **Settings** | Medium | Repository settings sync |

### Why Manual Installation?

GitHub requires OAuth consent for app installations - there's no API to programmatically install apps. Each app must be installed manually on each organization.

### Audit Workflow

The `org-apps-audit` workflow runs weekly to check installations and creates issues for missing apps.

```bash
# Manual check
gh workflow run org-apps-audit.yml --repo jbcom/control-center

# CLI check
gh api /orgs/strata-game-library/installations --jq '.installations[].app_slug'
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

## Release Process

Control Center uses a unified release process that publishes:

1. **Go Binary** (OSS) - Cross-platform binaries via GoReleaser
2. **Docker Images** - Multi-arch images to GHCR (`ghcr.io/jbcom/control-center`)
3. **GitHub Actions** - Marketplace actions with floating version tags
4. **Ecosystem Sync** - Automatic propagation to all managed organizations

### Installation

**Go:**
```bash
go install github.com/jbcom/control-center/cmd/control-center@latest
```

**Docker:**
```bash
docker pull ghcr.io/jbcom/control-center:latest
docker run ghcr.io/jbcom/control-center:latest version
```

**GitHub Action:**
```yaml
- uses: jbcom/control-center@v1
  with:
    command: reviewer
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}
```

**Binary Download:**
Download from [Releases](https://github.com/jbcom/control-center/releases) for your platform.

### Version Management

- **Current Version**: See `.release-please-manifest.json` or `CHANGELOG.md`
- **Releases**: https://github.com/jbcom/control-center/releases
- **Go Proxy**: Automatically published when users run `go install`
- **Semver**: Follows [Semantic Versioning 2.0.0](https://semver.org/)

### Release Workflow

On release (via release-please or manual tag):
1. GoReleaser builds cross-platform binaries
2. Docker images published to GHCR for `linux/amd64` and `linux/arm64`
3. Action tags updated (`v1`, `v1.x`, `v1.x.y`) for marketplace
4. Ecosystem sync triggered to propagate to all orgs

**See**: [`docs/RELEASE-PROCESS.md`](./RELEASE-PROCESS.md) for complete details.
