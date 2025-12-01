# AWS Guard Lambda Deployment Module

This module deploys a single guard lambda function with all necessary supporting infrastructure for controlled, safe deployments in AWS organization governance scenarios.

## Features

- **Complete Lambda Deployment**: Lambda function with proper IAM permissions, logging, and error handling
- **Controlled Deployments**: Uses AWS CodeDeploy with gradual rollout and automatic rollback
- **Scheduled Execution**: EventBridge rules for automated guard execution
- **Monitoring & Alerting**: CloudWatch alarms and SNS notifications for deployment events
- **Dead Letter Queue**: SQS queue for failed executions with monitoring
- **Version Management**: Lambda aliases for blue/green deployments

## Usage

```hcl
module "iam_user_cleanup_guard" {
  source = "../../modules/aws-guard-lambda-deployment"

  guard_name  = "iam-user-cleanup"
  description = "Guard lambda to manage inactive IAM users in the management account"
  
  # Lambda configuration
  handler     = "lambda_function.lambda_handler"
  runtime     = "python3.13"
  timeout     = 300
  memory_size = 512
  
  # Source code path (absolute path to lambda directory)
  source_path = "${path.module}/lambdas/iam-user-cleanup"
  
  # Schedule configuration
  schedule_expression  = "rate(1 day)"
  schedule_description = "Trigger IAM user cleanup guard lambda daily"
  
  # Environment variables
  environment_variables = {
    ADMIN_BOT_USERS      = jsonencode(local.context.admin_bot_users)
    LOG_LEVEL           = "INFO"
    DRY_RUN             = "false"
    DAYS_TO_DISABLE_KEYS = "90"
    DAYS_TO_DISABLE_USER = "180"
    DAYS_TO_DELETE_USER  = "270"
  }
  
  # IAM policy statements
  policy_statements = {
    iam_read = {
      effect = "Allow"
      actions = [
        "iam:ListUsers",
        "iam:GetUser",
        "iam:ListAccessKeys"
      ]
      resources = ["*"]
    }
    iam_write = {
      effect = "Allow"
      actions = [
        "iam:UpdateAccessKey",
        "iam:DeleteAccessKey",
        "iam:DeleteUser"
      ]
      resources = ["arn:aws:iam::${local.account_id}:user/*"]
      condition = {
        StringNotEquals = {
          "aws:PrincipalArn" = local.context.admin_bot_users
        }
      }
    }
  }
  
  # Guard-specific tags
  function_tags = {
    GuardType = "IAM-Cleanup"
    Schedule  = "Daily"
  }

  # SNS topic ARNs for notifications
  deployment_notifications_topic_arn = aws_sns_topic.guard_deployment_notifications.arn
  deployment_failures_topic_arn      = aws_sns_topic.guard_deployment_failures.arn

  # Common variables
  environment    = local.environment
  workspace_name = local.workspace_name
}
```

## Architecture

The module creates the following resources for each guard:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│  Lambda Alias    │───▶│ Lambda Function │
│      Rule       │    │    (current)     │    │   (versioned)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   CodeDeploy     │    │  CloudWatch     │
                       │   Application    │    │     Logs        │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  SNS Topics      │    │   SQS DLQ       │
                       │ (notifications)  │    │ (failed exec)   │
                       └──────────────────┘    └─────────────────┘
```

## Deployment Process

1. **Code Change**: Lambda source code is updated
2. **Version Creation**: New lambda version is automatically created
3. **CodeDeploy Trigger**: Deployment starts with SNS notification
4. **Gradual Rollout**: Traffic shifts 10% every 5 minutes by default
5. **Monitoring**: CloudWatch monitors for errors during deployment
6. **Completion**: Success/failure notification sent via SNS

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.7 |
| aws | >= 6.0 |

## Providers

| Name | Version |
|------|---------|
| aws | >= 6.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| guard_lambda | terraform-aws-modules/lambda/aws | 8.0.1 |
| guard_alias | terraform-aws-modules/lambda/aws//modules/alias | 8.0.1 |
| guard_deploy | terraform-aws-modules/lambda/aws//modules/deploy | 8.0.1 |

## Resources

| Name | Type |
|------|------|
| aws_cloudwatch_event_rule.guard_schedule | resource |
| aws_cloudwatch_event_target.guard_target | resource |
| aws_cloudwatch_metric_alarm.guard_dlq_alarm | resource |
| aws_sqs_queue.guard_dlq | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| guard_name | Name of the guard lambda (e.g., 'iam-user-cleanup') | `string` | n/a | yes |
| description | Description of the guard lambda | `string` | n/a | yes |
| source_path | Absolute path to the lambda source code directory | `string` | n/a | yes |
| schedule_expression | EventBridge schedule expression (e.g., 'rate(1 day)') | `string` | n/a | yes |
| schedule_description | Description for the EventBridge schedule | `string` | n/a | yes |
| deployment_notifications_topic_arn | ARN of SNS topic for deployment notifications | `string` | n/a | yes |
| deployment_failures_topic_arn | ARN of SNS topic for deployment failure notifications | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| workspace_name | Workspace name | `string` | n/a | yes |
| handler | Lambda function handler | `string` | `"lambda_function.lambda_handler"` | no |
| runtime | Lambda runtime | `string` | `"python3.13"` | no |
| timeout | Lambda timeout in seconds | `number` | `300` | no |
| memory_size | Lambda memory size in MB | `number` | `512` | no |
| environment_variables | Environment variables for the lambda function | `map(string)` | `{}` | no |
| policy_statements | IAM policy statements for the lambda function | `map(object)` | `{}` | no |
| function_tags | Additional tags specific to this guard function | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| lambda_function_arn | The ARN of the Lambda Function |
| lambda_function_name | The name of the Lambda Function |
| lambda_alias_arn | The ARN of the Lambda alias |
| cloudwatch_log_group_name | The name of the Cloudwatch Log Group |
| dead_letter_queue_arn | The ARN of the dead letter queue |
| eventbridge_rule_arn | The ARN of the EventBridge rule |
| codedeploy_app_name | The name of the CodeDeploy application |

## Lambda Requirements

All lambda functions deployed with this module must follow these requirements:

- **Python 3.13**: Use Python 3.13 runtime
- **No uppercase types**: Use lowercase type hints (e.g., `list`, `dict`, `str`)
- **No Optional**: Do not use `Optional` type hints
- **Class-based implementation**: Implement as classes for better organization
- **requirements.txt**: Include dependencies in requirements.txt file

## Directory Structure

```
lambdas/
└── <guard-name>/
    ├── lambda_function.py    # Main lambda handler
    └── requirements.txt      # Python dependencies
```

## Security Considerations

- Lambda functions run with least privilege IAM permissions
- Admin bot users are protected through IAM conditions
- All actions are logged to CloudWatch
- Dead letter queues capture failed executions
- Gradual deployments prevent organization-wide impact

## Monitoring

The module provides comprehensive monitoring:

- **CloudWatch Logs**: All lambda executions are logged
- **Dead Letter Queue**: Failed executions are captured
- **CloudWatch Alarms**: DLQ messages trigger alarms
- **SNS Notifications**: Deployment events are reported
- **CodeDeploy Metrics**: Deployment success/failure tracking

## Adding New Guards

To add a new guard lambda:

1. Create lambda source code directory under `lambdas/`
2. Add module call in workspace main.tf
3. Configure guard-specific IAM permissions
4. Set appropriate schedule and environment variables
5. Deploy and monitor

## Examples

See the guards workspace for complete examples of guard lambda implementations.
