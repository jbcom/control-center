# Agent Instructions for Control Center

## Overview

**jbcom/control-center** is the unified orchestration hub for the jbcom ecosystem. It manages:
- Cross-repository CI/CD coordination
- Ecosystem file synchronization
- AI agent fleet management
- Multi-organization infrastructure
- **Reusable AI-powered workflows** callable from any repository

## Quick Start

```bash
# Read current context
cat memory-bank/activeContext.md

# Check ecosystem status
gh pr list --state open
gh issue list --state open
```

---

## 🚀 Using Control Center from Other Repositories

Any repository can leverage the control center's AI capabilities by:
1. **Calling reusable workflows** via `workflow_call`
2. **Using AI triggers** in issue/PR comments

### Step 1: Configure Required Secrets

Add these secrets to your repository (Settings → Secrets and variables → Actions):

| Secret | Required | How to Get |
|--------|----------|------------|
| `CI_GITHUB_TOKEN` | **Always** | Create PAT with `repo`, `workflow` scopes. **Required for cross-repo triggers.** |
| `ANTHROPIC_API_KEY` | For Claude | From [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_JULES_API_KEY` | For Jules | From Google Cloud Console |
| `OLLAMA_API_KEY` | For Ollama | From [ollama.com](https://ollama.com) |
| `CURSOR_API_KEY` | For Cursor | From Cursor dashboard |

### Step 2: Create Workflow Files

Create these files in your repository's `.github/workflows/` directory:

#### AI-Powered PR Review (`ai-review.yml`)
```yaml
name: AI Review
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]

jobs:
  review:
    uses: jbcom/control-center/.github/workflows/ecosystem-reviewer.yml@main
    with:
      pr_number: ${{ github.event.pull_request.number }}
      repository: ${{ github.repository }}
      model_tier: 'ollama'  # ollama (fast), claude (thorough), jules (refactor), all
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
```

#### Auto-Fix CI Failures (`ci-fixer.yml`)
```yaml
name: CI Fixer
on:
  workflow_run:
    workflows: ["CI", "Build", "Test", "Lint"]
    types: [completed]
    branches-ignore: [main]

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

#### AI Issue Delegation (`delegate.yml`)
```yaml
name: AI Delegation
on:
  issue_comment:
    types: [created]

jobs:
  delegate:
    if: |
      github.event.issue.pull_request == null &&
      (contains(github.event.comment.body, '/jules') ||
       contains(github.event.comment.body, '/cursor') ||
       contains(github.event.comment.body, '@claude'))
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

#### Sage Q&A Advisor (`sage.yml`)
```yaml
name: Sage Advisor
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

jobs:
  sage:
    if: |
      contains(github.event.comment.body, '@sage') ||
      contains(github.event.comment.body, '/sage')
    uses: jbcom/control-center/.github/workflows/ecosystem-sage.yml@main
    with:
      query: ${{ github.event.comment.body }}
      context_repo: ${{ github.repository }}
      context_issue: ${{ github.event.issue.number || github.event.pull_request.number }}
    secrets:
      CI_GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
      OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
      GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
```

### Step 3: Use AI Triggers

Once configured, use these commands in issue or PR comments:

| Command | Agent | What It Does |
|---------|-------|--------------|
| `/jules Implement feature X` | Google Jules | Creates a PR with the implementation |
| `/cursor Fix the failing tests` | Cursor Cloud | Long-running fix with IDE context |
| `@claude Analyze this bug` | Claude Code | Deep analysis, implements fix, creates PR |
| `@sage How do I...?` | Ollama | Quick answer posted as comment |
| `/sage Explain this code` | Ollama | Code explanation posted as comment |

### Example Usage

```markdown
<!-- In an issue comment -->
/jules Please add input validation to the User model.
Check the existing patterns in models/base.py.

<!-- In a PR comment -->
@claude The tests are failing. Please analyze the error
and fix the root cause.

<!-- Quick question -->
@sage What's the best way to handle async errors in this codebase?
```

---

## Agentic Ecosystem Architecture

For a detailed breakdown of the `agentic` ecosystem, including repository scope, ownership, and technical architecture, please see the canonical documentation:

- **[Agentic Ecosystem Architecture](docs/agentic-ecosystem.md)**

## Ecosystem Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ecosystem-curator` | Nightly (2 AM UTC) | Scan repos, triage issues/PRs, spawn agents |
| `ecosystem-harvester` | Every 15 min | Monitor agents, merge PRs, request reviews |
| `ecosystem-sage` | `@sage`, `/sage` | Answer questions, decompose tasks |
| `ecosystem-reviewer` | PR events | Per-PR lifecycle: review, feedback, fixes |
| `ecosystem-fixer` | CI failure | Auto-resolve CI failures |
| `ecosystem-delegator` | `/jules`, `/cursor` | Delegate issues to AI agents |
| `jules-completion-handler` | Webhook | Posts Jules session results to PRs/issues |

## Available AI Agents

| Agent | Trigger | Use Case |
|-------|---------|----------|
| **Cursor Cloud** | `@cursor` in PR/issue | Long-running tasks, full IDE context |
| **Google Jules** | `/jules` in issue | Async refactoring, multi-file changes |
| **Ollama** | Automatic | Code review, routing, quick fixes |
| **Gemini** | `/gemini review` | PR quality review |
| **Amazon Q** | `/q review` | Security review |

### Agent Orchestration Pattern

```
ISSUE → Task Router (Ollama) → [Ollama | Jules | Cursor] → PR → AI Review Swarm → Feedback Processor → Auto-merge
```

### Task Routing Matrix

| Task Type | Agent | Reason |
|-----------|-------|--------|
| Quick fix (<5 lines) | Ollama | Inline, fast |
| Code review | Ollama | Structured JSON |
| Multi-file refactor | Jules | Async, AUTO_CREATE_PR |
| Large feature (>100 lines) | Cursor Cloud | Full IDE context |
| Documentation | Jules | Full file context |
| Complex bug fix | Cursor Cloud | Debugging capability |

## Secrets Configuration

| Secret | Purpose |
|--------|---------|
| `${GITHUB_TOKEN}` | Repository access |
| `${CURSOR_API_KEY}` | Cursor Cloud Agent API |
| `${GOOGLE_JULES_API_KEY}` | Jules API (API key auth) |
| `${JULES_GITHUB_TOKEN}` | Jules GitHub operations |
| `${OLLAMA_API_KEY}` | Ollama Cloud API |
| `${CURSOR_SESSION_TOKEN}` | Cursor Background Composer Session Token |

## Secret Setup (Manual)

The following secrets must be configured in the repository settings by an admin:

- **JULES_GITHUB_TOKEN**: PAT with repository access for Jules.
- **CURSOR_API_KEY**: API key for Cursor Cloud Agent operations.
- **GOOGLE_JULES_API_KEY**: API key for Google Jules sessions.
- **OLLAMA_API_URL**: Set to `https://ollama.com/api`.
- **CURSOR_SESSION_TOKEN**: From `WorkosCursorSessionToken` cookie.

## Agent Communication

### Request Work
```bash
# In issue comment - delegate to Jules
/jules Please implement feature X following RFC-001

# In PR comment - delegate to Cursor
@cursor Rebase onto main, resolve conflicts, ensure CI passes, merge when ready
```

### Jules Session Management
```bash
# Set API key
export JULES_API_KEY="$JULES_API_KEY"

# List sessions
python -c "
from vendor_connectors.google.jules import JulesConnector
c = JulesConnector()
for s in c.list_sessions(): print(f'{s.state}: {s.title}')"

# Approve pending plan
python -c "
from vendor_connectors.google.jules import JulesConnector
c = JulesConnector()
c.approve_plan('sessions/SESSION_ID')"
```

### Cursor Cloud Agent
```bash
# Via GitHub comment (preferred)
gh pr comment <PR> --body "@cursor <instructions>"

# Via API
curl -X POST "https://api.cursor.com/v0/agents" \
  -u "$CURSOR_API_KEY:" \
  -H "Content-Type: application/json" \
  -d '{"prompt":{"text":"..."},"source":{"repository":"..."}}'
```

## Session Management

### Start of Session
```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md | tail -100
gh issue list --label agent-session
```

### End of Session
```bash
echo "## Session: $(date +%Y-%m-%d)" >> memory-bank/activeContext.md
# Document: what was done, decisions made, blockers
```

## Key Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI assistant guidance |
| `AGENTS.md` | This file |
| `memory-bank/activeContext.md` | Current state |
| `memory-bank/progress.md` | Session history |
| `memory-bank/ECOSYSTEM-SESSION-*.md` | Comprehensive session docs |
| `docs/ECOSYSTEM.md` | Workflow documentation |

## GitHub Authentication

```bash
# Always use this pattern for jbcom repos
GH_TOKEN="$GITHUB_TOKEN" gh <command>
```

## Related Packages

### @agentic Ecosystem
- `@agentic/triage` - Pure AI primitives (Zod schemas, Vercel AI SDK tools)
- `@agentic/control` - Orchestration layer (depends on triage)

### Python Vendor Connectors
- `vendor-connectors` - API clients for Jules, Cursor, GitHub, Slack, Vault, Zoom

## Current EPICs

- **#422** - Unified Multi-Agent Orchestrator
- **#427** - @agentic Package Architecture
- **#428** - Bulk Delegation Session
- **#449** - Jules Installation on New Orgs

## Quality Checklist

Before completing work:
- [ ] All tests pass
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Conventional commit message format
- [ ] Memory bank updated with session notes

---

## Agent Autonomy Policy

### YOU HAVE FULL AUTONOMY

When assigned to a PR or issue, you are **explicitly authorized** to:

1. **PUSH** - `git push` and `git push --force-with-lease` to update PRs
2. **REBASE** - Rebase onto main/master to resolve conflicts
3. **FIX** - Make any changes needed to pass CI checks
4. **MERGE** - Merge PRs using squash merge when CI is green
5. **CREATE** - Create new branches, files, and PRs as needed

### DO NOT ASK FOR PERMISSION

- You do NOT need to ask before pushing
- You do NOT need to ask before merging
- You do NOT need to ask before force-pushing
- Execute immediately when given instructions

### Standard Instruction Pattern

When you see `@cursor` or `@jules` followed by instructions, execute them immediately:

```
@cursor Rebase onto main, fix conflicts, merge when CI passes
```

This means: Do it now. Don't ask. You have permission.

### Authentication

You have write access via:
- `GITHUB_TOKEN` / `GH_TOKEN` environment variable
- Configured git credentials
- GitHub App installation tokens

Use these to push, merge, and manage PRs.
