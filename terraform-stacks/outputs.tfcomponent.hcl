# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

output "repository_urls" {
  description = "URLs of managed repositories"
  type        = map(string)
  value       = { for name, repo in component.repositories : name => repo.html_url }
}

output "repository_count" {
  description = "Number of repositories in this deployment"
  type        = number
  value       = length(var.repos)
}

output "language" {
  description = "Language category for this deployment"
  type        = string
  value       = var.language
}
