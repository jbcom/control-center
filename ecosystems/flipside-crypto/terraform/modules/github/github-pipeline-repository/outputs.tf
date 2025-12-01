output "name" {
  value = github_repository.default.name

  description = "Repository name"
}

output "default_branch" {
  value = github_branch.default.branch

  description = "Default branch"
}