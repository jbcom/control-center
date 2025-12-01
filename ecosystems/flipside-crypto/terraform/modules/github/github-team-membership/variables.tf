variable "config" {
  type = object({
    github_team_id = optional(string)

    admins  = optional(list(string), [])
    members = optional(list(string), [])
    owners  = optional(list(string), [])

    parent = optional(string)

    external_github_members = optional(list(string), [])
  })

  description = "Github team config"
}

variable "membership" {
  type = object({
    github_team_members = list(string)
  })

  description = "Membership data"
}

variable "parent_groups" {
  type = any

  default = {}

  description = "Parent groups data"
}
