output "zones" {
  value = local.aws_route53_zone_data

  description = "AWS Route53 zones for the account"
}