resource "aws_route53_record" "default" {
  for_each = var.children

  zone_id = var.parent_zone_id
  name    = each.key
  type    = "NS"
  ttl     = 300

  allow_overwrite = true

  records = each.value["zone_name_servers"]
}