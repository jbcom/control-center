# AWS Guard Lambda Deployment Module
# This module creates guard lambdas for AWS Organization governance
# Resources are organized across multiple files:
# - build.tf: Lambda function and EventBridge scheduling
# - deploy.tf: CodeDeploy, aliases, and deployment notifications
# - monitoring.tf: Dead letter queues and CloudWatch alarms
# - locals.tf: Configuration extraction and defaults
