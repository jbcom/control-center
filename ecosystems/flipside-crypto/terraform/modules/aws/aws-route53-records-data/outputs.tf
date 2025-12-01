output "records" {
  value = local.aws_route53_records_data

  description = "AWS Route53 records for the provided zones in the account"
}