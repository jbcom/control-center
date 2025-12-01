data "aws_ssoadmin_instances" "default" {}

locals {
  instance_arn = tolist(data.aws_ssoadmin_instances.default.arns)[0]
}