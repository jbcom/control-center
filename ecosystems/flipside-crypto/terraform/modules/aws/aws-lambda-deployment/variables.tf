# Lambda Function Configuration Variables
variable "function_name" {
  type        = string
  default     = null
  description = "Name of the Lambda function. If not provided, will use the module name with context"
}

variable "description" {
  type        = string
  default     = ""
  description = "Description of the Lambda function"
}

variable "handler" {
  type        = string
  default     = ""
  description = "Lambda Function entrypoint in your code. Required for package_type=Zip"
}

variable "runtime" {
  type        = string
  default     = ""
  description = "Lambda Function runtime. Required for package_type=Zip"
}

variable "architectures" {
  type        = list(string)
  default     = ["x86_64"]
  description = "Instruction set architecture for your Lambda function. Valid values are [\"x86_64\"] and [\"arm64\"]"
}

variable "memory_size" {
  type        = number
  default     = 128
  description = "Amount of memory in MB your Lambda Function can use at runtime"
}

variable "timeout" {
  type        = number
  default     = 3
  description = "Amount of time your Lambda Function has to run in seconds"
}

variable "ephemeral_storage_size" {
  type        = number
  default     = 512
  description = "Amount of ephemeral storage (/tmp) in MB your Lambda Function can use at runtime"
}

variable "environment_variables" {
  type        = map(string)
  default     = {}
  description = "Map of environment variables for the Lambda function"
}

variable "publish" {
  type        = bool
  default     = true
  description = "Whether to publish creation/change as new Lambda Function Version"
}

variable "reserved_concurrent_executions" {
  type        = number
  default     = -1
  description = "Amount of reserved concurrent executions for this lambda function"
}

variable "layers" {
  type        = list(string)
  default     = null
  description = "List of Lambda Layer Version ARNs to attach to your Lambda Function"
}

variable "tracing_mode" {
  type        = string
  default     = "Active"
  description = "Tracing mode for Lambda function. Valid values: PassThrough or Active"
}

# kms_key_arn variable moved to global_variables.tf to avoid duplication

# Lambda@Edge specific variables
variable "lambda_at_edge" {
  type        = bool
  default     = false
  description = "Set this to true if using Lambda@Edge, to enable publishing, limit the timeout, and allow edgelambda.amazonaws.com to invoke the function"
}

variable "lambda_at_edge_logs_all_regions" {
  type        = bool
  default     = true
  description = "Whether to specify a wildcard in IAM policy used by Lambda@Edge to allow logging in all regions"
}

# Package Type and Source Configuration
variable "package_type" {
  type        = string
  default     = "Zip"
  description = "Lambda deployment package type. Valid values are Zip and Image"
}

variable "source_path" {
  type        = any
  default     = null
  description = "Path to the function's source code. Required if creating package locally"
}

variable "local_existing_package" {
  type        = string
  default     = null
  description = "Path to an existing zip-file to use for the Lambda function"
}

variable "s3_existing_package" {
  type        = map(string)
  default     = null
  description = "Map with S3 existing package location. Should contain bucket, key, version"
}

variable "image_uri" {
  type        = string
  default     = null
  description = "ECR image URI containing the function's deployment package"
}

variable "image_config_entry_point" {
  type        = list(string)
  default     = []
  description = "Entry point for the docker image"
}

variable "image_config_command" {
  type        = list(string)
  default     = []
  description = "CMD for the docker image"
}

variable "image_config_working_directory" {
  type        = string
  default     = null
  description = "Working directory for the docker image"
}

# VPC Configuration
variable "vpc_subnet_ids" {
  type        = list(string)
  default     = null
  description = "List of subnet IDs when Lambda should run in a VPC"
}

variable "vpc_security_group_ids" {
  type        = list(string)
  default     = null
  description = "List of security group IDs when Lambda should run in a VPC"
}

variable "attach_network_policy" {
  type        = bool
  default     = false
  description = "Controls whether VPC policy should be added to IAM role for Lambda Function"
}

# IAM Role Configuration
variable "create_role" {
  type        = bool
  default     = true
  description = "Controls whether IAM role for Lambda Function should be created"
}

variable "lambda_role" {
  type        = string
  default     = ""
  description = "IAM role ARN attached to the Lambda Function. This governs both who/what can invoke your Lambda Function, as well as what resources our Lambda Function has access to"
}

variable "role_name" {
  type        = string
  default     = null
  description = "Name of IAM role to use for Lambda Function"
}

variable "role_description" {
  type        = string
  default     = null
  description = "Description of IAM role to use for Lambda Function"
}

variable "role_path" {
  type        = string
  default     = null
  description = "Path of IAM role to use for Lambda Function"
}

variable "role_permissions_boundary" {
  type        = string
  default     = null
  description = "The ARN of the policy that is used to set the permissions boundary for the IAM role used by Lambda Function"
}

variable "role_tags" {
  type        = map(string)
  default     = {}
  description = "A map of tags to assign to IAM role"
}

variable "policy_statements" {
  type        = any
  default     = {}
  description = "Map of dynamic policy statements to attach to Lambda Function role"
}

variable "attach_policy_statements" {
  type        = bool
  default     = false
  description = "Controls whether policy_statements should be added to IAM role for Lambda Function"
}

variable "attach_cloudwatch_logs_policy" {
  type        = bool
  default     = true
  description = "Controls whether CloudWatch Logs policy should be added to IAM role for Lambda Function"
}

variable "attach_dead_letter_policy" {
  type        = bool
  default     = false
  description = "Controls whether SNS/SQS dead letter notification policy should be added to IAM role for Lambda Function"
}

variable "attach_tracing_policy" {
  type        = bool
  default     = false
  description = "Controls whether X-Ray tracing policy should be added to IAM role for Lambda Function"
}

variable "dead_letter_target_arn" {
  type        = string
  default     = null
  description = "ARN of an SNS topic or SQS queue to notify when an invocation fails"
}

variable "trusted_entities" {
  type        = list(string)
  default     = []
  description = "List of additional trusted entities for assuming Lambda Function role (trust relationship)"
}

# CloudWatch Logs Configuration
variable "cloudwatch_logs_retention_in_days" {
  type        = number
  default     = 30
  description = "Specifies the number of days you want to retain log events in the Lambda function log group"
}

variable "cloudwatch_logs_kms_key_id" {
  type        = string
  default     = null
  description = "The ARN of the KMS Key to use when encrypting log data"
}

variable "use_existing_cloudwatch_log_group" {
  type        = bool
  default     = false
  description = "Whether to use an existing CloudWatch log group or create new"
}

# Deployment Configuration
variable "create_alias" {
  type        = bool
  default     = true
  description = "Whether to create a Lambda function alias"
}

variable "alias_name" {
  type        = string
  default     = "current"
  description = "Name for the alias"
}

variable "create_version_alias" {
  type        = bool
  default     = true
  description = "Whether to create a version alias"
}

variable "create_deploy" {
  type        = bool
  default     = true
  description = "Whether to create CodeDeploy resources for Lambda deployment"
}

variable "deployment_config_name" {
  type        = string
  default     = "CodeDeployDefault.LambdaCanary10Percent5Minutes"
  description = "Name of deployment config to use"
}

variable "deployment_group_name" {
  type        = string
  default     = null
  description = "Name of deployment group to use"
}

variable "auto_rollback_enabled" {
  type        = bool
  default     = true
  description = "Indicates whether a defined automatic rollback configuration is currently enabled"
}

variable "auto_rollback_events" {
  type        = list(string)
  default     = ["DEPLOYMENT_FAILURE", "DEPLOYMENT_STOP_ON_ALARM"]
  description = "List of event types that trigger a rollback"
}

# ECR Repository Configuration
variable "create_ecr_repository" {
  type        = bool
  default     = false
  description = "Controls whether ECR repository for Lambda image should be created"
}

variable "ecr_repository_name" {
  type        = string
  default     = null
  description = "Name of ECR repository to use or to create"
}

variable "ecr_repository_lifecycle_policy" {
  type        = string
  default     = null
  description = "JSON formatted ECR lifecycle policy"
}

variable "ecr_image_tag_mutability" {
  type        = string
  default     = "MUTABLE"
  description = "The tag mutability setting for the repository. Must be one of: MUTABLE or IMMUTABLE"
}

variable "ecr_scan_on_push" {
  type        = bool
  default     = true
  description = "Indicates whether images are scanned after being pushed to the repository"
}

variable "ecr_force_delete" {
  type        = bool
  default     = true
  description = "If true, will delete the repository even if it contains images"
}

variable "ecr_repository_tags" {
  type        = map(string)
  default     = {}
  description = "A map of tags to assign to ECR repository"
}

# Docker Build Configuration
variable "create_docker_build" {
  type        = bool
  default     = false
  description = "Controls whether to build Docker image for Lambda function"
}

variable "docker_file_path" {
  type        = string
  default     = "Dockerfile"
  description = "Path to Dockerfile in source package"
}

# The following variables have been removed as they are not supported by the terraform-aws-modules/lambda/aws//modules/docker-build module:
# - docker_build_root
# - docker_image
# - docker_with_ssh_agent
# - docker_additional_options

variable "build_args" {
  type        = map(string)
  default     = {}
  description = "A map of Docker build arguments"
}

variable "image_tag" {
  type        = string
  default     = null
  description = "Image tag to use. If not specified current timestamp in format 'YYYYMMDDhhmmss' will be used"
}

variable "use_image_tag" {
  type        = bool
  default     = true
  description = "Controls whether to use image tag in ECR repository URI"
}

# Function URL Configuration
variable "create_lambda_function_url" {
  type        = bool
  default     = false
  description = "Controls whether the Lambda Function URL resource should be created"
}

variable "authorization_type" {
  type        = string
  default     = "NONE"
  description = "The type of authentication that the Lambda Function URL uses. Set to 'AWS_IAM' to restrict access to authenticated IAM users only. Set to 'NONE' to bypass IAM authentication and create a public endpoint"
}

variable "cors" {
  type        = any
  default     = {}
  description = "CORS settings to be used by the Lambda Function URL"
}

variable "invoke_mode" {
  type        = string
  default     = null
  description = "Invoke mode of the Lambda Function URL. Valid values are BUFFERED (default) and RESPONSE_STREAM"
}

# Async Event Configuration
variable "create_async_event_config" {
  type        = bool
  default     = false
  description = "Controls whether async event configuration for Lambda Function/Alias should be created"
}

variable "maximum_event_age_in_seconds" {
  type        = number
  default     = null
  description = "Maximum age of a request that Lambda sends to a function for processing in seconds"
}

variable "maximum_retry_attempts" {
  type        = number
  default     = null
  description = "Maximum number of times to retry when the function returns an error"
}

variable "destination_on_failure" {
  type        = string
  default     = null
  description = "Amazon Resource Name (ARN) of the destination resource for failed asynchronous invocations"
}

variable "destination_on_success" {
  type        = string
  default     = null
  description = "Amazon Resource Name (ARN) of the destination resource for successful asynchronous invocations"
}

# Event Source Mapping
variable "event_source_mapping" {
  type        = any
  default     = {}
  description = "Map of event source mapping"
}

# Allowed Triggers
variable "allowed_triggers" {
  type        = map(any)
  default     = {}
  description = "Map of allowed triggers to create Lambda permissions"
}

variable "create_current_version_allowed_triggers" {
  type        = bool
  default     = true
  description = "Whether to allow triggers on current version of Lambda Function (this will revoke permissions from previous version because Terraform manages only current resources)"
}

variable "create_unqualified_alias_allowed_triggers" {
  type        = bool
  default     = true
  description = "Whether to allow triggers on unqualified alias pointing to $LATEST version"
}

# Provisioned Concurrency
variable "provisioned_concurrent_executions" {
  type        = number
  default     = -1
  description = "Amount of capacity to allocate. Set to 1 or greater to enable, or set to 0 to disable provisioned concurrency"
}

# Logging Configuration
variable "logging_log_format" {
  type        = string
  default     = "JSON"
  description = "The log format of the Lambda Function. Valid values are 'JSON' or 'Text'"
}

variable "logging_application_log_level" {
  type        = string
  default     = "INFO"
  description = "The application log level of the Lambda Function. Valid values are 'TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', or 'FATAL'"
}

variable "logging_system_log_level" {
  type        = string
  default     = "INFO"
  description = "The system log level of the Lambda Function. Valid values are 'DEBUG', 'INFO', or 'WARN'"
}

# File System Configuration
variable "file_system_arn" {
  type        = string
  default     = null
  description = "The Amazon Resource Name (ARN) of the Amazon EFS Access Point that provides access to the file system"
}

variable "file_system_local_mount_path" {
  type        = string
  default     = null
  description = "The path where the function can access the file system, starting with /mnt/"
}

# Timeouts
variable "timeouts" {
  type        = map(string)
  default     = {}
  description = "Define maximum timeout for creating, updating, and deleting Lambda Function resources"
}

# Skip Destroy
variable "skip_destroy" {
  type        = bool
  default     = false
  description = "Set to true if you do not wish the function to be deleted at destroy time, and instead just remove the function from the Terraform state"
}

# Function Tags
variable "function_tags" {
  type        = map(string)
  default     = {}
  description = "A map of tags to assign only to the lambda function"
}

# CloudWatch Alarms
variable "create_cloudwatch_alarm" {
  type        = bool
  default     = false
  description = "Controls whether CloudWatch Alarm for Lambda errors should be created"
}

variable "cloudwatch_alarm_name" {
  type        = string
  default     = null
  description = "Name for the CloudWatch Alarm. If not provided, will use the function name with '-errors' suffix"
}

variable "cloudwatch_alarm_description" {
  type        = string
  default     = null
  description = "Description for the CloudWatch Alarm. If not provided, will use a default description"
}

variable "cloudwatch_alarm_threshold" {
  type        = number
  default     = 0
  description = "The threshold for the CloudWatch Alarm. Default is 0 (any error will trigger the alarm)"
}

variable "cloudwatch_alarm_evaluation_periods" {
  type        = number
  default     = 1
  description = "The number of periods over which data is compared to the threshold"
}

variable "cloudwatch_alarm_period" {
  type        = number
  default     = 60
  description = "The period in seconds over which the statistic is applied"
}

variable "cloudwatch_alarm_statistic" {
  type        = string
  default     = "Sum"
  description = "The statistic to apply to the alarm's metric. Valid values are: SampleCount, Average, Sum, Minimum, Maximum"
}

variable "cloudwatch_alarm_comparison_operator" {
  type        = string
  default     = "GreaterThanThreshold"
  description = "The arithmetic operation to use when comparing the specified statistic and threshold"
}

variable "cloudwatch_alarm_tags" {
  type        = map(string)
  default     = {}
  description = "A map of tags to assign to the CloudWatch Alarm"
}

# SSM Parameters
variable "create_ssm_parameters" {
  type        = bool
  default     = false
  description = "Controls whether SSM Parameters should be created"
}

variable "use_ssm_parameter_prefix" {
  type        = bool
  default     = false
  description = "Controls whether to use a prefix for SSM Parameter names"
}

variable "ssm_parameters" {
  type = map(object({
    name        = optional(string, null)
    value       = string
    type        = optional(string, "SecureString")
    description = optional(string, "Managed by Terraform")
    overwrite   = optional(bool, true)
    key_id      = optional(string, null)
  }))
  default     = {}
  description = "Map of SSM Parameters to create. The key is used as the parameter name if name is not provided. The value is an object with name (optional), value, type, description, overwrite, and key_id"
  sensitive   = true
}

variable "ssm_parameter_prefix" {
  type        = string
  default     = null
  description = "Prefix to add to all SSM Parameter names when use_ssm_parameter_prefix is true. If not provided but use_ssm_parameter_prefix is true, will use /{function_name}/"
}

# Additional IAM Role Policy Attachments
variable "additional_iam_role_policy_arns" {
  type        = list(string)
  default     = []
  description = "List of additional IAM policy ARNs to attach to the Lambda execution role"
}

# Additional Lambda Permissions
variable "additional_lambda_permissions" {
  type = list(object({
    statement_id       = string
    action             = string
    principal          = string
    source_arn         = optional(string, null)
    source_account     = optional(string, null)
    event_source_token = optional(string, null)
    qualifier          = optional(string, null)
  }))
  default     = []
  description = "List of additional Lambda permissions to create"
}
