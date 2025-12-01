data "aws_partition" "current" {}

locals {
  partition = data.aws_partition.current.partition
}

data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}
