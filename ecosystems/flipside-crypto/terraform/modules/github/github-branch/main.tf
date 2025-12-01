resource "github_branch" "this" {
  branch     = var.branch_name
  repository = var.repository_name
}

resource "github_branch_default" "this" {
  count = var.default_branch ? 1 : 0

  branch     = github_branch.this.branch
  repository = var.repository_name
}