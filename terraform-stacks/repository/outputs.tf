# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

output "name" {
  description = "Repository name"
  value       = github_repository.this.name
}

output "full_name" {
  description = "Full repository name (org/repo)"
  value       = github_repository.this.full_name
}

output "html_url" {
  description = "Repository URL"
  value       = github_repository.this.html_url
}

output "node_id" {
  description = "Repository node ID"
  value       = github_repository.this.node_id
}

output "default_branch" {
  description = "Default branch"
  value       = github_repository.this.default_branch
}
