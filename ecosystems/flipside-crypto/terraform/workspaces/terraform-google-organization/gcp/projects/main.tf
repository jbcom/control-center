locals {
  # Project and organization
  billing_account = "0107B9-45570A-CE2E85"
  billing_project = "cs-host-cf978c9f30fc401ba79e34"

  org_id = "429463833666"

  # Networking
  subnet_name_primary   = "compute"
  subnet_name_secondary = "auth"

  # SCIM configuration
  scim_subdomain = "scim"
}

module "project" {
  source  = "terraform-google-modules/project-factory/google"
  version = "18.0.0"

  for_each = local.context.gcp.projects

  name            = try(coalesce(each.value.name), each.key)
  project_id      = try(coalesce(each.value.project_id), each.key)
  org_id          = local.org_id
  billing_account = local.billing_account
}

locals {
  projects = module.project
}