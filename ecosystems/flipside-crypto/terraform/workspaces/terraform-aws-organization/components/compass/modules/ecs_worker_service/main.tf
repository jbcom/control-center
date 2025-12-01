
# ECS Cluster
data "aws_ecs_cluster" "cluster" {
  cluster_name = var.cluster_name
}

# EFS Storage
data "aws_efs_file_system" "efs" {
  tags = {
    Name = var.efs_name
  }
}

# ECR
data "aws_ecr_repository" "worker" {
  name = var.ecr_repository_name
}

# IAM Role
data "aws_iam_role" "task_execution_role" {
  name = var.iam_task_execution_role_name
}

# Security Groups
data "aws_security_group" "egress_all" {
  name = var.sg_egress_all_name
}

data "aws_security_group" "efs" {
  name = var.sg_efs_mount_target_name
}

# VPC
data "aws_vpc" "vpc" {
  tags = {
    Name = var.vpc_name
  }
}

# Subnets
data "aws_subnets" "private_ids" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }

  tags = {
    Tier = "private"
  }
}

data "aws_subnet" "private" {
  for_each = toset(data.aws_subnets.private_ids.ids)
  id       = each.value
}

# Datadog API Key
data "aws_ssm_parameter" "datadog_api_key" {
  name = element(split("parameter", var.ssm_arn_datadog_api_key), 1)
}


##
## ECS Service Compass Workers
##
##
resource "aws_ecs_service" "workers" {
  name            = "${var.name}-${var.env}-workers"
  task_definition = aws_ecs_task_definition.workers.arn
  cluster         = data.aws_ecs_cluster.cluster.id
  launch_type     = "FARGATE"
  desired_count   = var.service_count

  network_configuration {
    assign_public_ip = false

    # security_groups = [
    #   var.egress_all_sg_id,
    #   var.efs_mount_target_sg_id,
    # ]

    security_groups = [
      data.aws_security_group.egress_all.id,
      data.aws_security_group.efs.id
    ]

    subnets = [for s in data.aws_subnet.private : s.id]

  }
}

resource "aws_cloudwatch_log_group" "workers_datadog_logs" {
  name = "/ecs/${var.name}-${var.env}-workers/datadog-agent"
}

# Task Definition
resource "aws_ecs_task_definition" "workers" {
  family = "${var.name}-${var.env}-workers"

  execution_role_arn = data.aws_iam_role.task_execution_role.arn

  container_definitions = <<EOF
  [
    {
      "essential": true,
      "image": "amazon/aws-for-fluent-bit:latest",
      "name": "${var.name}-${var.env}-logrouter",
      "firelensConfiguration": {
        "type": "fluentbit",
        "options": {
          "enable-ecs-log-metadata": "true"
        }
      }
    },
    {
      "name": "${var.name}-${var.env}-worker",
      "image": "${data.aws_ecr_repository.worker.repository_url}:${var.image_tag}",
      "command": ["yarn", "--cwd", "apps/workers", "start"],
      "environment": [
        {"name": "QUERY_RESULT_DIR", "value": "${var.query_run_results_dir}"},
        {"name": "NODE_ENV", "value": "${var.env}"}
      ],
       "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "${var.ssm_arn_app_db_write_url}"
        },
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "${var.ssm_arn_access_key_id}"
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "valueFrom": "${var.ssm_arn_secret_access_key}"
        },
        {
          "name": "ENCRYPTION_KEY",
          "valueFrom": "${var.ssm_arn_data_source_encryption_key}"
        },
        {
          "name": "SENTRY_DSN_WORKERS",
          "valueFrom": "${var.ssm_arn_sentry_dsn_workers}"
        },
        {
          "name": "DATADOG_API_KEY",
          "valueFrom": "${var.ssm_arn_datadog_api_key}"
        },
        {
          "name": "FIREHOSE_DELIVERY_STREAM",
          "valueFrom": "${var.ssm_arn_firehose_delivery_stream}"
        }
      ],
      "mountPoints": [
          {
              "containerPath": "${var.query_run_results_dir}",
              "sourceVolume": "${var.mounted_volume_name}"
          }
      ],
      "logConfiguration": {
        "logDriver": "awsfirelens",
        "options": {
            "Name": "datadog",
            "apiKey": "${data.aws_ssm_parameter.datadog_api_key.value}",
            "dd_service":  "${var.name}-${var.env}-worker",
            "dd_source": "httpd",
            "dd_tags": "name=${var.name},env=${var.env}",
            "TLS": "on",
            "provider": "ecs"
        }
      }
    },
    {
        "name": "${var.name}-${var.env}-worker-datadog-agent",
        "image": "datadog/agent:latest",
        "cpu": 10,
        "memory": 256,
        "mountPoints": [],
        "environment": [
            {
                "name": "ECS_FARGATE",
                "value": "true"
            },
            {
                "name": "DD_PROCESS_AGENT_ENABLED",
                "value": "true"
            },
            {
                "name": "DD_DOGSTATSD_NON_LOCAL_TRAFFIC",
                "value": "true"
            }
        ],
        "secrets": [
          {
            "name": "DD_API_KEY",
            "valueFrom": "${var.ssm_arn_datadog_api_key}"
          }
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
              "awslogs-group": "${aws_cloudwatch_log_group.workers_datadog_logs.name}",
              "awslogs-region": "${var.aws_region}",
              "awslogs-stream-prefix": "ecs"
            }
        }
    }
  ]
  EOF

  # These are the minimum values for Fargate containers.
  cpu                      = var.cpu
  memory                   = var.memory
  requires_compatibilities = ["FARGATE"]

  # This is required for Fargate containers (more on this later).
  network_mode = "awsvpc"

  volume {
    name = var.mounted_volume_name
    efs_volume_configuration {
      file_system_id = data.aws_efs_file_system.efs.id
      root_directory = "/"
    }
  }

}