data "aws_caller_identity" "current" {
  count = local.enabled_from_cloudposse_context ? 1 : 0
}

data "aws_partition" "current" {
  count = local.enabled_from_cloudposse_context ? 1 : 0
}

data "aws_region" "current" {
  count = local.enabled_from_cloudposse_context ? 1 : 0
}
