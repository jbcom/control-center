locals {
  tags = {
    Name      = "${var.name}-${var.env}"
    Env       = var.env
    Terraform = "true"
  }
}

##
## ECS Cluster
##
##
resource "aws_ecs_cluster" "cluster" {
  name = "${var.name}-${var.env}"
}

##
## Permissions / Policies
##
##
# This is the role under which ECS will execute our task. This role becomes more important
# as we add integrations with other AWS services later on.

# The assume_role_policy field works with the following aws_iam_policy_document to allow
# ECS tasks to assume this role we're creating.
resource "aws_iam_role" "task_execution_role" {
  name               = "${var.name}-${var.env}-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_policy" "ssm_policy" {
  name        = "${var.name}-${var.env}-ssm-policy"
  path        = "/"
  description = "SSM policy for compass"

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ssm:GetParameters",
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}


data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Normally we'd prefer not to hardcode an ARN in our Terraform, but since this is
# an AWS-managed policy, it's okay.
data "aws_iam_policy" "ecs_task_execution_role" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy" "ssm_read" {
  arn = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
}


data "aws_iam_policy" "kinesis_firehose_full_access" {
  arn = "arn:aws:iam::aws:policy/AmazonKinesisFirehoseFullAccess"
}



# Attach the above policies to the execution role.
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role" {
  role       = aws_iam_role.task_execution_role.name
  policy_arn = data.aws_iam_policy.ecs_task_execution_role.arn
}

resource "aws_iam_role_policy_attachment" "ecs_ssm_read_role" {
  role       = aws_iam_role.task_execution_role.name
  policy_arn = data.aws_iam_policy.ssm_read.arn
}

resource "aws_iam_role_policy_attachment" "ecs_ssm" {
  role       = aws_iam_role.task_execution_role.name
  policy_arn = aws_iam_policy.ssm_policy.arn
}

resource "aws_iam_role_policy_attachment" "ecs_kinesis_firehose_full_access_role" {
  role       = aws_iam_role.task_execution_role.name
  policy_arn = data.aws_iam_policy.kinesis_firehose_full_access.arn
}

# IAM user for accessing the AWS console

resource "aws_iam_user" "user" {
  name = "${var.name}-${var.env}-user"
  path = "/system/"
}

resource "aws_iam_access_key" "default" {
  user = aws_iam_user.user.name
}

resource "aws_iam_user_policy_attachment" "user_ssm_read_policy" {
  user       = aws_iam_user.user.name
  policy_arn = data.aws_iam_policy.ssm_read.arn
}

resource "aws_iam_user_policy_attachment" "user_kinesis_firehose_full_policy" {
  user       = aws_iam_user.user.name
  policy_arn = data.aws_iam_policy.kinesis_firehose_full_access.arn
}


resource "aws_ssm_parameter" "access_key_id" {
  name        = "/${var.name}/${var.env}/services/access_key_id"
  description = "Service access key id"
  type        = "SecureString"
  value       = aws_iam_access_key.default.id

  tags = local.tags
}

resource "aws_ssm_parameter" "secret_access_key" {
  name        = "/${var.name}/${var.env}/services/secret_access_key"
  description = "Service secret access key"
  type        = "SecureString"
  value       = aws_iam_access_key.default.secret

  tags = local.tags
}

resource "aws_ssm_parameter" "data_source_encryption_key" {
  name        = "/${var.name}/${var.env}/services/data_sources/encryption_key"
  description = "Key to encrypt/decrypt data sources stored in the database."
  type        = "SecureString"
  value       = var.data_source_encryption_key

  tags = local.tags
}