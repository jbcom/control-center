locals {
  task_config = var.deployment_config["task"]
}

data "aws_iam_policy_document" "secret_policy_document" {
  for_each = {
    for secret_arn, task_identifiers in var.deployment_config["secrets"] : secret_arn => task_identifiers if length(task_identifiers) > 0
  }

  statement {
    principals {
      type        = "AWS"
      identifiers = each.value
    }

    actions = [
      "secretsmanager:*",
    ]

    resources = ["*"]
  }
}

resource "aws_secretsmanager_secret_policy" "secret_policy" {
  for_each = data.aws_iam_policy_document.secret_policy_document

  policy     = each.value.json
  secret_arn = each.key
}

resource "aws_security_group_rule" "alb" {
  for_each = local.task_config["task_launched"] && local.task_config["task_security_group_id"] != "" ? toset(local.task_config["unique_container_ports"]) : []

  description              = "Allow inbound traffic on port ${each.key} from ALB"
  type                     = "ingress"
  from_port                = split("/", each.key)[1]
  to_port                  = split("/", each.key)[1]
  protocol                 = split("/", each.key)[0]
  source_security_group_id = local.task_config["task_security_group_id"]
  security_group_id        = local.task_config["service_security_group_id"]
}

locals {
  task_policy_arn = local.task_config["task_policy_arn"]
}

resource "aws_iam_role_policy_attachment" "task_role" {
  policy_arn = local.task_policy_arn
  role       = local.task_config["task_role_name"]
}

resource "aws_iam_role_policy_attachment" "task_exec_role" {
  policy_arn = local.task_policy_arn
  role       = local.task_config["task_exec_role_name"]
}