module "dns_metadata" {
  source = "../../../../dns/infrastructure/infrastructure-metadata"
}

locals {
  domain_name = local.account_data["subdomain"]

  dns_data = module.dns_metadata.metadata

  zone_data = local.dns_data["zones"][local.json_key][local.domain_name]
  zone_id   = local.cluster_zone["zone_id"]

  certificate_data = local.dns_data["certificates"][local.json_key][local.domain_name]
  certificate_arn  = local.certificate_data["arn"]

  access_logs_data = var.context["networks"][local.json_key]["access_logs"]

  task_primary_container = try(coalesce(one(keys(var.task_config["containers"])), keys(var.task_config["containers"])[0], null))

  task_ingress_config = merge({
    port             = 80
    protocol         = "HTTP"
    protocol_version = "HTTP1"
  }, try(var.task_config["containers"][local.task_primary_container]["ingress"], {}))

  task_health_check_config = merge({
    path                = "/"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 15
    matcher             = "200-399"
    timeout             = 10
  }, try(var.task_config["containers"][local.task_primary_container]["health_check"], {}))
}

module "target_group" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  name = local.task_primary_container

  attributes = [var.task_name]

  id_length_limit = 32

  context = var.context
}

module "alb" {
  source  = "cloudposse/alb/aws"
  version = "2.4.0"

  name = var.task_name

  enabled = local.task_enabled && local.task_exposed

  vpc_id                    = local.vpc_id
  ip_address_type           = "ipv4"
  subnet_ids                = local.public_subnet_ids
  https_enabled             = true
  http_ingress_cidr_blocks  = ["0.0.0.0/0"]
  https_ingress_cidr_blocks = ["0.0.0.0/0"]
  certificate_arn           = local.certificate_arn

  health_check_path                = local.task_health_check_config["path"]
  health_check_protocol            = local.task_health_check_config["protocol"]
  health_check_healthy_threshold   = local.task_health_check_config["healthy_threshold"]
  health_check_unhealthy_threshold = local.task_health_check_config["unhealthy_threshold"]
  health_check_interval            = local.task_health_check_config["interval"]
  health_check_matcher             = local.task_health_check_config["matcher"]
  health_check_timeout             = local.task_health_check_config["timeout"]

  target_group_name             = module.target_group.id
  target_group_port             = local.task_ingress_config["port"]
  target_group_protocol         = local.task_ingress_config["protocol"]
  target_group_protocol_version = local.task_ingress_config["protocol_version"]
  target_group_target_type      = "ip"

  default_target_group_enabled = true

  access_logs_prefix = var.task_name

  access_logs_s3_bucket_id = local.access_logs_data["bucket_id"]

  context = var.context
}

locals {
  cluster_zone        = local.dns_data["zones"][local.json_key][local.domain_name]
  cluster_certificate = local.certificate_data
  load_balancer_data  = module.alb

  alb_security_group_id = local.load_balancer_data["security_group_id"]
}

locals {
  route53_hostnames = distinct(concat([
    for _, container_definition in local.task_containers_config : container_definition["hostname"] if local.task_enabled && local.task_exposed && container_definition["enabled"] && container_definition["exposed"]
    ], [
    for hostname in lookup(var.task_config, "extra_hostnames", []) : format("%s.%s", split(".", hostname)[0], local.cluster_zone["fqdn"]) if local.task_enabled && local.task_exposed
  ]))

  cloudflare_hostnames = {
    for hostname in local.route53_hostnames : hostname => format("%s.%s", split(".", hostname)[0], local.cloudflare_domain) if local.cloudflare_zone != "" && local.cloudflare_domain != ""
  }

  hostnames = concat(local.route53_hostnames, values(local.cloudflare_hostnames))

  container_priorities = {
    for idx, container_name in sort(keys(local.task_containers_config)) : container_name => 100 + idx
  }
}

#module "alb_ingress" {
#  for_each = local.task_containers_config
#
#  source  = "cloudposse/alb-ingress/aws"
#  version = "0.28.0"
#
#  name = each.key
#
#  id_length_limit = 32
#
#  enabled = local.task_enabled && local.task_exposed && each.value["enabled"] && each.value["exposed"]
#
#  vpc_id = local.vpc_id
#
#  port             = each.value["ingress"]["port"]
#  protocol         = each.value["ingress"]["protocol"]
#  protocol_version = each.value["ingress"]["protocol_version"]
#
#  health_check_path                = each.value["health_check"]["path"]
#  health_check_protocol            = each.value["health_check"]["protocol"]
#  health_check_healthy_threshold   = each.value["health_check"]["healthy_threshold"]
#  health_check_unhealthy_threshold = each.value["health_check"]["unhealthy_threshold"]
#  health_check_interval            = each.value["health_check"]["interval"]
#  health_check_matcher             = each.value["health_check"]["matcher"]
#  health_check_timeout             = each.value["health_check"]["timeout"]
#
#  default_target_group_enabled = each.key == local.task_primary_container ? false : true
#  target_group_arn             = each.key == local.task_primary_container ? local.load_balancer_data["default_target_group_arn"] : ""
#
#  unauthenticated_listener_arns = local.load_balancer_data["listener_arns"]
#
#  unauthenticated_paths = [
#    "/*",
#  ]
#
#  unauthenticated_hosts = local.hostnames
#
#  unauthenticated_priority = local.container_priorities[each.key]
#
#  context = local.task_context
#}

locals {
  service_load_balancer_config = [
    for container_name, container_definition in local.task_containers_config : {
      container_name = lookup(container_definition, "name", container_name)
      container_port = try(container_definition["ingress"]["port"], null)
      elb_name       = null
      # target_group_arn = try(module.alb_ingress[container_name].target_group_arn, null)
      target_group_arn = local.load_balancer_data["default_target_group_arn"]
    } if local.task_enabled && local.task_exposed && container_definition["enabled"] && container_definition["exposed"]
  ]

  # sns_topic_arn      = local.task_environment_data["sns_topic_arn"]
  task_alarms_config = var.task_config["alarms"]
}

resource "aws_route53_record" "container_alias" {
  for_each = toset(local.route53_hostnames)

  zone_id = local.cluster_zone["zone_id"]
  name    = each.key
  type    = "A"

  alias {
    name                   = local.load_balancer_data["alb_dns_name"]
    zone_id                = local.load_balancer_data["alb_zone_id"]
    evaluate_target_health = true
  }
}

resource "cloudflare_record" "container_cloudflare_alias" {
  for_each = local.cloudflare_hostnames

  zone_id = local.cloudflare_zone
  name    = each.value
  value   = aws_route53_record.container_alias[each.key].fqdn
  type    = "CNAME"
  proxied = true
}

locals {
  container_load_balancer_targets = local.service_load_balancer_config
}