# OpenSearch Logging Domain Post-Configuration Module Outputs for Serverless

# OpenSearch collection properties
output "collection" {
  description = "OpenSearch Serverless collection properties"
  value = {
    id       = local.id
    endpoint = local.collection_endpoint
    region   = local.aws_region
  }
}

# Resource names (used for references by other modules)
output "ism_policies" {
  description = "Default ISM policy names (serverless might not use these)"
  value = {
    logs_retention          = "${local.id}-logs-retention"
    security_logs_retention = "${local.id}-security-logs-retention"
  }
}

output "ingest_pipelines" {
  description = "Default ingest pipeline names (serverless might not use these)"
  value = {
    cloudwatch_logs = "${local.id}-cloudwatch-logs"
    cloudtrail_logs = "${local.id}-cloudtrail-logs"
    vpc_flow_logs   = "${local.id}-vpc-flow-logs"
    s3_logs         = "${local.id}-s3-logs"
  }
}

output "index_templates" {
  description = "Default index template names (serverless might not use these)"
  value = {
    logs            = "${local.id}-logs"
    cloudtrail_logs = "${local.id}-cloudtrail-logs"
  }
}

# Suggested Index Patterns
output "suggested_index_patterns" {
  description = "Suggested index patterns for OpenSearch Dashboards"
  value = [
    "logs-*",                 # All logs
    "logs-*-cloudtrail-*",    # CloudTrail logs
    "logs-*-vpc-flow-logs-*", # VPC Flow logs
    "logs-*-lambda-*",        # Lambda logs
    "logs-*-rds-*",           # RDS logs
    "logs-*-s3-*",            # S3 logs 
    "logs-*-apigateway-*",    # API Gateway logs
    "logs-*-ecs-*",           # ECS logs 
    "logs-*-eks-*",           # EKS logs
    "logs-*-guardduty-*",     # GuardDuty findings
    "logs-*-cloudfront-*",    # CloudFront logs
    "logs-*-waf-*"            # WAF logs
  ]
}
