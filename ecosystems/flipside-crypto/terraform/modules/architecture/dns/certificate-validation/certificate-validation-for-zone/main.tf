module "default" {
  for_each = var.certificates

  source = "./.."

  zone_id = var.zone_id

  domain_validation_options = flatten(each.value["domain_validation_options"])

  acm_certificate_arn = each.value["arn"]
}