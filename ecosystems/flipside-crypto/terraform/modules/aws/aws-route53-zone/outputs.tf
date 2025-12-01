output "zone_id" {
  value = aws_route53_zone.this.zone_id

  description = "Zone ID"
}

output "arn" {
  value = aws_route53_zone.this.arn

  description = "Zone ARN"
}

output "name_servers" {
  value = aws_route53_zone.this.name_servers

  description = "Name servers"
}

output "primary_name_server" {
  value = aws_route53_zone.this.primary_name_server

  description = "Primary name server"
}