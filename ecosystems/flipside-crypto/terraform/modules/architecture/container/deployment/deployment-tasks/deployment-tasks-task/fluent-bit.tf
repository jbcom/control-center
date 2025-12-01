module "container_definition_fluentbit" {
  source  = "cloudposse/ecs-container-definition/aws"
  version = "0.61.2"

  container_name  = "logrouter"
  container_image = "public.ecr.aws/aws-observability/aws-for-fluent-bit:stable"

  container_memory_reservation = 64

  essential = true

  firelens_configuration = {
    type = "fluentbit"
    options = {
      enable-ecs-log-metadata = true
      config-file-type        = "file"
      config-file-value       = "/fluent-bit/configs/parse-json.conf"
    }
  }
}

data "aws_iam_policy_document" "fluentbit_policy" {
  statement {
    actions = [
      "ecs:ListClusters",
      "ecs:ListContainerInstances",
      "ecs:DescribeContainerInstances",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }
}
