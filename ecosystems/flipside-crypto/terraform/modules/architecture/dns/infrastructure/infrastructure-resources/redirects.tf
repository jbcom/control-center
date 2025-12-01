data "aws_ssm_parameters_by_path" "redirects" {
  for_each = local.configured_zones

  path = "/redirects/${each.key}"

  recursive = true
}

locals {
  zone_redirects_data = {
    for zone_name, parameters_data in data.aws_ssm_parameters_by_path.redirects : zone_name => {
      redirects = {
        for k, v in zipmap(parameters_data["names"], parameters_data["values"]) : trimprefix(k, "/redirects/${zone_name}/") => jsondecode(v)
      }
    }
  }

  redirects_data = {
    zones = local.zone_redirects_data
  }
}