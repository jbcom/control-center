# Agent Instructions for Control Center

## Philosophy

**We are stewards and servants of the open source community FIRST.**

This repository is the **GENESIS** of everything in this enterprise. We lead by example:
- We use conventional commits because we mandate them
- We use semver because we mandate it
- We document thoroughly because we expect it from others

---

## Overview

**jbcom/control-center** is a pure Go CLI providing AI-powered automation:

| Command | Purpose |
|---------|---------|
| `reviewer` | AI code review using Ollama GLM 4.6 |
| `fixer` | CI failure analysis and fix suggestions |
| `curator` | Nightly issue/PR triage with smart routing |
| `delegator` | `/jules` and `/cursor` command routing |
| `gardener` | Enterprise cascade orchestration |

**Zero jbcom dependencies. Pure Go. Single binary.**

---

## Quick Start

```bash
# Read current context
cat memory-bank/activeContext.md

# Build and test
make build
make test
make lint

# Check ecosystem status
gh pr list --state open
gh issue list --state open
```

---

## For OSS Users

### Installation

```bash
# Go
go install github.com/jbcom/control-center/cmd/control-center@latest

# Docker
docker pull ghcr.io/jbcom/control-center:latest
```

### GitHub Actions (Recommended)

```yaml
# AI Code Review
- uses: jbcom/control-center/actions/reviewer@v1
  with:
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}

# CI Failure Analysis
- uses: jbcom/control-center/actions/fixer@v1
  with:
    repo: ${{ github.repository }}
    run_id: ${{ github.event.workflow_run.id }}

# Nightly Triage
- uses: jbcom/control-center/actions/curator@v1
  with:
    repo: ${{ github.repository }}

# Task Delegation (/jules, /cursor)
- uses: jbcom/control-center/actions/delegator@v1
  with:
    repo: ${{ github.repository }}
    issue: ${{ github.event.issue.number }}
    command: ${{ github.event.comment.body }}
```

### Required Secrets

| Secret | Required For | Source |
|--------|--------------|--------|
| `GITHUB_TOKEN` | All | Automatic in Actions |
| `OLLAMA_API_KEY` | reviewer, fixer, curator | [ollama.com](https://ollama.com) |
| `GOOGLE_JULES_API_KEY` | delegator (/jules) | Google Cloud Console |
| `CURSOR_API_KEY` | delegator (/cursor) | Cursor dashboard |

---

## For AI Agents Working on This Repo

### Commit Standards (MANDATORY)

```bash
# Good
feat(reviewer): add support for multi-file review
fix(curator): handle empty issue body gracefully
docs: update installation instructions

# Bad
Fixed bug
Update code
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full conventional commit guide.

### Before Committing

```bash
make lint    # Must pass
make test    # Must pass
```

### Session Protocol

#### Start of Session

```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md | tail -50
```

#### End of Session

```bash
cat >> memory-bank/activeContext.md << 'EOF'

## Session: $(date +%Y-%m-%d)

### Completed
- [x] Task description

### For Next Agent
- [ ] Follow-up task
EOF

git add memory-bank/
git commit -m "docs: update memory bank for handoff"
```

---

## Architecture

```
control-center/
├── cmd/control-center/     # CLI (Cobra)
│   └── cmd/                # Commands
├── pkg/
│   ├── clients/            # Native API clients
│   │   ├── ollama/         # Ollama GLM 4.6
│   │   ├── jules/          # Google Jules
│   │   ├── cursor/         # Cursor Cloud Agent
│   │   └── github/         # GitHub via gh CLI
│   └── orchestrator/       # Gardener logic
├── actions/                # Namespaced GitHub Actions
│   ├── reviewer/
│   ├── fixer/
│   ├── curator/
│   ├── delegator/
│   └── gardener/
├── docs/site/              # Hugo + doc2go
└── repository-files/       # Files synced to managed repos
```

---

## Enterprise Context

### Organizations Managed

| Organization | Domain | Purpose |
|-------------|--------|---------|
| jbcom | jonbogaty.com | Enterprise control plane |
| arcade-cabinet | arcade-cabinet.dev | Game development |
| agentic-dev-library | agentic.dev | AI agent orchestration |
| strata-game-library | strata.game | 3D graphics library |
| extended-data-library | extendeddata.dev | Enterprise data utilities |

### Sync Architecture

**See [docs/SYNC-ARCHITECTURE.md](docs/SYNC-ARCHITECTURE.md) for full details.**

```
jbcom/control-center (THE PROGENITOR)
│
├── enterprise/settings.json → jbcom org API settings
│
├── org-github-repo/settings.yml → org/.github repos (INITIAL)
│   ↓ repository-settings/app inheritance
│   ALL repos inherit these defaults (merge queue, branch protection, etc.)
│   Individual repos OVERRIDE with their own .github/settings.yml
│
├── global-sync/* → ALL repo roots (DIRECT)
│   AI workflows, ecosystem workflows, agent configs
│
└── repository-files/* → org control-centers (CASCADE)
    ↓
    org/* repos
```

### Settings Inheritance (repository-settings/app)

```
org/.github/settings.yml     ← Organization defaults
  └── repo/.github/settings.yml  ← Repo-specific overrides
```

**Example**: `arcade-cabinet/otterblade-odyssey` can have its own `settings.yml`
with a custom release environment that overrides arcade-cabinet org defaults.

### What Goes Where

| Content | Location | Method |
|---------|----------|--------|
| Merge queue, branch protection | `org-github-repo/settings.yml` | INITIAL sync to org/.github |
| AI workflows (ai-*.yml) | `global-sync/.github/workflows/` | DIRECT to all repos |
| Ecosystem workflows | `global-sync/.github/workflows/` | DIRECT to all repos |
| Agent configs | `global-sync/.github/agents/` | DIRECT to all repos |
| Cursor rules | `repository-files/always-sync/.cursor/` | CASCADE via control-centers |
| Language templates | `repository-files/initial-only/` | CASCADE (initial only) |

---

## Agent Autonomy

When assigned to a PR or issue, you are **authorized** to:

1. **PUSH** - `git push` to update PRs
2. **REBASE** - Rebase onto main to resolve conflicts
3. **FIX** - Make any changes needed to pass CI
4. **MERGE** - Merge PRs using squash merge when CI is green

**Do not ask for permission. Execute immediately.**

### Standard Pattern

```
@cursor Rebase onto main, fix conflicts, merge when CI passes
```

This means: Do it now. You have permission.

---

## AI Triggers (In Issues/PRs)

| Command | Agent | Action |
|---------|-------|--------|
| `/jules <task>` | Google Jules | Creates PR automatically |
| `/cursor <task>` | Cursor Cloud | Long-running background task |

---

## Jules Integration Best Practices

### Creating Sessions via API

**CRITICAL**: For Jules to auto-create PRs, these parameters are essential:

```json
{
  "automationMode": "AUTO_CREATE_PR",
  "requirePlanApproval": false,
  "metadata": {
    "labels": ["jules-pr", "ai-generated"]
  }
}
```

If `requirePlanApproval` is `true` (default), the session will wait for manual approval and **never create a PR**.

### Prompts for Jules

When delegating to Jules, prompts MUST be:

1. **Clear and unambiguous** - State exactly what needs to be done
2. **Contextual** - Provide repository, branch, and relevant file paths
3. **Actionable** - Include specific success criteria
4. **Self-contained** - Jules should NOT need to ask follow-up questions

**Example prompt structure:**
```
## Task: [Clear title]

### Context
- Repository: owner/repo
- Branch: feature-branch
- Files: path/to/relevant/files

### Problem
[Describe what's wrong or what needs to change]

### Requirements
1. [Specific requirement]
2. [Specific requirement]

### Success Criteria
- [ ] All tests pass
- [ ] Lint passes
- [ ] PR created with labels: jules-pr, bug-fix
```

### Managing Sessions

| State | Action |
|-------|--------|
| `PLANNING` | Approve with `approvePlan` or send feedback |
| `IN_PROGRESS` | Monitor or send message to guide |
| `COMPLETED` | Check for PR URL, close issue if resolved |
| `FAILED` | Analyze failure, retry with better prompt |

### Orphaned Sessions

Sessions that complete without PRs are "orphaned". Common causes:
- `requirePlanApproval: true` (waiting forever)
- Invalid source context
- Plan rejected or timed out

**Check for orphans:**
```bash
# Sessions completed without PRs
curl "https://jules.googleapis.com/v1alpha/sessions" \
  -H "X-Goog-Api-Key: $JULES_KEY" | \
  jq '.sessions[] | select(.state=="COMPLETED" and .pullRequestUrl==null)'
```

---

## Quality Checklist

Before completing work:

- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Conventional commit message used
- [ ] Documentation updated if needed
- [ ] Memory bank updated for handoff
