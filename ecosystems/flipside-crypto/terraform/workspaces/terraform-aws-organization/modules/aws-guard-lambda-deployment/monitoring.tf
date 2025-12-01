# Dead letter queue for failed lambda executions
resource "aws_sqs_queue" "guard_dlq" {
  count = local.enabled_from_cloudposse_context ? 1 : 0

  name                      = "${local.function_name}-dlq"
  message_retention_seconds = local.dlq_retention_seconds_from_repo_context

  tags = local.tags_from_cloudposse_context
}

# CloudWatch alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "guard_dlq_alarm" {
  count = local.enabled_from_cloudposse_context ? 1 : 0

  alarm_name          = "${local.function_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors failed ${local.function_name} guard executions"
  alarm_actions       = [] # Add SNS topic ARN here if you want notifications

  dimensions = {
    QueueName = aws_sqs_queue.guard_dlq[0].name
  }

  tags = local.tags_from_cloudposse_context
}
