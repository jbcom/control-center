module "self" {
  source = "../../external/git-repository-data"

  query_type = "local"

  log_file_path = local.log_file_path
  log_file_name = local.log_file_name
}

locals {
  rel_to_root = module.self.rel_to_root
}