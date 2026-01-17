# Ecosystem Sync Architecture

This document describes how configuration, settings, and workflows propagate across the jbcom enterprise.

## Overview

```
jbcom/control-center (THE PROGENITOR)
│
├── Phase 0: ENTERPRISE ORG SETTINGS
│   enterprise/settings.json → jbcom org API
│
└── Phase 1: SYNC FILES (direct to all repo roots)
    sync-files/always-sync/global/* → ALL repos .github/, agents/, etc.
    sync-files/always-sync/{lang}/* → Language specific repos
    sync-files/initial-only/* → One-time templates
```

## Release-Triggered Sync

When a new version of control-center is released:

1. **Release Workflow** creates Go binaries, Docker images, and action tags
2. **Ecosystem Sync** is automatically triggered (see `.github/workflows/release.yml`)
3. **Cascade Propagation** updates all managed organizations with:
   - New action version references
   - Updated Docker image tags
   - Latest Cursor rules and configurations

This ensures the entire ecosystem stays synchronized with the latest control-center release.

**See**: [`docs/RELEASE-PROCESS.md`](./RELEASE-PROCESS.md) for complete release details.

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

### 2. Org .github Repos (`sync-files/initial-only/org-github-repo/`)

**Target**: `{org}/.github/settings.yml` in each organization  
**Method**: INITIAL sync only (won't overwrite if exists)  
**Effect**: All repos in org inherit these settings via repository-settings/app  

This is where merge queues, branch protection, and other repo-level settings are defined as organization defaults.

### 3. Unified Sync (`sync-files/`)

**Target**: Root of managed repos
**Method**: Direct file copy using `repo-file-sync-action`
**What**: All configuration, workflows, and templates

Files in `sync-files/always-sync/global` go to ALL repos.
Files in `sync-files/always-sync/{ecosystem}` go to ecosystem-specific repos.

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
          └──→ Phase 1: File Sync (DIRECT to all repos)
                   ↓
              Settings, workflows, and configs applied
```

## Adding a New Organization

1. Add org name to `MANAGED_ORGS` in sync.yml
2. Add org to target_org choice options
3. Run sync workflow
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
2. Verify sync-files contains the workflow
3. Run sync manually with dry_run=false
4. Check git history for sync commits

### Merge queue not working

1. Verify ruleset is in settings.yml with `type: merge_queue`
2. Check that PR branch protection allows merge queue
3. Ensure CI checks are passing (merge queue requires green checks)
