variable "config" {
  type = object({
    github_team_id = optional(string)

    pull_repositories     = optional(list(string), [])
    push_repositories     = optional(list(string), [])
    maintain_repositories = optional(list(string), [])
    triage_repositories   = optional(list(string), [])
    admin_repositories    = optional(list(string), [])

    channels = optional(list(string), [])

    # external_aws_identitystore_users = optional(list(string), [])

    external_google_members       = optional(list(string), [])
    external_google_group_members = optional(list(string), [])
    external_google_admins        = optional(list(string), [])
    external_google_group_admins  = optional(list(string), [])
    external_google_owners        = optional(list(string), [])
    external_google_group_owners  = optional(list(string), [])

    external_github_members = optional(list(string), [])

    external_slack_users    = optional(list(string), [])
    external_slack_channels = optional(list(string), [])
  })

  description = "Google group config"
}