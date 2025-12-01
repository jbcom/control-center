module "git_repository_data" {
  source = "../../git/git-repository-data"
}

locals {
  repository_local_data = module.git_repository_data
  repository_name       = local.repository_local_data["name"]
  metadata              = jsondecode(file("${path.module}/files/metadata.json"))
  repositories_data     = local.metadata["github_repositories"]
  repository_data       = local.repositories_data[local.repository_name]
}