# Repository type definitions
variable "python_repos" {
  description = "Python package repositories"
  type        = list(string)
  default = [
    "agentic-crew",
    "ai_game_dev",
    "directed-inputs-class",
    "extended-data-types",
    "lifecyclelogging",
    "python-terraform-bridge",
    "rivers-of-reckoning",
    "vendor-connectors",
  ]
}

variable "nodejs_repos" {
  description = "Node.js/TypeScript package repositories"
  type        = list(string)
  default = [
    "agentic-control",
    "otter-river-rush",
    "otterfall",
    "pixels-pygame-palace",
    "rivermarsh",
    "strata",
  ]
}

variable "go_repos" {
  description = "Go package repositories"
  type        = list(string)
  default = [
    "port-api",
    "vault-secret-sync",
  ]
}

variable "terraform_repos" {
  description = "Terraform module repositories"
  type        = list(string)
  default = [
    "terraform-github-markdown",
    "terraform-repository-automation",
  ]
}

# Repository settings
variable "default_branch" {
  description = "Default branch name for all repositories"
  type        = string
  default     = "main"
}

variable "allow_squash_merge" {
  description = "Allow squash merging pull requests"
  type        = bool
  default     = true
}

variable "allow_merge_commit" {
  description = "Allow merge commits"
  type        = bool
  default     = false
}

variable "allow_rebase_merge" {
  description = "Allow rebase merging"
  type        = bool
  default     = false
}

variable "delete_branch_on_merge" {
  description = "Automatically delete head branches after pull requests are merged"
  type        = bool
  default     = true
}

variable "enable_issues" {
  description = "Enable GitHub Issues"
  type        = bool
  default     = true
}

variable "enable_projects" {
  description = "Enable GitHub Projects"
  type        = bool
  default     = false
}

variable "enable_wiki" {
  description = "Enable GitHub Wiki"
  type        = bool
  default     = false
}

variable "enable_discussions" {
  description = "Enable GitHub Discussions"
  type        = bool
  default     = false
}

# Security settings
variable "enable_secret_scanning" {
  description = "Enable secret scanning"
  type        = bool
  default     = true
}

variable "enable_secret_scanning_push_protection" {
  description = "Enable secret scanning push protection"
  type        = bool
  default     = true
}

variable "enable_dependabot_security_updates" {
  description = "Enable Dependabot security updates"
  type        = bool
  default     = true
}

# Branch protection settings
variable "require_pull_request" {
  description = "Require pull requests before merging"
  type        = bool
  default     = true
}

variable "required_approving_review_count" {
  description = "Number of required approving reviews"
  type        = number
  default     = 0
}

variable "dismiss_stale_reviews" {
  description = "Dismiss stale pull request approvals when new commits are pushed"
  type        = bool
  default     = false
}

variable "require_code_owner_reviews" {
  description = "Require review from code owners"
  type        = bool
  default     = false
}

variable "require_linear_history" {
  description = "Require linear history"
  type        = bool
  default     = false
}

variable "allow_force_pushes" {
  description = "Allow force pushes"
  type        = bool
  default     = false
}

variable "allow_deletions" {
  description = "Allow deletions of the protected branch"
  type        = bool
  default     = false
}

variable "enable_pages" {
  description = "Enable GitHub Pages with Actions build"
  type        = bool
  default     = true
}

# Additional repository settings
variable "repository_visibility" {
  description = "Repository visibility (public or private). All jbcom repos are public."
  type        = string
  default     = "public"
}

variable "allow_auto_merge" {
  description = "Allow auto-merge on pull requests"
  type        = bool
  default     = false
}

# Additional branch protection settings
variable "require_last_push_approval" {
  description = "Require approval from someone other than the last pusher"
  type        = bool
  default     = false
}

variable "require_signed_commits" {
  description = "Require signed commits on protected branch"
  type        = bool
  default     = false
}

variable "required_status_checks_strict" {
  description = "Require branches to be up to date before merging"
  type        = bool
  default     = false
}

variable "required_status_checks_contexts" {
  description = "List of required status check contexts (CI jobs that must pass)"
  type        = list(string)
  default     = []
}
