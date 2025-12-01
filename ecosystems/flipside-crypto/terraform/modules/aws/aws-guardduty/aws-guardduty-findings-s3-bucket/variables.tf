variable "assume_role_name" {
  description = "The role to assume in the delegated admin account."
  default     = "GuardDutyTerraformOrgRole"
}


# S3 Lifecycle variables
variable "s3_bucket_enable_object_transition_to_glacier" {
  default = true
}

variable "s3_bucket_object_transition_to_glacier_after_days" {
  default = 365
}

variable "s3_bucket_enable_object_deletion" {
  default = false
}

variable "s3_bucket_object_deletion_after_days" {
  default = 1095
}

variable "context" {
  type = any

  description = "Context data"
}