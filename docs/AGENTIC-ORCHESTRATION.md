# Agentic Orchestration Architecture

## Overview

This document describes the bidirectional agent coordination system between the **control plane** (jbcom-control-center) and **managed repositories**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                                     │
│                 jbcom-control-center                                 │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Agentic    │───▶│ Decomposer   │───▶│  Dispatcher  │          │
│  │    Cycle     │    │              │    │              │          │
│  │   (Issue)    │    │ Break down   │    │ Create repo  │          │
│  └──────────────┘    │ to repo tasks│    │ issues/PRs   │          │
│         ▲            └──────────────┘    └──────────────┘          │
│         │                                       │                   │
│         │            ┌──────────────┐           │                   │
│         └────────────│  Aggregator  │◀──────────┼───────────────┐  │
│                      │              │           │               │  │
│                      │ Collect repo │           │               │  │
│                      │ status/PRs   │           │               │  │
│                      └──────────────┘           │               │  │
└─────────────────────────────────────────────────┼───────────────┼──┘
                                                  │               │
                    ┌─────────────────────────────┼───────────────┼──┐
                    │           MANAGED REPOS     │               │  │
                    │                             ▼               │  │
                    │  ┌─────────────────────────────────────┐   │  │
                    │  │      jbcom/extended-data-types      │   │  │
                    │  │  ┌─────────┐  ┌─────────┐           │   │  │
                    │  │  │ CLAUDE  │  │ Claude  │──────────────────┘
                    │  │  │   .md   │  │Workflows│  Feedback │   │
                    │  │  └─────────┘  └─────────┘           │   │
                    │  └─────────────────────────────────────┘   │
                    │                                             │
                    │  ┌─────────────────────────────────────┐   │
                    │  │        jbcom/lifecyclelogging       │   │
                    │  │  ┌─────────┐  ┌─────────┐           │   │
                    │  │  │ CLAUDE  │  │ Claude  │───────────────┘
                    │  │  │   .md   │  │Workflows│  Feedback │
                    │  │  └─────────┘  └─────────┘           │
                    │  └─────────────────────────────────────┘
                    │                                             
                    │  ┌─────────────────────────────────────┐
                    │  │       jbcom/vendor-connectors       │
                    │  │  ┌─────────┐  ┌─────────┐           │
                    │  │  │ CLAUDE  │  │ Claude  │
                    │  │  │   .md   │  │Workflows│
                    │  │  └─────────┘  └─────────┘           │
                    │  └─────────────────────────────────────┘
                    └─────────────────────────────────────────────┘
```

## Agentic Cycle Lifecycle

### Phase 1: Cycle Initiation
1. Control plane creates "Agentic Cycle" issue with goals
2. Decomposer analyzes and breaks into repo-specific tasks
3. Dispatcher creates issues in target repos

### Phase 2: Distributed Execution
1. Each repo's Claude workflows pick up issues
2. Agents work independently on their tasks
3. PRs are created in each repo
4. Progress updates flow back to control plane

### Phase 3: Aggregation
1. Control plane monitors all repo activity
2. Collects PR statuses, CI results
3. Updates cycle issue with progress
4. Identifies blockers, dependencies

### Phase 4: Completion
1. All repo PRs merged
2. Control plane verifies ecosystem health
3. Cycle issue closed with summary
4. Next cycle can begin

## Communication Mechanisms

### Control Plane → Repos (Dispatch)
- GitHub Issues with `agent-task` label
- Issue body contains:
  - Task description
  - Success criteria
  - Related issues in other repos
  - Link back to control plane cycle

### Repos → Control Plane (Feedback)
- Cross-repo issue mentions: `See jbcom/jbcom-control-center#123`
- PR descriptions linking to cycle
- Claude comments on cycle issue
- Workflow dispatch events

### Station-to-Station (Repo to Repo)
- Dependency PRs link to each other
- Coordinated merges (foundation first)
- Issue cross-references

## Standardized Repo Setup

Each managed repo receives:

```
repo/
├── CLAUDE.md              # Project context for Claude
├── .claude/
│   └── commands/          # Custom slash commands
│       ├── label-issue.md
│       └── review-pr.md
├── .github/
│   └── workflows/
│       ├── claude.yml           # @claude mentions
│       ├── claude-pr-review.yml # Auto PR review
│       └── claude-issue-triage.yml
└── .cursor/
    └── rules/             # Cursor-specific rules (optional)
```

## Cycle Issue Template

```markdown
# 🔄 Agentic Cycle: [CYCLE_NAME]

**Started**: YYYY-MM-DD
**Status**: 🟡 In Progress | 🟢 Complete | 🔴 Blocked

## Goals
- [ ] Goal 1
- [ ] Goal 2

## Decomposed Tasks

### extended-data-types
- [ ] Issue #X: Task description

### lifecyclelogging  
- [ ] Issue #X: Task description

### vendor-connectors
- [ ] Issue #X: Task description

## Progress Updates
<!-- Claude will update this section -->

## Blockers
<!-- Any issues blocking progress -->

## Completion Criteria
- [ ] All repo PRs merged
- [ ] All CI green
- [ ] PyPI releases successful
- [ ] No regressions
```

## Workflows

### 1. Cycle Dispatch Workflow
Triggered when cycle issue is created:
- Parses issue body for tasks
- Creates issues in target repos
- Updates cycle issue with links

### 2. Cycle Aggregation Workflow  
Runs on schedule or dispatch:
- Queries all repo issues/PRs
- Updates cycle issue status
- Detects blockers

### 3. Repo Feedback Workflow
In each managed repo:
- When PR merged, comments on control plane
- When blocked, notifies control plane
- Cross-links related work

## Benefits Over Holding PRs

| Holding PRs | Agentic Cycles |
|-------------|----------------|
| Session dies when merged | Cycles persist across sessions |
| Single agent bottleneck | Distributed parallel work |
| No visibility into progress | Structured progress tracking |
| Manual coordination | Automated orchestration |
| Branch pollution | Clean issue-based tracking |

## Implementation Priority

1. ✅ Standardized Claude tooling (CLAUDE.md, workflows)
2. 🔲 Sync workflow to push tooling to repos
3. 🔲 Cycle dispatch workflow
4. 🔲 Cycle aggregation workflow
5. 🔲 Repo feedback workflows
6. 🔲 Station-to-station coordination
