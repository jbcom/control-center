# Repository information
output "managed_repositories" {
  description = "Map of all managed repositories"
  value = {
    for repo, config in local.all_repos : repo => {
      name     = github_repository.managed[repo].name
      language = config.language
      url      = github_repository.managed[repo].html_url
    }
  }
}

output "python_repositories" {
  description = "List of Python repositories"
  value       = var.python_repos
}

output "nodejs_repositories" {
  description = "List of Node.js repositories"
  value       = var.nodejs_repos
}

output "go_repositories" {
  description = "List of Go repositories"
  value       = var.go_repos
}

output "terraform_repositories" {
  description = "List of Terraform repositories"
  value       = var.terraform_repos
}

output "repository_count" {
  description = "Total number of managed repositories"
  value       = length(local.all_repos)
}
