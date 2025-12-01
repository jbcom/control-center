variable "backend_name" {
  type = string

  description = "Backend name"
}

variable "dynamodb_table_name" {
  type = string

  default = ""

  description = "DynamoDB table name"
}

locals {
  dynamodb_table_name = var.dynamodb_table_name != "" ? var.dynamodb_table_name : var.backend_name
}

variable "tags" {
  type        = map(string)
  description = "Tags for the objects"
}

variable "enabled" {
  type        = bool
  description = "Whether to enable the state storage bucket"
  default     = true
}

variable "arn_format" {
  type        = string
  default     = "arn:aws"
  description = "ARN format to be used. May be changed to support deployment in GovCloud/China regions."
}

variable "billing_mode" {
  default     = "PAY_PER_REQUEST"
  description = "DynamoDB billing mode"
}

variable "read_capacity" {
  default     = null
  description = "DynamoDB read capacity units"
}

variable "write_capacity" {
  default     = null
  description = "DynamoDB write capacity units"
}

variable "access_logs" {
  type = any

  default = {}

  description = "Access logs configuration"
}

variable "attach_allow_organization_access_policy" {
  description = "Controls if S3 bucket should allow organization access"
  type        = bool
  default     = false
}

variable "attach_allow_organization_account_access_policy" {
  description = "Controls if S3 bucket should allow organization accounts access"
  type        = bool
  default     = true
}

variable "organization_account_access_policy_extra_account_ids" {
  description = "Accounts to remove from organization-level policies for individual member accounts"
  type        = list(string)
  default     = []
}

variable "organization_account_access_policy_extra_principals" {
  description = "Principals to add to the list of accounts granted access via the organization accounts access policy"
  type        = list(string)
  default     = []
}

variable "organization_access_policy_actions" {
  description = "Actions to allow for organization-level policies"
  type        = list(string)
  default = [
    "s3:ListBucket",
    "s3:GetObjectVersion",
    "s3:GetObject",
    "s3:GetBucketVersioning",
    "s3:GetBucketLocation",
  ]
}

variable "enable_versioning" {
  type = bool

  default = true

  description = "Whether to enable versioning"
}