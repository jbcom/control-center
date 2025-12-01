locals {
  environment_name = var.context["environment"]

}

module "secrets" {
  for_each = var.shared_data

  source = "../secrets"

  config = lookup(each.value, "secrets", {})

  secret_manager_name_prefix = "shared/${each.key}"

  create_policy = true

  policy_name = "${each.key}-shared-secrets"

  context = var.context

  rel_to_root = var.rel_to_root
}

module "environment_variables" {
  for_each = var.shared_data

  source = "../environment-variables"

  config = lookup(each.value, "environment_variables", {})

  context = var.context

  rel_to_root = var.rel_to_root
}

locals {
  records_config = {
    data_groups = {
      for share_name in keys(var.shared_data) : share_name => merge(try(module.secrets[share_name], {}), try(module.environment_variables[share_name], {}))
    }
  }
}

module "permanent_record" {
  source = "../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
