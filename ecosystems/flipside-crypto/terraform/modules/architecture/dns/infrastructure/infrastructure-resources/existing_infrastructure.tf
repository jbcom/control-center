variable "existing_infrastructure" {
  type = any

  default = {}

  description = "Existing infrastructure data to merge in"
}

locals {
  existing_infrastructure_data = var.existing_infrastructure
}