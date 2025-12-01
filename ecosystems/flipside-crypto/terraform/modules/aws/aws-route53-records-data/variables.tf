variable "zone_ids" {
  type = list(string)

  description = "Zone IDs for the account"
}

variable "execution_role_arn" {
  type = string

  default = ""

  description = "Execution role ARN"
}
