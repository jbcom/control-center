data "sops_file" "grafana_secrets" {
  source_file = "${path.module}/secrets/grafana.yaml"
}

module "base" {
  source = "../modules/infrastructure"

  context         = local.context
  vendors         = local.vendors_data
  grafana_api_key = data.sops_file.grafana_secrets.data.api_key
  rel_to_root     = local.rel_to_root
  records_dir     = "records/${local.workspaces_dir}"
}

import {
  id = "compass-us-east-1-compass-prod-public-20230221220447335100000006"
  to = module.base.aws_db_parameter_group.db_instance_prod
}

import {
  id = "compass-us-east-1-compass-stg-public-20230221220447314700000003"
  to = module.base.aws_db_parameter_group.db_instance_stg
}
