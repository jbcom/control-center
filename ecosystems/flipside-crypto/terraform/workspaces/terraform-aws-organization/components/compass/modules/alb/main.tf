
##
## Load Balancer
##
##

terraform {
  required_providers {
    cloudflare = {
      source  = "registry.terraform.io/cloudflare/cloudflare"
      version = "~> 3.33.1"
    }
  }
}

# VPC
data "aws_vpc" "vpc" {
  tags = {
    Name = var.vpc_name
  }
}

# Subnets
data "aws_subnets" "public_ids" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }

  tags = {
    Tier = "public"
  }
}

data "aws_subnet" "public" {
  for_each = toset(data.aws_subnets.public_ids.ids)
  id       = each.value
}

# Security Groups
data "aws_security_group" "egress_all" {
  name = var.sg_egress_all_name
}

data "aws_security_group" "http" {
  name = var.sg_http_name
}

data "aws_security_group" "https" {
  name = var.sg_https_name
}

resource "aws_lb_target_group" "rpc" {
  name        = "${var.name}-${var.env}-rpc"
  port        = var.rpc_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.aws_vpc.vpc.id

  health_check {
    enabled = true
    path    = var.health_check_path
  }

}

resource "aws_alb" "rpc" {
  name               = "${var.name}-${var.env}-rpc-lb"
  internal           = false
  load_balancer_type = "application"

  subnets = tolist([for s in data.aws_subnet.public : s.id])

  security_groups = [
    data.aws_security_group.egress_all.id,
    data.aws_security_group.http.id,
    data.aws_security_group.https.id
  ]
}


resource "aws_alb_listener" "rpc_http" {
  load_balancer_arn = aws_alb.rpc.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

data "cloudflare_zone" "zone" {
  name = var.cloudflare_zone
}

resource "cloudflare_record" "subdomain" {
  zone_id = data.cloudflare_zone.zone.id
  name    = var.subdomain
  value   = aws_alb.rpc.dns_name
  type    = "CNAME"
  ttl     = 3600
}

# # These comments are here so Terraform doesn't try to create the listener
# # before we have a valid certificate.
resource "aws_alb_listener" "rpc_https" {
  load_balancer_arn = aws_alb.rpc.arn
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.rpc.arn
  }
}