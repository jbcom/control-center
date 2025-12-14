# Docker Hub Repository Module
# Manages Docker Hub repositories using the artificialinc/dockerhub provider
#
# Usage:
#   module "dockerhub" {
#     source = "../modules/dockerhub"
#
#     repositories = {
#       "agentic-triage" = {
#         description = "AI-powered GitHub issue triage"
#         private     = false
#       }
#     }
#   }

# Note: required_providers is defined in terragrunt generate "provider" block
# Do not add terraform {} block here to avoid conflicts

variable "namespace" {
  type        = string
  description = "Docker Hub namespace (username or organization)"
  default     = "jbdevprimary"
}

variable "repositories" {
  type = map(object({
    description      = optional(string, "")
    private          = optional(bool, false)
    full_description = optional(string, "")
  }))
  description = "Map of repository names to their configurations"
}

# Create Docker Hub repositories
resource "dockerhub_repository" "repo" {
  for_each = var.repositories

  namespace        = var.namespace
  name             = each.key
  description      = each.value.description
  private          = each.value.private
  full_description = each.value.full_description != "" ? each.value.full_description : each.value.description
}

output "repositories" {
  value = {
    for name, repo in dockerhub_repository.repo : name => {
      namespace = repo.namespace
      name      = repo.name
      url       = "https://hub.docker.com/r/${repo.namespace}/${repo.name}"
    }
  }
  description = "Created Docker Hub repositories"
}
