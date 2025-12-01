locals {
  environment_name = var.context["environment"]
  cluster_name     = var.context["clusters"][local.environment_name]["cluster_name"]
  account_data     = var.context["cluster_accounts_by_environment"][local.environment_name]
  json_key         = local.account_data["json_key"]
  tags             = local.account_data["tags"]

  networking_data    = var.context["cluster_networks"][local.json_key]
  vpc_id             = local.networking_data["vpc_id"]
  private_subnet_ids = local.networking_data["private_subnet_ids"]
  public_subnet_ids  = local.networking_data["public_subnet_ids"]
}

locals {
  records_config = {
    system_environment = {
      tasks = local.task_environment_config

      task_tags = local.task_tags

      ecr_repository_urls = module.ecr_repository.repository_url_map
    }
  }
}

module "permanent_record" {
  source = "../../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}