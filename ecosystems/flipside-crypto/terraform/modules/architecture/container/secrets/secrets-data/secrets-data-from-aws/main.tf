data "aws_secretsmanager_secret_version" "this" {
  for_each = {
    for secret_key, secret_data in var.secrets : secret_key => secret_data["id"] if secret_data["type"] == "secretsmanager" || (secret_data["type"] == "" && startswith(secret_data["id"], "arn:aws:secretsmanager"))
  }

  secret_id = each.value
}

data "aws_ssm_parameter" "this" {
  for_each = {
    for secret_key, secret_data in var.secrets : secret_key => secret_data["id"] if secret_data["path"] == "" && (secret_data["type"] == "ssm" || (secret_data["type"] == "" && startswith(secret_data["id"], "/")))
  }

  name = each.value
}

data "aws_ssm_parameters_by_path" "this" {
  for_each = {
    for secret_key, secret_data in var.secrets : secret_key => secret_data["path"] if secret_data["path"] != "" && (secret_data["type"] == "ssm" || secret_data["type"] == "")
  }

  path = each.value

  recursive = true
}

locals {
  ssm_path_data = {
    for secret_key, parameters_data in data.aws_ssm_parameters_by_path.this : secret_key => {
      for k, v in zipmap(parameters_data["names"], parameters_data["values"]) : trimprefix(k, "${trimsuffix(var.secrets[secret_key]["path"], "/")}/") => v
    }
  }

  secrets_data = merge({
    for secret_key, secret_data in var.secrets : secret_key => secret_data["id"] if !contains(keys(data.aws_secretsmanager_secret_version.this), secret_key) && !contains(keys(data.aws_ssm_parameter.this), secret_key) && lookup(secret_data, "path", "") == ""
    }, {
    for secret_key, secret_data in data.aws_secretsmanager_secret_version.this : secret_key => secret_data["secret_string"]
    }, {
    for secret_key, secret_data in data.aws_ssm_parameter.this : secret_key => secret_data["value"]
    }, {
    for secret_key, path_data in local.ssm_path_data : secret_key => lookup(path_data, var.secrets[secret_key]["id"], "")
  })
}
