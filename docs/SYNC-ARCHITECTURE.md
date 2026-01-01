# Ecosystem Sync Architecture

This document describes how configuration, settings, and workflows propagate across the jbcom enterprise.

## Overview

```
jbcom/control-center (THE PROGENITOR)
│
├── Phase 0: ENTERPRISE ORG SETTINGS
│   enterprise/settings.json → jbcom org API
│
├── Phase 1a: ORG .GITHUB REPOS (settings inheritance)
│   repository-files/org-github-repo/settings.yml → org/.github repos
│   ↓ repository-settings/app
│   ALL repos in each org inherit these defaults
│   Individual repos can OVERRIDE with their own settings.yml
│
├── Phase 1b: GLOBAL SYNC (direct to all repo roots)
│   global-sync/* → ALL repos .github/, agents/, etc.
│   Control-centers USE these (not distribute)
│
└── Phase 1c-3: CASCADE SYNC (through org control-centers)
    repository-files/* → org/control-center/repository-files/
    ↓ org control-center sync workflow
    org/* repos
```

## Settings Inheritance via repository-settings/app

The [repository-settings/app](https://github.com/apps/settings) is installed on all organizations and enables:

### Hierarchy

```
org/.github/settings.yml     ← Organization defaults (all repos inherit)
  │
  └── repo/.github/settings.yml  ← Repo-specific overrides
```

### What Can Be Configured

- **Repository settings**: merge strategies, branch deletion, security features
- **Rulesets**: branch protection, merge queue, code scanning
- **Environments**: deployment environments with protection rules
- **Labels**: organization-wide label standards
- **Teams/Collaborators**: access control

### Example: Game-Specific Override

`arcade-cabinet/otterblade-odyssey/.github/settings.yml`:
```yaml
# Inherit org defaults, override specific settings
_extends: .github

# Custom environment for this game
environments:
  - name: release
    wait_timer: 0
    reviewers:
      - id: 12345
        type: Team
    deployment_branch_policy:
      protected_branches: true

# Additional ruleset for E2E gate
rulesets:
  - name: Release Gate
    target: branch
    enforcement: active
    conditions:
      ref_name:
        include: ["~DEFAULT_BRANCH"]
    rules:
      - type: required_status_checks
        parameters:
          required_status_checks:
            - context: "E2E Tests"
```

## Sync Types

### 1. Enterprise Org Settings (`enterprise/settings.json`)

**Target**: jbcom organization API settings  
**Method**: Direct API call to `/orgs/jbcom`  
**Frequency**: On push to enterprise/ or scheduled  

Configures organization-level settings like:
- Default repository permissions
- Member repository creation rights
- Security feature defaults

### 2. Org .github Repos (`repository-files/org-github-repo/`)

**Target**: `{org}/.github/settings.yml` in each organization  
**Method**: INITIAL sync only (won't overwrite if exists)  
**Effect**: All repos in org inherit these settings via repository-settings/app  

This is where merge queues, branch protection, and other repo-level settings are defined as organization defaults.

### 3. Global Sync (`global-sync/`)

**Target**: Root of ALL repos across ALL orgs  
**Method**: Direct file copy to repo root  
**What**: AI workflows, ecosystem workflows, agent configs  

Files here go directly to:
- `.github/workflows/ai-*.yml`
- `.github/workflows/ecosystem-*.yml`
- `.github/agents/*`
- `.github/actions/agentic-*`

Control-centers receive these to USE them (not redistribute).

### 4. Cascade Sync (`repository-files/`)

**Target**: Org control-center `repository-files/` directories  
**Method**: Copy to control-center, then control-center syncs to org repos  
**What**: Org-specific configs that cascade down  

Subdirectories:
- `always-sync/` - Overwrite on every sync
- `initial-only/` - Only create if missing
- `org-control-center/` - Control-center workflow template

## Merge Queue Configuration

Merge queues are configured at the REPOSITORY level via rulesets in `settings.yml`:

```yaml
rulesets:
  - name: Main Branch Protection
    target: branch
    enforcement: active
    conditions:
      ref_name:
        include: ["~DEFAULT_BRANCH"]
    rules:
      - type: merge_queue
        parameters:
          check_response_timeout_minutes: 60
          grouping_strategy: ALLGREEN
          max_entries_to_build: 5
          max_entries_to_merge: 5
          merge_method: SQUASH
          min_entries_to_merge: 1
          min_entries_to_merge_wait_minutes: 5
```

This is placed in `org/.github/settings.yml` to apply to all repos, or in individual repos to override.

## Phase Execution Order

```
Phase 0:  Enterprise org settings (API)
          │
          ├──→ Phase 1a: Org .github repos (INITIAL sync)
          │         ↓
          │    repository-settings/app applies to all repos
          │
          ├──→ Phase 1b: Global sync (DIRECT to all repos)
          │         ↓
          │    AI/ecosystem workflows in all repo roots
          │
          └──→ Phase 1c: Ensure org control-centers exist
                    │
                    ↓
               Phase 2: Sync to org control-center repository-files/
                    │
                    ↓
               Phase 3: Trigger org control-center cascade
                    │
                    ↓
               Org repos receive cascaded files
```

Phases 1a, 1b, and 1c run in PARALLEL after Phase 0.

## Adding a New Organization

1. Add org name to `MANAGED_ORGS` in ecosystem-sync.yml
2. Add org to target_org choice options
3. Run ecosystem-sync workflow
4. Workflow will:
   - Create `org/.github` repo with settings.yml
   - Create `org/control-center` repo
   - Sync all files appropriately

## Troubleshooting

### Settings not applying to repo

1. Check if repository-settings app is installed on the org
2. Verify `org/.github/settings.yml` exists and is valid YAML
3. Check repo's own `.github/settings.yml` for overrides
4. Look at repository-settings app delivery logs

### Workflows not appearing in repo

1. Check if repo is in the correct org
2. Verify global-sync contains the workflow
3. Run ecosystem-sync manually with dry_run=false
4. Check git history for sync commits

### Merge queue not working

1. Verify ruleset is in settings.yml with `type: merge_queue`
2. Check that PR branch protection allows merge queue
3. Ensure CI checks are passing (merge queue requires green checks)
