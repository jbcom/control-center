# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Does

jbcom Control Center is a unified hub that:
1. **Manages all repository configuration** via shell scripts + gh CLI
2. **Syncs files** to all managed repos (Cursor rules, workflows, etc.)
3. **Provides reusable AI-powered workflows** that any repo can call

---

## 🚀 Using Control Center Workflows from Other Repos

Any repository can leverage the control center's AI-powered workflows by calling them as reusable workflows.

### Required Secrets

Configure these secrets in your repository (Settings → Secrets → Actions):

| Secret | Required | Purpose |
|--------|----------|---------|
| `CI_GITHUB_TOKEN` | **Yes** | PAT with `repo`, `workflow` scopes for cross-repo operations |
| `ANTHROPIC_API_KEY` | For Claude | Claude Code API key |
| `GOOGLE_JULES_API_KEY` | For Jules | Google Jules API key |
| `OLLAMA_API_KEY` | For Ollama | Ollama Cloud API key |
| `CURSOR_API_KEY` | For Cursor | Cursor Cloud Agent API key |

### Available Reusable Workflows

#### 1. Ecosystem Reviewer (AI PR Review)

```yaml
# .github/workflows/ai-review.yml
name: AI Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    uses: jbcom/control-center/.github/workflows/ecosystem-reviewer.yml@main
    with:
      pr_number: ${{ github.event.pull_request.number }}
      repository: ${{ github.repository }}
      model_tier: 'ollama'  # Options: ollama, claude, jules, all
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
```

#### 2. Ecosystem Fixer (Auto-fix CI Failures)

```yaml
# .github/workflows/ci-fixer.yml
name: CI Fixer
on:
  workflow_run:
    workflows: ["CI", "Build", "Test"]
    types: [completed]

jobs:
  fix:
    if: github.event.workflow_run.conclusion == 'failure'
    uses: jbcom/control-center/.github/workflows/ecosystem-fixer.yml@main
    with:
      run_id: ${{ github.event.workflow_run.id }}
      repository: ${{ github.repository }}
      branch: ${{ github.event.workflow_run.head_branch }}
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### 3. Ecosystem Delegator (Issue → AI Agent)

```yaml
# .github/workflows/delegate.yml
name: AI Delegation
on:
  issue_comment:
    types: [created]

jobs:
  delegate:
    if: |
      contains(github.event.comment.body, '/jules') ||
      contains(github.event.comment.body, '/cursor') ||
      contains(github.event.comment.body, '@claude')
    uses: jbcom/control-center/.github/workflows/ecosystem-delegator.yml@main
    with:
      comment_body: ${{ github.event.comment.body }}
      issue_number: ${{ github.event.issue.number }}
      issue_title: ${{ github.event.issue.title }}
      issue_body: ${{ github.event.issue.body }}
      repository: ${{ github.repository }}
      default_branch: ${{ github.event.repository.default_branch }}
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
      CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### 4. Ecosystem Sage (AI Q&A Advisor)

```yaml
# .github/workflows/sage.yml
name: Sage Advisor
on:
  issue_comment:
    types: [created]

jobs:
  sage:
    if: contains(github.event.comment.body, '@sage') || contains(github.event.comment.body, '/sage')
    uses: jbcom/control-center/.github/workflows/ecosystem-sage.yml@main
    with:
      query: ${{ github.event.comment.body }}
      context_repo: ${{ github.repository }}
      context_issue: ${{ github.event.issue.number }}
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
```

### AI Agent Triggers (in Issues/PRs)

| Trigger | Agent | Description |
|---------|-------|-------------|
| `/jules <task>` | Google Jules | Multi-file refactoring, creates PR automatically |
| `/cursor <task>` | Cursor Cloud | Long-running tasks with full IDE context |
| `@claude <task>` | Claude Code | Complex reasoning, implements and creates PR |
| `@sage <question>` | Ollama | Quick answers, task decomposition |
| `/sage <question>` | Ollama | Same as @sage |

---

## Structure

```
.
├── repo-config.json         # Repository configuration (source of truth)
├── repository-files/        # Files synced to target repos
│   ├── always-sync/         # Always overwrite (Cursor rules, workflows)
│   ├── initial-only/        # Sync once, repos customize after
│   ├── python/              # Python language rules
│   ├── nodejs/              # Node.js/TypeScript rules
│   ├── go/                  # Go language rules
│   └── terraform/           # Terraform/HCL language rules
├── scripts/                 # Shell scripts for repo management
│   ├── sync-files           # Rsync files to repos
│   ├── configure-repos      # Configure repo settings via gh CLI
│   └── sync-secrets         # Sync secrets to repos
├── .github/workflows/
│   └── repo-sync.yml        # Orchestrates all syncing
├── docs/                    # Documentation
├── memory-bank/             # Agent session context
└── packages/                # Local packages
```

## Authentication

A unified GitHub token is used for all operations:

| Variable | Use Case |
|----------|----------|
| `GITHUB_TOKEN` | Default token for GitHub Actions and general API access |
| `CI_GITHUB_TOKEN` | Legacy PAT for triggering workflows (being replaced by JULES_GITHUB_TOKEN) |
| `JULES_GITHUB_TOKEN` | Primary PAT for Jules and Ecosystem Curator workflows |
| `CURSOR_GITHUB_TOKEN` | GitHub token for Cursor agent operations |
| `CURSOR_API_KEY` | Cursor Cloud Agent API key |
| `GOOGLE_JULES_API_KEY` | Google Jules API key (standardized) |
| `OLLAMA_API_URL` | Ollama Cloud API URL (standardized) |
| `OLLAMA_API_KEY` | Ollama Cloud API key |
| `CURSOR_SESSION_TOKEN` | Cursor Background Composer Session Token |

```bash
# All repos use the same token - gh CLI auto-uses GITHUB_TOKEN
gh pr list --repo jbcom/jbcom-control-center
```

## Repository Management

### Configuration
All repo settings are defined in `repo-config.json`:
- Merge settings (squash only, delete branch on merge)
- Features (issues, projects, wiki, discussions, pages)
- Security (Dependabot, secret scanning)
- Rulesets (branch protection)
- Labels

### Scripts

```bash
# Sync files to all repos
./scripts/sync-files --all

# Configure repo settings
./scripts/configure-repos --all

# Sync secrets
./scripts/sync-secrets --all

# Orchestrate agents
./scripts/ecosystem-harvester.mjs jbcom/jbcom-control-center cursor:agent-id:123

# Preview without making changes
./scripts/sync-files --dry-run --all
./scripts/configure-repos --dry-run --all
```

## Agent Orchestration

The `scripts/ecosystem-harvester.mjs` script manages multi-agent workflows.

### Ecosystem Curator

The `scripts/ecosystem-curator.mjs` script is a nightly autonomous orchestration workflow that triages issues and processes PRs across all repositories in the `jbcom` organization.

- **Schedule**: Nightly at 2 AM UTC (`.github/workflows/ecosystem-curator.yml`)
- **Discovery**: Scans all non-archived repositories in the `jbcom` org.
- **Triage**:
  - Complex issues/Epics -> Google Jules session.
  - Quick fixes -> Cursor Cloud Agent.
  - Questions -> Ollama (GLM 4.6 Cloud) resolution.
- **PR Processing**:
  - Failed CI -> Cursor Agent fix.
  - Blocking reviews -> Cursor Agent address.
  - Ready to merge -> Auto-merge (squash).
  - Agent questions -> Ollama resolution.

### Task Routing Guidelines

| Task Type | Recommended Agent | Description |
|-----------|-------------------|-------------|
| **Quick Fix** | Ollama | Fast, local execution for single-file changes |
| **Multi-file** | Jules | Google Jules for complex multi-file refactors |
| **Long-running** | Cursor | Cursor Cloud Agents for autonomous background tasks |

### API Endpoints

- **Cursor Cloud Agent**: `https://api.cursor.com/v0/agents` (Requires `CURSOR_API_KEY`)
- **Google Jules**: `https://jules.googleapis.com/v1alpha/sessions` (Requires `GOOGLE_JULES_API_KEY`)

## Session Start/End Protocol

### Start of Session
```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md
```

### End of Session
```bash
cat >> memory-bank/activeContext.md << EOF

## Session: $(date +%Y-%m-%d)

### Completed
- [x] Task description

### For Next Agent
- [ ] Follow-up task
EOF

git add memory-bank/
git commit -m "docs: update memory bank for handoff"
```

## Sync Behavior

| Directory | Behavior | Purpose |
|-----------|----------|---------|
| `always-sync/` | Always overwrite | Cursor rules, workflows |
| `initial-only/` | Sync once | Dockerfile, env, docs scaffold |
| `python/`, `nodejs/`, `go/`, `terraform/` | Always overwrite | Language-specific rules |

## Managed Repositories

Defined in `repo-config.json`:

**Python:** agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors

**Node.js:** agentic-control, agentic-triage, strata, otter-river-rush, otterfall, rivermarsh, pixels-pygame-palace

**Go:** port-api, vault-secret-sync, secretsync

**Terraform:** terraform-github-markdown, terraform-repository-automation

## Workflow Triggers

| Event | Actions |
|-------|---------|
| Push to main (repository-files/**) | Sync files to all repos |
| Daily schedule | Sync secrets |
| Manual dispatch | Selective sync with dry-run |

## Rules

### Don't
- Push to main without PR
- Manually edit versions (use conventional commits)
- Skip tests

### Do
- Use PRs for changes
- Update memory-bank on session end
- Use conventional commits with scopes

## Documentation

- Token management: `docs/TOKEN-MANAGEMENT.md`
- Environment variables: `docs/ENVIRONMENT_VARIABLES.md`

## Cursor Cloud Agent Orchestration

### Environment Variables

Cloud agents have access to:
- `GOOGLE_JULES_API_KEY` - Google Jules API for async code changes
- `CURSOR_GITHUB_TOKEN` - GitHub API for repo operations
- `CURSOR_API_KEY` - Cursor API for agent operations

### Jules API Usage

```bash
# Create session
curl -X POST 'https://jules.googleapis.com/v1alpha/sessions' \
  -H "X-Goog-Api-Key: $GOOGLE_JULES_API_KEY" \
  -d '{
    "prompt": "Task description",
    "sourceContext": {
      "source": "sources/github/jbcom/REPO_NAME",
      "githubRepoContext": {"startingBranch": "main"}
    },
    "automationMode": "AUTO_CREATE_PR"
  }'
```

### Orchestrator Script

```bash
node scripts/ecosystem-harvester.mjs
```

### Task Routing

| Task Type | Agent |
|-----------|-------|
| Quick fix (<10 lines) | Cursor (direct) |
| Multi-file refactor | Jules |
| CI failure resolution | Cursor (direct) |
| Documentation | Jules |
| Complex debugging | Cursor (direct) |

## Cursor Background Composer API

The ecosystem uses Cursor's Background Composer API for AI-assisted coding tasks.

**Authentication**: Session token via `WorkosCursorSessionToken` cookie

**API Reference**: https://github.com/mjdierkes/cursor-background-agent-api

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/startBackgroundComposerFromSnapshot` | POST | Create a new background composer |
| `/api/background-composer/list` | POST | List all composers |
| `/api/background-composer/get-detailed-composer` | POST | Get composer details |
| `/api/background-composer/open-pr` | POST | Create PR from composer |
| `/api/background-composer/pause` | POST | Pause a running composer |

### Getting the Session Token

1. Log in to [cursor.com](https://cursor.com)
2. Open browser DevTools → Application → Cookies
3. Copy the value of `WorkosCursorSessionToken`
4. Set as `CURSOR_SESSION_TOKEN` secret
