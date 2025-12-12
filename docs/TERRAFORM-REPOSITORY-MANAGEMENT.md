# Terraform Repository Management

## Overview

As of December 2025, jbcom-control-center uses Terragrunt to actively manage repository configurations across all 18 jbcom repositories. This replaces the previous passive sync workflow approach.

## Why Terragrunt?

### Problems with Previous Approach

The previous sync workflow had several issues:

1. **Passive Management**: Used bash scripts in GitHub Actions to sync settings
2. **No State Management**: No tracking of actual vs. desired state
3. **Drift Detection**: No automated way to detect when repositories diverged
4. **Configuration Scattered**: Settings spread across multiple YAML files
5. **Limited Rollback**: Difficult to undo changes or review history
6. **No Preview**: Changes applied immediately without review

### Benefits of Terragrunt

1. **Active State Management**: Terraform tracks actual state vs. desired state
2. **Drift Detection**: Automatically detects when repositories diverge
3. **Plan Preview**: See exactly what will change before applying
4. **Version Control**: All configuration in code with full git history
5. **Rollback**: Easy to revert to previous configurations
6. **Declarative**: Describe desired state, not imperative steps
7. **DRY**: Shared module for all 18 repositories
8. **File Sync**: Cursor rules and workflows managed as Terraform resources

## Architecture

### Directory Structure

```
terragrunt-stacks/
├── terragrunt.hcl                    # Root config (provider, backend)
├── modules/
│   └── repository/main.tf            # Shared repository module
├── python/
│   ├── agentic-crew/terragrunt.hcl
│   ├── ai_game_dev/terragrunt.hcl
│   └── ...                           # 8 repos total
├── nodejs/
│   ├── agentic-control/terragrunt.hcl
│   └── ...                           # 6 repos total
├── go/
│   ├── port-api/terragrunt.hcl
│   └── vault-secret-sync/terragrunt.hcl
└── terraform/
    ├── terraform-github-markdown/terragrunt.hcl
    └── terraform-repository-automation/terragrunt.hcl

repository-files/
├── always-sync/                      # Overwritten every apply
│   ├── .cursor/rules/               # Cursor IDE rules
│   └── .github/workflows/           # Claude workflow
├── initial-only/                     # Created once, repos customize
│   ├── .cursor/                     # Environment config
│   └── docs/                        # Documentation scaffold
├── python/                           # Python-specific rules
├── nodejs/                           # Node.js-specific rules
├── go/                               # Go-specific rules
└── terraform/                        # Terraform-specific rules
```

### State Storage

- **Backend**: HCP Terraform (Terraform Cloud) - secure encrypted remote state
- **Organization**: `jbcom`
- **Workspaces**: `jbcom-repo-{repo-name}` (auto-generated per repository)
- **Security**: State is encrypted at rest, secrets never stored locally in plaintext
- **Authentication**: Uses `TF_API_TOKEN` secret via `TF_TOKEN_app_terraform_io` environment variable
- **Import**: Uses Terraform 1.5+ import blocks for zero-destroy import

### Repository Categories

Repositories are managed in 4 language categories:

| Category | Count | Repos |
|----------|-------|-------|
| **Python** | 8 | agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors |
| **Node.js** | 6 | agentic-control, otter-river-rush, otterfall, pixels-pygame-palace, rivermarsh, strata |
| **Go** | 2 | port-api, vault-secret-sync |
| **Terraform** | 2 | terraform-github-markdown, terraform-repository-automation |

## What's Managed

### Repository Settings (`github_repository`)
- Merge strategies (squash only, delete branch on merge)
- Feature flags (issues enabled, wiki/projects/discussions disabled by default)
- Visibility (public)
- Auto-merge settings
- Vulnerability alerts

### Branch Protection (`github_branch_protection`)
- Pull request requirements
- Review dismissal settings
- Linear history enforcement
- Force push protection
- Deletion protection

### Security Settings (`security_and_analysis` block)
- Secret scanning (enabled)
- Secret scanning push protection (enabled)

### GitHub Pages (`pages` block)
- Enabled for all repositories
- Build type: GitHub Actions workflow

### File Sync (`github_repository_file`)
- **Always-sync files**: Cursor rules, Claude workflow (overwritten every apply)
- **Initial-only files**: Docs scaffold, environment config (created once)
- **Language-specific rules**: Python, Node.js, Go, Terraform rules

### Secrets (`github_actions_secret`)
- **All repository secrets** managed via Terraform
- Syncs: CI_GITHUB_TOKEN, PYPI_TOKEN, NPM_TOKEN, DOCKERHUB_USERNAME, DOCKERHUB_TOKEN, ANTHROPIC_API_KEY
- Secrets passed as TF_VAR_* environment variables from terraform-sync.yml workflow
- Only non-empty secrets are synced

## Usage

### Plan All Repositories

```bash
cd terragrunt-stacks
terragrunt run-all plan --non-interactive
```

### Apply All Repositories

```bash
cd terragrunt-stacks
terragrunt run-all apply --non-interactive
```

### Plan Single Repository

```bash
cd terragrunt-stacks/python/agentic-crew
terragrunt plan
```

### Apply Single Repository

```bash
cd terragrunt-stacks/python/agentic-crew
terragrunt apply
```

## Workflow Automation

The GitHub Actions workflow (`terraform-sync.yml`) handles:

| Event | Action |
|-------|--------|
| Pull Request | Plan only (shows changes) |
| Push to main | Apply changes |
| Schedule (2 AM UTC) | Drift detection |
| Manual dispatch | Plan or apply |

## Configuration

### Repository Unit Configuration

Each repository has a `terragrunt.hcl` that specifies inputs:

```hcl
# terragrunt-stacks/nodejs/agentic-control/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/repository"
}

inputs = {
  name            = "agentic-control"
  language        = "nodejs"
  has_wiki        = false
  has_discussions = false
  has_pages       = true
  sync_files      = true
}
```

### Available Variables

#### Repository Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | string | required | Repository name |
| `language` | string | required | python, nodejs, go, terraform |
| `visibility` | string | "public" | Repository visibility |
| `has_issues` | bool | true | Enable Issues |
| `has_wiki` | bool | false | Enable Wiki |
| `has_discussions` | bool | false | Enable Discussions |
| `has_pages` | bool | true | Enable GitHub Pages |
| `allow_squash_merge` | bool | true | Allow squash merging |
| `allow_merge_commit` | bool | false | Allow merge commits |
| `allow_rebase_merge` | bool | false | Allow rebase merging |
| `delete_branch_on_merge` | bool | true | Delete branch after merge |
| `allow_auto_merge` | bool | false | Enable auto-merge |
| `vulnerability_alerts` | bool | true | Enable Dependabot alerts |
| `sync_files` | bool | true | Sync Cursor rules/workflows |

#### Main Branch Protection

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `default_branch` | string | "main" | Default branch name |
| `required_approvals` | number | 0 | Required PR approvals |
| `dismiss_stale_reviews` | bool | false | Dismiss stale reviews |
| `require_code_owner_reviews` | bool | false | Require CODEOWNERS |
| `require_last_push_approval` | bool | false | Require approval after last push |
| `required_linear_history` | bool | false | Require linear history |
| `require_signed_commits` | bool | false | Require signed commits |
| `require_conversation_resolution` | bool | true | Require conversation resolution |
| `allow_force_pushes` | bool | false | Allow force pushes |
| `allow_deletions` | bool | false | Allow deletions |
| `lock_branch` | bool | false | Lock branch (read-only) |
| `required_status_checks_strict` | bool | false | Require up-to-date branches |
| `required_status_checks_contexts` | list(string) | [] | Required status checks |

#### Feature Branch Protection

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `feature_branch_patterns` | list(string) | [] | Branch patterns (e.g., ["feature/*"]) |
| `feature_required_approvals` | number | 0 | Required approvals for features |
| `feature_required_status_checks_contexts` | list(string) | [] | Required status checks |
| `feature_allow_force_pushes` | bool | false | Allow force pushes |
| `feature_allow_deletions` | bool | true | Allow deletions |

## Branch Protection Best Practices

### Main vs Feature Branch Strategy

Following industry best practices (Mergify, GitHub, 2024), we implement **separate protection rules** for main and feature branches:

#### Main Branch - Strict Protection
- **Purpose**: Production-ready code requiring maximum protection
- **Strategy**: Strictest rules to ensure code quality
- **Recommended Settings**:
  - ✅ `require_conversation_resolution = true` - All discussions resolved
  - ✅ `required_approvals = 1` (or more) - Peer review required
  - ✅ `required_status_checks_contexts` - CI must pass
  - ✅ `allow_force_pushes = false` - Protect history
  - ✅ `allow_deletions = false` - Prevent accidental loss
  - ⚠️ `required_linear_history = false` - Allow merge commits (optional)

#### Feature Branches - Lighter Protection
- **Purpose**: Development, testing, experimentation
- **Strategy**: Balance protection with developer velocity
- **Patterns**: `feature/*`, `bugfix/*`, `hotfix/*`, `release/*`
- **Recommended Settings**:
  - ✅ `require_conversation_resolution = true` - Keep discussions resolved
  - ⚠️ `feature_required_approvals = 0` - No reviews required (can enable)
  - ✅ `feature_allow_deletions = true` - Allow cleanup after merge
  - ⚠️ `feature_allow_force_pushes = false` - Protect shared branches

### Example Configuration

```hcl
# terragrunt-stacks/nodejs/strata/terragrunt.hcl
inputs = {
  name     = "strata"
  language = "nodejs"
  
  # Main branch - strict protection
  require_conversation_resolution = true
  required_approvals              = 1
  required_status_checks_contexts = ["ci/build", "ci/test"]
  allow_force_pushes              = false
  
  # Feature branches - lighter protection
  feature_branch_patterns = [
    "feature/*",
    "bugfix/*",
    "hotfix/*",
    "release/*"
  ]
  feature_allow_deletions    = true
  feature_allow_force_pushes = false
}
```

### Merge Queue Compatibility

For repositories using GitHub merge queues:
1. Configure CI workflows to trigger on `merge_group` event
2. Set `required_status_checks_contexts` to include merge queue checks
3. Use `required_status_checks_strict = true` to require up-to-date branches
4. Avoid wildcard branch patterns on merge queue branches

### GitHub Rulesets vs Branch Protection

- **Branch Protection** (current): Traditional, well-tested, works everywhere
- **GitHub Rulesets** (newer): More flexible, better for organizations, easier audit
- **Recommendation**: Stick with branch protection for now, migrate to rulesets when needed

### References

- [Mergify Merge Protections](https://docs.mergify.com/merge-protections/)
- [GitHub Branch Protection Best Practices](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [Managing a Merge Queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

## Troubleshooting

### HCP Terraform Authentication Errors

Ensure `TF_API_TOKEN` secret is set in GitHub Actions:
- Generate a team or user API token at https://app.terraform.io/app/settings/tokens
- Token needs permissions to manage workspaces in the `jbcom` organization
- The workflow automatically configures credentials via `cli_config_credentials_token`

### GitHub Authentication Errors

Ensure `CI_GITHUB_TOKEN` is set with appropriate permissions:
- `repo` (full control)
- `admin:org` (read access for org settings)

### Import Errors

The module uses Terraform 1.5+ import blocks. If import fails:
1. Verify repository exists: `gh repo view jbcom/<repo>`
2. Check token permissions
3. Verify branch protection exists

### File Sync Errors

If file sync fails:
1. Check file path is correct
2. Verify branch exists
3. Check repository isn't archived

### Drift Detection

If drift is detected:
1. Review the plan output
2. Decide if external changes should be kept or reverted
3. Either update terragrunt config or apply to restore

## Migration from Previous Approach

1. Removed duplicate `terraform/` directory (was HCP-based approach)
2. Added `.terragrunt-cache/` to `.gitignore`
3. Integrated file sync into Terraform module (replaces repo-file-sync-action)
4. Added `security_and_analysis` block for secret scanning
