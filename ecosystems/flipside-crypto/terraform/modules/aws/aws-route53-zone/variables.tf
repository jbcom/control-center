variable "config" {
  type = object({
    name              = string
    comment           = optional(string, "Managed by Terraform")
    delegation_set_id = optional(string)
    force_destroy     = optional(bool, false)
    tags              = optional(map(string), {})
    vpcs              = optional(any, [])
  })

  description = "KMS key configuration"
}