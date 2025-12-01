locals {
  name = "compass"
  env  = "prod"

  tags = {
    ServiceName = "${local.name}-${local.env}"
    Env         = local.env
  }
}

resource "aws_ssm_parameter" "temporal_caconf" {
  name        = "/${local.name}/${local.env}/temporal/caconf"
  description = "CA Conf for Temporal"
  type        = "SecureString"
  value       = file("./ca.conf")

  tags = local.tags
}

resource "aws_ssm_parameter" "temporal_cakey" {
  name        = "/${local.name}/${local.env}/temporal/cakey"
  description = "CA Key for Temporal"
  type        = "SecureString"
  value       = file("./ca.key")

  tags = local.tags
}


resource "aws_ssm_parameter" "temporal_capem" {
  name        = "/${local.name}/${local.env}/temporal/capem"
  description = "CA PEM for Temporal"
  type        = "SecureString"
  value       = file("./ca.pem")

  tags = local.tags
}