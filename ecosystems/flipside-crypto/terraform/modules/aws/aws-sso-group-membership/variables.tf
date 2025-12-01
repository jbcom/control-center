variable "config" {
  type = object({
    aws_identitystore_group_id = string

    aws_identitystore_members = optional(list(string), [])
  })

  description = "Membership config"
}