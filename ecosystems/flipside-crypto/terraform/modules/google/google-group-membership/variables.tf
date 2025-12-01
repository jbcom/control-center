variable "config" {
  type = object({
    google_group_id = optional(string)

    admins  = optional(list(string), [])
    members = optional(list(string), [])
    owners  = optional(list(string), [])

    group_admins  = optional(list(string), [])
    group_members = optional(list(string), [])
    group_owners  = optional(list(string), [])

    external_google_members       = optional(list(string), [])
    external_google_group_members = optional(list(string), [])
    external_google_admins        = optional(list(string), [])
    external_google_group_admins  = optional(list(string), [])
    external_google_owners        = optional(list(string), [])
    external_google_group_owners  = optional(list(string), [])
  })

  description = "Google group config"
}

variable "membership" {
  type = object({
    google_group_admins  = optional(list(string), [])
    google_group_members = optional(list(string), [])
    google_group_owners  = optional(list(string), [])
    google_user_admins   = optional(list(string), [])
    google_user_members  = optional(list(string), [])
    google_user_owners   = optional(list(string), [])
  })

  description = "Membership data"
}

variable "parent_groups" {
  type = any

  default = {}

  description = "Parent groups data"
}
