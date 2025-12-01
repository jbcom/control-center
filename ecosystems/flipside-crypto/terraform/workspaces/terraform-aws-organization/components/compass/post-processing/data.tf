data "aws_cloudwatch_log_groups" "codebuild" {
  log_group_name_prefix = "/aws/codebuild"
}
