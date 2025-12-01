data "aws_region" "current" {}

locals {
  region = coalesce(var.aws_region, data.aws_region.current.name)
}