variable "group" {
  type = object({
    description = optional(string)

    google_group_name = optional(string)

    admins = optional(list(string), [])

    members = optional(list(string), [])

    owners = optional(list(string), [])

    group_admins = optional(list(string), [])

    group_members = optional(list(string), [])

    group_owners = optional(list(string), [])
  })

  description = "Google group config"
}

variable "context" {
  type = any

  description = "Context data"
}