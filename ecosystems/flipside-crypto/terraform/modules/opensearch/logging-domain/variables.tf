# Input variables for the OpenSearch logging domain post-configuration module

variable "opensearch_module" {
  description = "The entire OpenSearch Serverless module output"
  type        = any
}

variable "context" {
  description = "Context object with standard label variables"
  type        = any
}

variable "retention_days" {
  description = "Number of days to retain logs before deletion"
  type        = number
  default     = 365
}

variable "security_logs_retention_days" {
  description = "Number of days to retain security logs before moving to frozen state"
  type        = number
  default     = 730
}

variable "warm_transition_days" {
  description = "Number of days before transitioning logs to warm storage"
  type        = number
  default     = 30
}

variable "cold_transition_days" {
  description = "Number of days before transitioning logs to cold storage"
  type        = number
  default     = 90
}

variable "frozen_transition_days" {
  description = "Number of days before transitioning security logs to frozen storage"
  type        = number
  default     = 180
}

variable "index_shards" {
  description = "Number of shards for indices"
  type        = number
  default     = 3
}

variable "index_replicas" {
  description = "Number of replicas for indices"
  type        = number
  default     = 1
}

variable "sign_aws_requests" {
  description = "Whether to sign AWS requests for OpenSearch"
  type        = bool
  default     = true
}
