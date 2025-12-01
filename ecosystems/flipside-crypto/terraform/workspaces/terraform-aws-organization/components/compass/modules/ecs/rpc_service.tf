

# ##
# ## ECS Service Query Engine RPC
# ##
# ##
# resource "aws_ecs_service" "rpc" {
#   name            = "${var.name}-${var.env}-rpc"
#   task_definition = aws_ecs_task_definition.rpc.arn
#   cluster         = aws_ecs_cluster.cluster.id
#   launch_type     = "FARGATE"
#   desired_count   = var.rpc_count

#   load_balancer {
#     target_group_arn = var.alb_target_group_arn
#     container_name   = "${var.name}-${var.env}-rpc"
#     container_port   = "${var.rpc_port}"
#   }

#   network_configuration {
#       assign_public_ip = false

#       security_groups = [
#         var.egress_all_sg_id,
#         var.ingress_rpc_sg_id,
#         var.efs_mount_target_sg_id,
#       ]

#       subnets = var.subnets
#   }
# }

# resource "aws_cloudwatch_log_group" "rpc_datadog_logs" {
#   name = "/ecs/${var.name}-${var.env}-rpc/datadog-agent"
# }

# # Task Definition
# resource "aws_ecs_task_definition" "rpc" {
#   family = "${var.name}-${var.env}-rpc"

#   execution_role_arn = aws_iam_role.task_execution_role.arn

#   container_definitions = <<EOF
#   [
#     {
#       "essential": true,
#       "image": "amazon/aws-for-fluent-bit:latest",
#       "name": "${var.name}-${var.env}-logrouter",
#       "firelensConfiguration": {
#         "type": "fluentbit",
#         "options": {
#           "enable-ecs-log-metadata": "true"
#         }
#       }
#     },
#     {
#       "name": "${var.name}-${var.env}-rpc",
#       "image": "${var.ecr_rpc_url}:${var.ecr_rpc_image_tag}",
#       "command": ["yarn", "--cwd", "apps/rpc", "start:server"],
#       "portMappings": [
#         {
#           "containerPort": ${var.rpc_port}
#         }
#       ],
#       "mountPoints": [
#           {
#               "containerPath": "${var.query_run_results_dir}",
#               "sourceVolume": "${var.mounted_volume_name}"
#           }
#       ],
#       "environment": [
#         {"name": "DATABASE_URL", "value": "${var.database_url}/${var.database_name}"},
#         {"name": "AWS_ACCESS_KEY_ID", "value": "${aws_iam_access_key.default.id}"},
#         {"name": "AWS_SECRET_ACCESS_KEY", "value": "${aws_iam_access_key.default.secret}"},
#         {"name": "ENCRYPTION_KEY", "value": "${var.data_sources_encryption_key}"},
#         {"name": "QUERY_RESULT_DIR", "value": "${var.query_run_results_dir}"},
#         {"name": "NODE_ENV", "value": "${var.env}"},
#         {"name": "FIREHOSE_DELIVERY_STREAM", "value": "${var.firehose_delivery_stream}"},
#         {"name": "SENTRY_DSN_RPC", "value": "${var.sentry_dsn_rpc}"},
#         {"name": "DATADOG_API_KEY", "value": "${var.datadog_api_key}"}
#       ],
#       "logConfiguration": {
#         "logDriver": "awsfirelens",
#         "options": {
#             "Name": "datadog",
#             "apiKey": "${var.datadog_api_key}",
#             "dd_service":  "${var.name}-${var.env}-rpc",
#             "dd_source": "httpd",
#             "dd_tags": "name=${var.name},env=${var.env}",
#             "TLS": "on",
#             "provider": "ecs"
#         }
#       }
#     },
#     {
#         "name": "${var.name}-${var.env}-rpc-datadog-agent",
#         "image": "datadog/agent:latest",
#         "cpu": 10,
#         "memory": 256,
#         "mountPoints": [],
#         "environment": [
#             {
#                 "name": "ECS_FARGATE",
#                 "value": "true"
#             },
#             {
#                 "name": "DD_PROCESS_AGENT_ENABLED",
#                 "value": "true"
#             },
#             {
#                 "name": "DD_DOGSTATSD_NON_LOCAL_TRAFFIC",
#                 "value": "true"
#             },
#             {
#                 "name": "DD_API_KEY",
#                 "value": "${var.datadog_api_key}"
#             }
#         ],
#         "logConfiguration": {
#             "logDriver": "awslogs",
#             "options": {
#               "awslogs-group": "${aws_cloudwatch_log_group.rpc_datadog_logs.name}",
#               "awslogs-region": "${var.aws_region}",
#               "awslogs-stream-prefix": "ecs"
#             }
#         }
#     }
#   ]
#   EOF

#   # These are the minimum values for Fargate containers.
#   cpu = var.rpc_cpu
#   memory = var.rpc_memory
#   requires_compatibilities = ["FARGATE"]

#   # This is required for Fargate containers (more on this later).
#   network_mode = "awsvpc"

#   volume {
#     name      = var.mounted_volume_name
#     efs_volume_configuration {
#       file_system_id = var.efs_id
#       root_directory = "/"
#     }
#   }

#   # runtime_platform {
#   #   operating_system_family = "LINUX"
#   #   cpu_architecture        = "X86_64"
#   # }
# }