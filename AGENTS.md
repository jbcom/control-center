# Agent Instructions for Control Center

## Overview

**jbcom/control-center** is the unified orchestration hub for the jbcom ecosystem. It manages:
- Cross-repository CI/CD coordination
- Ecosystem file synchronization
- AI agent fleet management
- Multi-organization infrastructure

## Quick Start

```bash
# Read current context
cat memory-bank/activeContext.md

# Check ecosystem status
gh pr list --state open
gh issue list --state open
```

## Ecosystem Scope

### Organizations Managed

| Organization | Domain | Purpose | Repos |
|-------------|--------|---------|-------|
| `jbcom` | jonbogaty.com | Control center, games, portfolio | 9 |
| `strata-game-library` | strata.game | Procedural 3D graphics library | 9 |
| `agentic-dev-library` | agentic.dev | AI agent orchestration | 6 |
| `extended-data-library` | extendeddata.dev | Enterprise data utilities | 6 |

### Repository Structure

```
control-center/
├── .github/
│   └── workflows/           # Ecosystem workflows
│       ├── ecosystem-curator.yml      # Nightly triage
│       ├── ecosystem-harvester.yml    # PR monitoring
│       ├── ecosystem-sage.yml         # On-call advisor
│       ├── ecosystem-reviewer.yml     # PR review
│       ├── ecosystem-fixer.yml        # CI auto-fix
│       └── ecosystem-delegator.yml    # Agent delegation
├── memory-bank/             # AI context and history
├── repository-files/        # Files synced to all repos
│   └── always-sync/         # Always overwrite
├── scripts/                 # Orchestration scripts
└── strata/                  # Strata-specific config
```

## Ecosystem Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ecosystem-curator` | Nightly (2 AM UTC) | Scan repos, triage issues/PRs, spawn agents |
| `ecosystem-harvester` | Every 15 min | Monitor agents, merge PRs, request reviews |
| `ecosystem-sage` | `@sage`, `/sage` | Answer questions, decompose tasks |
| `ecosystem-reviewer` | PR events | Per-PR lifecycle: review, feedback, fixes |
| `ecosystem-fixer` | CI failure | Auto-resolve CI failures |
| `ecosystem-delegator` | `/jules`, `/cursor` | Delegate issues to AI agents |

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
