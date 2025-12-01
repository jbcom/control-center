module "security_group" {
  source = "../aws-security-group"

  security_group_name = var.security_group_name != "" ? var.security_group_name : var.broker_name
  vpc_id              = local.vpc_id

  rules = flatten(concat([
    for cidr_block in var.allowed_cidr_blocks : [
      {
        type        = "ingress"
        from_port   = 0
        to_port     = 65535
        protocol    = "tcp"
        cidr_blocks = [cidr_block]
        description = "Allow ingress traffic to AmazonMQ from ${cidr_block}"
      },
    ]
    ], [
    [
      {
        type        = "egress"
        from_port   = 0
        to_port     = 65535
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
        description = "Allow all outbound trafic"
      },
    ]
  ]))

  enabled = local.security_group_enabled

  tags = local.tags
}
