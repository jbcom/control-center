variable "users" {
  type = map(object({
    github_handle        = optional(string)
    primary_email        = string
    sso_only             = optional(bool, false)
    aws_sso_scim_user_id = optional(string)
  }))

  description = "Users data"
}

variable "group_name" {
  type = string

  description = "Group name"
}

variable "group" {
  type = object({
    group_name = optional(string)

    google_group_id       = optional(string, null)
    github_team_id        = optional(string, null)
    aws_sso_scim_group_id = optional(string, null)

    enable_slack_group = optional(bool, false)
    slack_group_name   = optional(string)

    admins       = optional(any)
    group_admins = optional(any)

    owners       = optional(any)
    group_owners = optional(any)

    members       = optional(any)
    group_members = optional(any)

    external_admins       = optional(any)
    external_group_admins = optional(any)

    external_owners       = optional(any)
    external_group_owners = optional(any)

    external_members       = optional(any)
    external_group_members = optional(any)
  })

  description = "Group data"
}