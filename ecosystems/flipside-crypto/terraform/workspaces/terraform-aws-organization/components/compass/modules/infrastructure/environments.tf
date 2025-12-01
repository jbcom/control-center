module "environment_manifest" {
  for_each = module.copilot_environment_certificates

  source = "git@github.com:FlipsideCrypto/gitops.git//terraform/modules/os/os-update-and-record-file"

  yaml_data = templatefile("${path.module}/templates/manifests/environment.yml", {
    environment_name = each.key,
    vpc_id           = local.vpc_id,
    public_subnets   = local.public_subnet_ids,
    private_subnets  = local.private_subnet_ids,
    acm_certificate_arns = [
      aws_acm_certificate.route53.arn,
      each.value.arn,
    ],
  })

  checksum = timestamp()

  file_path = "copilot/environments/${each.key}/manifest.yml"

  log_file_name = "env-manifest-compass-${each.key}.log"
}
