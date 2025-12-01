module "environment_pipeline_manifest" {
  for_each = toset(local.compass_environments)

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = templatefile("${path.module}/templates/manifests/pipeline.yml", {
    environment_name = each.key
    pipeline_type    = "environment"
    connection_name  = aws_codestarconnections_connection.default.name
    branch           = each.key == "prod" ? "main" : "staging"
  })

  checksum = timestamp()

  file_path = "copilot/pipelines/compass-${each.key}-environment/manifest.yml"

  log_file_name = "pipeline-manifest-compass-env-${each.key}.log"
}

module "environment_pipeline_buildspec" {
  for_each = toset(local.compass_environments)

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = templatefile("${path.module}/templates/manifests/buildspec/environment.yml", {
    environment_name   = each.key
    dockerhub_username = aws_ssm_parameter.dockerhub["username"].name
    dockerhub_password = aws_ssm_parameter.dockerhub["password"].name
  })

  checksum = timestamp()

  file_path = "copilot/pipelines/compass-${each.key}-environment/buildspec.yml"

  log_file_name = "pipeline-buildspec-compass-env-${each.key}.log"
}

module "service_pipeline_manifest" {
  for_each = toset(local.compass_environments)

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = templatefile("${path.module}/templates/manifests/pipeline.yml", {
    environment_name = each.key
    pipeline_type    = "workloads"
    connection_name  = aws_codestarconnections_connection.default.name
    branch           = each.key == "prod" ? "main" : "staging"
  })

  checksum = timestamp()

  file_path = "copilot/pipelines/compass-${each.key}-workloads/manifest.yml"

  log_file_name = "pipeline-manifest-compass-workloads-${each.key}.log"
}

module "workloads_pipeline_buildspec" {
  for_each = toset(local.compass_environments)

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = templatefile("${path.module}/templates/manifests/buildspec/workloads.yml", {
    environment_name   = each.key
    dockerhub_username = aws_ssm_parameter.dockerhub["username"].name
    dockerhub_password = aws_ssm_parameter.dockerhub["password"].name
  })

  checksum = timestamp()

  file_path = "copilot/pipelines/compass-${each.key}-workloads/buildspec.yml"

  log_file_name = "pipeline-buildspec-compass-workloads-${each.key}.log"
}

resource "local_sensitive_file" "pipeline_overrides_file" {
  for_each = merge(flatten([
    for environment_name in local.compass_environments : [
      for pipeline_type in ["environment", "workloads"] : [
        for file_name in fileset("${var.rel_to_root}/overrides/pipelines", "*.yml") : {
          "compass-${environment_name}-${pipeline_type}/overrides/${file_name}" = file("${var.rel_to_root}/overrides/pipelines/${file_name}")
        }
      ]
    ]
  ])...)

  filename = "${var.rel_to_root}/copilot/pipelines/${each.key}"
  content  = each.value
}
