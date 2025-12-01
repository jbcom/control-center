# DNS Configuration for Lambda Deployment Resources

locals {
  # Determine if we need to create DNS records for API Gateway
  create_api_gateway_dns = local.dns.enabled && local.dns.create_dns_records && local.api_gateway.enabled && local.api_gateway.create_domain_name && local.api_gateway.create_domain_records

  # Determine if we need to create DNS records for S3 CDN
  create_s3_cdn_dns = local.dns.enabled && local.dns.create_dns_records && local.s3_cdn.enabled && local.s3_cdn.dns_alias_enabled

  # Determine the zone ID to use for API Gateway
  api_gateway_zone_id = local.api_gateway_effective_zone_id != null ? local.api_gateway_effective_zone_id : (
    local.api_gateway_effective_hosted_zone_name != null ? data.aws_route53_zone.api_gateway[0].zone_id : null
  )

  # Determine the zone ID to use for S3 CDN
  s3_cdn_zone_id = local.s3_cdn_effective_zone_id != null ? local.s3_cdn_effective_zone_id : (
    local.s3_cdn_effective_zone_name != "" ? data.aws_route53_zone.s3_cdn[0].zone_id : null
  )
}

# Data source to fetch the Route53 zone for API Gateway if needed
data "aws_route53_zone" "api_gateway" {
  count = local.create_api_gateway_dns && local.api_gateway_effective_hosted_zone_name != null && local.api_gateway_effective_zone_id == null ? 1 : 0

  name         = local.api_gateway_effective_hosted_zone_name
  private_zone = local.dns.private_zone
}

# Data source to fetch the Route53 zone for S3 CDN if needed
data "aws_route53_zone" "s3_cdn" {
  count = local.create_s3_cdn_dns && local.s3_cdn_effective_zone_name != "" && local.s3_cdn_effective_zone_id == null ? 1 : 0

  name         = local.s3_cdn_effective_zone_name
  private_zone = local.dns.private_zone
}

# Route53 record for API Gateway
resource "aws_route53_record" "api_gateway" {
  count = local.create_api_gateway_dns && local.api_gateway_zone_id != null ? 1 : 0

  zone_id = local.api_gateway_zone_id
  name    = local.api_gateway.domain_name
  type    = local.dns.dns_record_type
  ttl     = local.dns.dns_record_ttl

  alias {
    name                   = aws_apigatewayv2_domain_name.this[0].domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.this[0].domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = local.dns.dns_record_evaluate_target_health
  }
}

# Route53 record for S3 CDN (CloudFront)
# Note: This is only created if we're not using the built-in DNS functionality of the CloudFront module
resource "aws_route53_record" "s3_cdn" {
  for_each = local.create_s3_cdn_dns && local.s3_cdn_zone_id != null && length(local.s3_cdn.external_aliases) > 0 ? {
    for alias in local.s3_cdn.external_aliases : alias => alias
  } : {}

  zone_id = local.s3_cdn_zone_id
  name    = each.key
  type    = local.dns.dns_record_type
  ttl     = local.dns.dns_record_ttl

  alias {
    name                   = module.cloudfront_s3_cdn[0].cloudfront_distribution_domain_name
    zone_id                = module.cloudfront_s3_cdn[0].cloudfront_distribution_hosted_zone_id
    evaluate_target_health = local.dns.dns_record_evaluate_target_health
  }
}

# IPv6 Route53 record for S3 CDN (CloudFront)
resource "aws_route53_record" "s3_cdn_ipv6" {
  for_each = local.create_s3_cdn_dns && local.s3_cdn_zone_id != null && length(local.s3_cdn.external_aliases) > 0 && local.s3_cdn.ipv6_enabled ? {
    for alias in local.s3_cdn.external_aliases : alias => alias
  } : {}

  zone_id = local.s3_cdn_zone_id
  name    = each.key
  type    = "AAAA"

  alias {
    name                   = module.cloudfront_s3_cdn[0].cloudfront_distribution_domain_name
    zone_id                = module.cloudfront_s3_cdn[0].cloudfront_distribution_hosted_zone_id
    evaluate_target_health = local.dns.dns_record_evaluate_target_health
  }
}
