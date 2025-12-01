locals {
  domains_config = var.context["domains"]
}

resource "aws_route53_zone" "default" {
  name = local.domains_config["route53"]

  tags = local.tags
}

locals {
  zone_id   = aws_route53_zone.default.zone_id
  zone_name = aws_route53_zone.default.name
}

resource "aws_route53_record" "ns" {
  zone_id         = local.zone_id
  name            = local.zone_name
  type            = "NS"
  ttl             = 60
  allow_overwrite = true

  records = [
    aws_route53_zone.default.name_servers[0],
    aws_route53_zone.default.name_servers[1],
    aws_route53_zone.default.name_servers[2],
    aws_route53_zone.default.name_servers[3],
  ]
}

resource "aws_route53_record" "soa" {
  zone_id         = local.zone_id
  name            = local.zone_name
  type            = "SOA"
  ttl             = 30
  allow_overwrite = true

  records = [
    format("%s. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400", aws_route53_zone.default.name_servers[0])
  ]
}
