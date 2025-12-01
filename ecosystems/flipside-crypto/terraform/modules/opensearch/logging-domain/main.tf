# OpenSearch Logging Domain Post-Configuration Module
# This module configures an existing OpenSearch domain with policies, pipelines, and templates

# Local variables
locals {
  id = var.context.id

  # Extract values from the opensearch_module
  collection_endpoint = var.opensearch_module.opensearch_serverless_collection_endpoint
  aws_region          = var.opensearch_module.aws_region
}

# Create ISM policy for log retention
resource "opensearch_ism_policy" "logs_retention" {
  policy_id = "${local.id}-logs-retention"
  body = jsonencode({
    policy = {
      description   = "Retention policy for logs collection",
      default_state = "hot",
      states = [
        {
          name    = "hot",
          actions = [],
          transitions = [
            {
              state_name = "warm",
              conditions = {
                min_index_age = "${var.warm_transition_days}d"
              }
            }
          ]
        },
        {
          name = "warm",
          actions = [
            {
              replica_count = {
                number_of_replicas = 1
              }
            }
          ],
          transitions = [
            {
              state_name = "cold",
              conditions = {
                min_index_age = "${var.cold_transition_days}d"
              }
            }
          ]
        },
        {
          name = "cold",
          actions = [
            {
              replica_count = {
                number_of_replicas = 0
              }
            }
          ],
          transitions = [
            {
              state_name = "delete",
              conditions = {
                min_index_age = "${var.retention_days}d"
              }
            }
          ]
        },
        {
          name = "delete",
          actions = [
            {
              delete = {}
            }
          ],
          transitions = []
        }
      ],
      ism_template = [
        {
          index_patterns = ["logs-*"],
          priority       = 100
        }
      ]
    }
  })
}

# Create ISM policy for security logs with longer retention
resource "opensearch_ism_policy" "security_logs_retention" {
  policy_id = "${local.id}-security-logs-retention"
  body = jsonencode({
    policy = {
      description   = "Retention policy for security logs collection with longer retention",
      default_state = "hot",
      states = [
        {
          name    = "hot",
          actions = [],
          transitions = [
            {
              state_name = "warm",
              conditions = {
                min_index_age = "${var.warm_transition_days}d"
              }
            }
          ]
        },
        {
          name = "warm",
          actions = [
            {
              replica_count = {
                number_of_replicas = 1
              }
            }
          ],
          transitions = [
            {
              state_name = "cold",
              conditions = {
                min_index_age = "${var.cold_transition_days}d"
              }
            }
          ]
        },
        {
          name = "cold",
          actions = [
            {
              replica_count = {
                number_of_replicas = 0
              }
            }
          ],
          transitions = [
            {
              state_name = "frozen",
              conditions = {
                min_index_age = "${var.frozen_transition_days}d"
              }
            }
          ]
        },
        {
          name        = "frozen",
          actions     = [],
          transitions = []
        }
      ],
      ism_template = [
        {
          index_patterns = ["logs-*-cloudtrail-*", "logs-*-security-*"],
          priority       = 200
        }
      ]
    }
  })
}

# Create ingest pipeline for CloudWatch Logs
resource "opensearch_ingest_pipeline" "cloudwatch_logs" {
  name = "${local.id}-cloudwatch-logs"
  body = jsonencode({
    description = "Pipeline for ingesting CloudWatch Logs (excluding CloudTrail)",
    processors = [
      {
        grok = {
          field    = "message",
          patterns = ["%%{TIMESTAMP_ISO8601:timestamp} %%{LOGLEVEL:level} %%{GREEDYDATA:message}"]
        }
      },
      {
        date = {
          field        = "timestamp",
          target_field = "@timestamp",
          formats      = ["yyyy-MM-dd'T'HH:mm:ss.SSSZ"]
        }
      }
    ]
  })
}

# Create ingest pipeline for CloudTrail Logs
resource "opensearch_ingest_pipeline" "cloudtrail_logs" {
  name = "${local.id}-cloudtrail-logs"
  body = jsonencode({
    description = "Pipeline for ingesting CloudTrail Logs",
    processors = [
      {
        json = {
          field = "message"
        }
      },
      {
        date = {
          field        = "eventTime",
          target_field = "@timestamp",
          formats      = ["yyyy-MM-dd'T'HH:mm:ss'Z'"]
        }
      }
    ]
  })
}

# Create ingest pipeline for VPC Flow Logs
resource "opensearch_ingest_pipeline" "vpc_flow_logs" {
  name = "${local.id}-vpc-flow-logs"
  body = jsonencode({
    description = "Pipeline for ingesting VPC Flow Logs",
    processors = [
      {
        grok = {
          field = "message",
          patterns = [
            "%%{NUMBER:version} %%{NUMBER:account_id} %%{NOTSPACE:interface_id} %%{NOTSPACE:srcaddr} %%{NOTSPACE:dstaddr} %%{NOTSPACE:srcport} %%{NOTSPACE:dstport} %%{NOTSPACE:protocol} %%{NOTSPACE:packets} %%{NOTSPACE:bytes} %%{NOTSPACE:start} %%{NOTSPACE:end} %%{NOTSPACE:action} %%{NOTSPACE:log_status}"
          ]
        }
      }
    ]
  })
}

# Create ingest pipeline for S3 Logs
resource "opensearch_ingest_pipeline" "s3_logs" {
  name = "${local.id}-s3-logs"
  body = jsonencode({
    description = "Pipeline for ingesting S3 Logs",
    processors = [
      {
        json = {
          field = "message"
        }
      },
      {
        date = {
          field        = "timestamp",
          target_field = "@timestamp",
          formats      = ["yyyy-MM-dd'T'HH:mm:ss.SSSZ"]
        }
      }
    ]
  })
}

# Use AWS data sources for additional information if needed
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
