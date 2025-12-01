module "aws_kms_keys" {
  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["kms", "list-keys"]
  aws_cli_query    = "Keys"

  assume_role_arn = var.execution_role_arn
}

module "aws_kms_key_data" {
  for_each = toset([
    for result in module.aws_kms_keys.result : result["KeyArn"]
  ])

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["kms", "describe-key", "--key-id", each.key]
  aws_cli_query    = "KeyMetadata"

  assume_role_arn = var.execution_role_arn
}

locals {
  aws_kms_key_raw_data = {
    for kms_key_arn, results in module.aws_kms_key_data : kms_key_arn => {
      for k, v in results["result"] : replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") => v
    }
  }
}

module "aws_kms_key_aliases" {
  for_each = local.aws_kms_key_raw_data

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["kms", "list-aliases", "--key-id", each.key]
  aws_cli_query    = "Aliases"

  assume_role_arn = var.execution_role_arn
}

module "aws_kms_key_grants" {
  for_each = local.aws_kms_key_raw_data

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["kms", "list-grants", "--key-id", each.key]
  aws_cli_query    = "Grants"

  assume_role_arn = var.execution_role_arn
}

module "aws_kms_key_policy" {
  for_each = local.aws_kms_key_raw_data

  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["kms", "get-key-policy", "--policy-name", "default", "--key-id", each.key]
  aws_cli_query    = "Policy"

  assume_role_arn = var.execution_role_arn
}

locals {
  aws_kms_key_data = {
    for kms_key_arn, kms_key_data in local.aws_kms_key_raw_data : kms_key_arn => merge(kms_key_data, {
      aliases = [
        for result in module.aws_kms_key_aliases[kms_key_arn].result : trimprefix(result["AliasName"], "alias/")
      ]

      grants = {
        for result in module.aws_kms_key_grants[kms_key_arn].result : result["GrantId"] => {
          for k, v in result :
          replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_")
          => v
        }
      }

      policy = module.aws_kms_key_policy[kms_key_arn].result
    })
  }
}