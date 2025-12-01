# output "domain_validations" {
#   value = aws_acm_certificate.cert.domain_validation_options
# }

output "alb_url" {
  value = aws_alb.rpc.dns_name
}

output "alb_rpc_target_group_arn" {
  value = aws_lb_target_group.rpc.arn
}

output "alb_rpc_target_group_name" {
  value = aws_lb_target_group.rpc.name
}

output "cloudflare_zone_name" {
  value = data.cloudflare_zone.zone.name
}

output "cloudflare_zone_id" {
  value = data.cloudflare_zone.zone.id
}
