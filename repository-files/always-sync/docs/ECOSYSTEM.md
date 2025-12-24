# Ecosystem Workflows

The **Ecosystem** is a unified family of GitHub Actions workflows that provide autonomous development operations for the jbcom organization.

## Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **ecosystem-curator** | Nightly (2 AM UTC) | Scan repos, triage issues/PRs, spawn agents |
| **ecosystem-harvester** | Every 15 min | Monitor agents, merge PRs, request reviews |
| **ecosystem-sage** | On-call (`@sage`, `/sage`) | Answer questions, decompose tasks, unblock |
| **ecosystem-reviewer** | PR events | Per-PR lifecycle: review, feedback, fixes |
| **ecosystem-fixer** | CI failure | Auto-resolve CI failures on branches |
| **ecosystem-delegator** | `/jules`, `/cursor` | Delegate issues to AI agents |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ECOSYSTEM ORCHESTRATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
│  │   CURATOR   │────▶│  HARVESTER  │────▶│    SAGE     │        │
│  │  (Nightly)  │     │ (15 min)    │     │ (On-call)   │        │
│  └─────────────┘     └─────────────┘     └─────────────┘        │
│         │                   │                   │                │
│         │ spawn             │ monitor           │ advise         │
│         ▼                   ▼                   ▼                │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              AI AGENT POOL                           │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │        │
│  │  │  Jules   │  │  Cursor  │  │  Ollama  │           │        │
│  │  │ (Google) │  │  (Cloud) │  │  (LLM)   │           │        │
│  │  └──────────┘  └──────────┘  └──────────┘           │        │
│  └─────────────────────────────────────────────────────┘        │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              PER-PR AUTOMATION                       │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │        │
│  │  │ REVIEWER │  │  FIXER   │  │DELEGATOR │           │        │
│  │  │ (PR Ops) │  │ (CI Fix) │  │ (Issue)  │           │        │
│  │  └──────────┘  └──────────┘  └──────────┘           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### Ecosystem Curator

**Schedule:** Nightly at 2 AM UTC  
**File:** `.github/workflows/ecosystem-curator.yml`  
**Script:** `scripts/ecosystem-curator.mjs`

Performs a full ecosystem scan:
1. Discovers all repositories in the organization
2. Triages open issues:
   - Complex issues → Spawn Jules session
   - Quick fixes → Spawn Cursor agent
   - Questions → Resolve with Ollama
3. Processes open PRs:
   - Failed CI → Spawn fixer agent
   - Blocking reviews → Address feedback
   - Ready → Auto-merge
4. Monitors running agents and Jules sessions
5. Reports statistics to workflow summary

### Ecosystem Harvester

**Schedule:** Every 15 minutes  
**File:** `.github/workflows/ecosystem-harvester.yml`  
**Script:** `scripts/ecosystem-harvester.mjs`

Fast-cadence monitoring loop:
1. Checks all running Cursor agents
2. Checks all active Jules sessions
3. Processes completed agent results
4. Auto-merges PRs that meet criteria:
   - All CI checks pass
   - No blocking reviews
   - Not in draft
5. Requests reviews from AI reviewers (Gemini, Amazon Q)

### Ecosystem Sage

**Trigger:** `@sage` or `/sage` in comments, `workflow_call`, `workflow_dispatch`  
**File:** `.github/workflows/ecosystem-sage.yml`  
**Script:** `scripts/ecosystem-sage.mjs`

On-call intelligent advisor:
1. Classifies query type (REVIEW, QUESTION, FIX, IMPLEMENT, etc.)
2. Gathers codebase context
3. Generates intelligent response using Ollama
4. Decomposes complex tasks
5. Spawns agents if recommended

### Ecosystem Reviewer

**Trigger:** PR events (`opened`, `synchronize`, `ready_for_review`), review events  
**File:** `.github/workflows/ecosystem-reviewer.yml`

Per-PR lifecycle management:
1. Automatic code review on PR open
2. Monitors ALL AI agent feedback (Gemini, Copilot, Q, CodeRabbit, etc.)
3. Analyzes, triages, and resolves feedback automatically
4. Applies fixes and commits them
5. Resolves comment threads
6. Removes draft status when ready
7. Auto-merges when all feedback satisfied and CI green

### Ecosystem Fixer

**Trigger:** CI failure on non-main branches  
**File:** `.github/workflows/ecosystem-fixer.yml`

CI failure auto-resolution:
1. Detects CI failures
2. Parses error logs
3. Generates fixes using Ollama
4. Commits and pushes fixes
5. Re-triggers CI

### Ecosystem Delegator

**Trigger:** `/jules` or `/cursor` in issue comments  
**File:** `.github/workflows/ecosystem-delegator.yml`

Manual issue delegation:
- `/jules <task>` - Delegate to Google Jules (complex refactors)
- `/cursor <task>` - Delegate to Cursor Cloud Agent (quick fixes)
- `/sage <question>` - Ask the Sage (handled by ecosystem-sage.yml)

## Configuration

### Required Secrets

| Secret | Purpose |
|--------|---------|
| `GOOGLE_JULES_API_KEY` | Google Jules API authentication |
| `JULES_GITHUB_TOKEN` | GitHub PAT for Jules operations |
| `CURSOR_API_KEY` | Cursor Cloud Agent API authentication |
| `CURSOR_GITHUB_TOKEN` | GitHub PAT for Cursor operations |
| `OLLAMA_API_KEY` | Ollama cloud API authentication |

### Required Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `https://ollama.com` | Ollama API endpoint |
| `OLLAMA_MODEL` | `glm-4.6:cloud` | LLM model for Ollama |

## Usage

### Delegating Issues

Comment on any issue to delegate:

```
/jules Refactor the authentication module to use OAuth2
```

```
/cursor Fix the failing test in src/__tests__/auth.test.ts
```

```
@sage What's the best approach for implementing caching here?
```

### Manual Triggers

All workflows support `workflow_dispatch` for manual testing:

```bash
# Run curator for a specific repo
gh workflow run ecosystem-curator.yml -f target_repo=nodejs-strata -f dry_run=true

# Ask the sage
gh workflow run ecosystem-sage.yml -f query="How does the ECS system work?"

# Run harvester
gh workflow run ecosystem-harvester.yml -f dry_run=true
```

## Monitoring

### GitHub Actions Summary

Each workflow writes a report to the Actions summary with statistics:
- Issues triaged
- Agents spawned
- PRs processed
- Errors encountered

### Agent Fleet Status

The Harvester reports agent status every 15 minutes:
- Total agents
- Running vs completed
- PRs created/merged
