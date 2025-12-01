resource "github_repository" "default" {
  name        = var.pipeline_name
  description = "Pipeline repository for ${var.pipeline_name}"

  visibility   = "internal"
  auto_init    = true
  has_issues   = false
  has_projects = false
  has_wiki     = false
  is_template  = false

  gitignore_template = "Terraform"
  license_template   = "mit"

  allow_merge_commit          = false
  allow_squash_merge          = true
  squash_merge_commit_title   = "COMMIT_OR_PR_TITLE"
  squash_merge_commit_message = "COMMIT_MESSAGES"
  allow_rebase_merge          = false
  allow_auto_merge            = true
  delete_branch_on_merge      = true

  vulnerability_alerts = true

  topics = ["terraform", "pipelines", "infrastructure-as-code", "devops"]

  archive_on_destroy = false
}

resource "github_branch" "default" {
  repository = github_repository.default.name
  branch     = "main"
}

resource "github_branch_default" "default" {
  repository = github_repository.default.name
  branch     = github_branch.default.branch
}