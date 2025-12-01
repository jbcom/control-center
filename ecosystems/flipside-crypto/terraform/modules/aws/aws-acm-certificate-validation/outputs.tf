output "validation_record_fqdns" {
  value = [for record in aws_route53_record.default : record.fqdn]

  description = "Validation record FQDNs"
}