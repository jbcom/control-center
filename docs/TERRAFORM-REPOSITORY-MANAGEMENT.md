# Terraform Repository Management

## Overview

As of December 2025, jbcom-control-center uses Terraform to actively manage repository configurations across all 18 jbcom repositories. This replaces the previous passive sync workflow approach.

## Why Terraform?

### Problems with Previous Approach

The previous sync workflow had several issues:

1. **Passive Management**: Used bash scripts in GitHub Actions to sync settings
2. **No State Management**: No tracking of actual vs. desired state
3. **Drift Detection**: No automated way to detect when repositories diverged
4. **Configuration Scattered**: Settings spread across multiple YAML files
5. **Limited Rollback**: Difficult to undo changes or review history
6. **No Preview**: Changes applied immediately without review

### Benefits of Terraform

1. **Active State Management**: Terraform tracks actual state vs. desired state
2. **Drift Detection**: Automatically detects when repositories diverge
3. **Plan Preview**: See exactly what will change before applying
4. **Version Control**: All configuration in code with full git history
5. **Rollback**: Easy to revert to previous configurations
6. **Declarative**: Describe desired state, not imperative steps
7. **Provider Ecosystem**: Leverage GitHub provider features

## Architecture

### State Storage

- **Backend**: HCP Terraform Cloud
- **Organization**: `jbcom`
- **Workspace**: `jbcom-control-center`
- **Execution Mode**: Local (runs in GitHub Actions)
- **State Locking**: Automatic via HCP
- **State Encryption**: At rest in HCP

### Repository Categories

Repositories are managed in 4 language categories:

| Category | Count | Repos |
|----------|-------|-------|
| **Python** | 8 | agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors |
| **Node.js** | 6 | agentic-control, otter-river-rush, otterfall, pixels-pygame-palace, rivermarsh, strata |
| **Go** | 2 | port-api, vault-secret-sync |
| **Terraform** | 2 | terraform-github-markdown, terraform-repository-automation |

Each category has specific settings (e.g., Node.js repos enable ESLint in code quality checks).

## What's Managed

### Repository Settings (`github_repository`)
- Merge strategies (squash only, delete branch on merge)
- Feature flags (issues enabled, wiki/projects/discussions disabled)
- Visibility (public)
- Auto-merge settings

### Branch Protection (`github_branch_protection`)
- Pull request requirements (0 approvals required)
- Review dismissal settings
- Status check requirements
- Linear history enforcement
- Force push protection
- Deletion protection

### Security Settings (`github_repository_security_and_analysis`)
- Secret scanning (enabled)
- Secret scanning push protection (enabled)
- Dependabot security updates (enabled)

### GitHub Pages (`github_repository_pages`)
- Enabled for all repositories
- Build type: GitHub Actions workflow
- Source branch: main

## What's NOT Managed

These remain in the sync workflow:

1. **Secrets Sync** (`sync-secrets` job)
   - Managed via `jpoehnelt/secrets-sync-action`
   - Syncs: CI_GITHUB_TOKEN, PYPI_TOKEN, NPM_TOKEN, DOCKERHUB_*, ANTHROPIC_API_KEY

2. **File Sync** (`sync-files` job)
   - Managed via `BetaHuhn/repo-file-sync-action`
   - Syncs: Cursor rules, Dockerfiles, workflows, documentation

3. **Repository Rulesets** (temporary)
   - The GitHub Terraform provider doesn't fully support the new Rulesets API yet
   - Advanced features like Copilot code review, CodeQL integration still use the sync workflow
   - Will migrate when provider support is complete

## Directory Structure

```
terraform/
├── providers.tf          # GitHub provider + HCP backend config
├── variables.tf          # Input variables (repo lists, settings)
├── main.tf               # Repository resources
├── outputs.tf            # Output values
├── README.md             # Terraform-specific docs
├── .gitignore            # Ignore .terraform/, *.tfstate
└── .terraform.lock.hcl   # Provider version lock (committed)
```

## Workflow Integration

### Terraform Sync Workflow

`.github/workflows/terraform-sync.yml` runs Terraform automatically:

| Trigger | Action | Purpose |
|---------|--------|---------|
| Push to main (terraform/**) | `terraform apply` | Apply configuration changes |
| Pull request (terraform/**) | `terraform plan` | Preview changes, comment on PR |
| Daily at 2 AM UTC | `terraform plan` | Detect drift |
| Manual dispatch | `terraform plan` or `apply` | On-demand execution |

### Environment Variables

- `TF_API_TOKEN`: HCP Terraform Cloud token (GitHub secret, auto-provided to Copilot)
- `CI_GITHUB_TOKEN`: GitHub PAT for repository management (GitHub secret)
- `GITHUB_TOKEN`: Default Actions token (for PR comments)

## Migration from Sync Workflow

### Completed

- ✅ Created Terraform configuration
- ✅ Defined all 18 repositories
- ✅ Set up HCP Terraform Cloud workspace
- ✅ Created GitHub Actions workflow
- ✅ Documented new approach

### Remaining

- [ ] Initialize Terraform and import existing repositories
- [ ] Run `terraform plan` to verify no unintended changes
- [ ] Apply configuration to align repositories
- [ ] Update `.github/workflows/sync.yml` to remove redundant jobs
- [ ] Monitor drift detection for 1 week
- [ ] Archive old bash scripts

## Usage

### Making Configuration Changes

1. **Edit Terraform files** in `terraform/`
   ```bash
   cd terraform
   vim variables.tf  # Change settings
   ```

2. **Create a Pull Request**
   ```bash
   git checkout -b config/update-merge-settings
   git add terraform/
   git commit -m "config: update merge settings"
   git push origin config/update-merge-settings
   gh pr create
   ```

3. **Review the Plan**
   - GitHub Actions will comment on the PR with `terraform plan` output
   - Review what will change before merging

4. **Merge to Apply**
   - Merge the PR to main
   - GitHub Actions will automatically run `terraform apply`

### Detecting Drift

Drift occurs when repository settings are changed outside Terraform (e.g., via GitHub UI).

**Automated Detection**:
- Runs daily at 2 AM UTC
- Fails the workflow if drift is detected
- Outputs the drift in workflow logs

**Manual Detection**:
```bash
cd terraform
terraform plan
```

If drift is detected:
1. Review the plan to see what changed
2. Decide: Update Terraform to match reality, or apply Terraform to fix drift
3. Document the decision in a PR

### Adding a New Repository

1. **Add to variables.tf**:
   ```hcl
   variable "python_repos" {
     default = [
       "existing-repo",
       "new-repo",  # Add here
     ]
   }
   ```

2. **Create PR and merge**

3. **Import the repository**:
   ```bash
   cd terraform
   terraform import 'github_repository.managed["new-repo"]' new-repo
   terraform import 'github_branch_protection.main["new-repo"]' new-repo:main
   ```

### Removing a Repository

1. **Remove from variables.tf**
2. **Create PR and merge**
3. **Terraform will NOT delete the repo** (lifecycle prevent_destroy is enabled)

To actually delete:
```bash
terraform state rm 'github_repository.managed["old-repo"]'
terraform state rm 'github_branch_protection.main["old-repo"]'
```

## Troubleshooting

### Import Failures

**Symptom**: `terraform import` fails with "resource already in state"

**Solution**: Remove and re-import
```bash
terraform state rm 'github_repository.managed["repo-name"]'
terraform import 'github_repository.managed["repo-name"]' repo-name
```

### Authentication Errors

**Symptom**: "401 Unauthorized" or "403 Forbidden"

**Solution**: Verify GITHUB_TOKEN has correct permissions
```bash
export GITHUB_TOKEN="$CI_GITHUB_TOKEN"
gh auth status
terraform plan
```

### Drift Won't Resolve

**Symptom**: `terraform apply` doesn't fix drift

**Solution**: Some settings may be managed elsewhere (e.g., repository rulesets)
1. Check `.github/workflows/sync.yml` for conflicting management
2. Review GitHub UI for manual changes
3. Update Terraform to match reality if appropriate

### State Lock Issues

**Symptom**: "Error acquiring the state lock"

**Solution**: Another run is in progress or crashed
```bash
# Via HCP Terraform Cloud UI:
# Settings → Locking → Force Unlock
```

## References

- [HCP Terraform Cloud Workspace](https://app.terraform.io/app/jbcom/workspaces/jbcom-control-center)
- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [terraform/README.md](../terraform/README.md) - Local development guide
- [.github/workflows/terraform-sync.yml](../.github/workflows/terraform-sync.yml) - Workflow source

## Future Enhancements

1. **Migrate Rulesets to Terraform** when provider support is complete
2. **Add Repository Topics** management
3. **Add Team Permissions** management
4. **Add Branch Protection Rules** for feature branches
5. **Add Repository Variables** (non-secret configuration)
6. **Add Environments** (for deployment workflows)
