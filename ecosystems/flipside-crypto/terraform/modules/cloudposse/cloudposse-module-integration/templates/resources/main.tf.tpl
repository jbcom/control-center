locals {
  vault_path_prefix = "infrastructure/$${local.json_key}"

  environment = var.environment != null ? var.environment : lookup(var.context, "environment", null)

  json_key = var.account.json_key

  execution_role_arn = var.account.execution_role_arn

  domain = var.account.domain

  subdomain = var.account.subdomain

  kms_key_arn = var.kms_key_arn
  kms_key_id  = var.kms_key_id

  secrets_kms_key_arn = coalesce(var.secrets_kms_key_arn, local.kms_key_arn)

  vpc_id              = var.networking.vpc_id
  vpc_cidr_block      = var.networking.vpc_cidr_block
  public_subnet_ids   = var.networking.public_subnet_ids
  private_subnet_ids  = var.networking.private_subnet_ids

  allowed_cidr_blocks = var.allowed_cidr_blocks.private

  tags = {
  for k, v in var.context["tags"] : k => v if k != "Name"
  }

  public_cidr_blocks = var.allowed_cidr_blocks.public

  public_security_group_rules = [
    {
      type        = "ingress"
      from_port   = 0
      to_port     = 65535
      protocol    = "tcp"
      cidr_blocks = local.public_cidr_blocks
    }
  ]

  private_security_group_rules = [
  for cidr_block in local.allowed_cidr_blocks : {
    type        = "ingress"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = [cidr_block]
  }
  ]

  required_component_data = {
    account_id         = local.account_id
    execution_role_arn = local.execution_role_arn
  }

  live_infrastructure_data = {
%{ for module_name, module_data in generators ~}
%{ if length(module_data["child_module_names"]) > 0 ~}
    ${module_name} = {
      for module_name, module_data in local.${module_data["locals"]["resource"]} : module_name => merge(module_data, {
        children = [
%{ for child_module_name in module_data["child_module_names"] ~}
%{ for generated_child_module_name, generated_child_module_data in module_data["generates"] ~}
%{ if generated_child_module_data["module_name"] == child_module_name ~}
          "${generated_child_module_name}",
%{ endif ~}
%{ endfor ~}
%{ endfor ~}
        ]
      })
    }
%{ else ~}
    ${module_name} = local.${module_data["locals"]["resource"]}
%{ endif ~}

%{ endfor ~}
  }
%{ for module_name, generator_data in generated_from_generators ~}

  ${module_name}_infrastructure_data = {
    ${generator_data["infrastructure_merge_key"]} = local.${generator_data["locals"]["resource"]}
  }
%{ endfor ~}
}

module "infrastructure_data" {
  source = "$${REL_TO_ROOT}/terraform/modules/utils/deepmerge"

  source_maps = [
    local.live_infrastructure_data,
%{ for module_name, generator_data in generated_from_generators ~}
    local.${module_name}_infrastructure_data,
%{ endfor ~}
%{ for local_variable_name in extra_merged_resources ~}
    local.${local_variable_name},
%{ endfor ~}
  ]
}

locals {
  provisioned_infrastructure_data = module.infrastructure_data.merged_maps
}

module "permanent_record" {
  source = "$${REL_TO_ROOT}/terraform/modules/utils/permanent-record"

  save_permanent_record = var.save_permanent_record

  records = local.provisioned_infrastructure_data

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}