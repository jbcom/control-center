# Local values for managing all repositories
locals {
  # Combine all repositories into a single map with their language type
  all_repos = merge(
    { for repo in var.python_repos : repo => {
      language      = "python"
      enable_eslint = false
    } },
    { for repo in var.nodejs_repos : repo => {
      language      = "nodejs"
      enable_eslint = true
    } },
    { for repo in var.go_repos : repo => {
      language      = "go"
      enable_eslint = false
    } },
    { for repo in var.terraform_repos : repo => {
      language      = "terraform"
      enable_eslint = false
    } }
  )
}

# Repository settings
resource "github_repository" "managed" {
  for_each = local.all_repos

  name = each.key
  # Description will be managed separately per repo if needed
  # For now, rely on existing descriptions (Terraform won't overwrite if not specified)

  # Visibility - all jbcom repos are public
  visibility = var.repository_visibility

  # Features
  has_issues      = var.enable_issues
  has_projects    = var.enable_projects
  has_wiki        = var.enable_wiki
  has_discussions = var.enable_discussions

  # Merge settings
  allow_squash_merge     = var.allow_squash_merge
  allow_merge_commit     = var.allow_merge_commit
  allow_rebase_merge     = var.allow_rebase_merge
  delete_branch_on_merge = var.delete_branch_on_merge
  allow_auto_merge       = var.allow_auto_merge

  # Security
  vulnerability_alerts = var.enable_dependabot_security_updates

  # Lifecycle - don't destroy existing repos
  lifecycle {
    prevent_destroy = true
  }
}

# Branch protection
resource "github_branch_protection" "main" {
  for_each = local.all_repos

  repository_id = github_repository.managed[each.key].node_id
  pattern       = var.default_branch

  # Require pull requests
  required_pull_request_reviews {
    dismiss_stale_reviews           = var.dismiss_stale_reviews
    require_code_owner_reviews      = var.require_code_owner_reviews
    required_approving_review_count = var.required_approving_review_count
    require_last_push_approval      = var.require_last_push_approval
  }

  # Status checks - configurable via variables
  # Note: Specific per-repo checks can be added by updating required_status_checks_contexts
  required_status_checks {
    strict   = var.required_status_checks_strict
    contexts = var.required_status_checks_contexts
  }

  # Code scanning integration
  # Note: GitHub's new rulesets API (used in sync.yml) is not yet fully supported
  # in the Terraform provider, so we continue using branch protection for now

  # History requirements
  required_linear_history = var.require_linear_history
  require_signed_commits  = var.require_signed_commits

  # Force push protection
  allows_force_pushes = var.allow_force_pushes
  allows_deletions    = var.allow_deletions

  # Admin bypass - Allow semantic-release to bypass protection
  # This is configured via repository rulesets in the workflow instead
  # because the Terraform provider doesn't yet support the bypass_actors feature
}

# Note: Security settings (secret scanning, push protection) and GitHub Pages
# are managed via the github_repository resource's security_and_analysis and pages blocks
# in GitHub provider v6.x, or configured separately via GitHub API/UI
