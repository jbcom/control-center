variable "config" {
  type = object({
    skip_pr            = optional(bool, false)
    commit_each_file   = optional(bool, false)
    commit_prefix      = optional(string, "🔄 [skip actions]")
    branch_prefix      = optional(string)
    config_path        = optional(string, ".github/sync.yml")
    workflow_file_name = optional(string, "sync.yml")
    sync_on_push       = optional(bool, true)
    sync_on_call       = optional(bool, true)
    sync_on_dispatch   = optional(bool, true)

    push_triggers = optional(object({
      paths    = optional(list(string), [])
      branches = optional(list(string), ["main"])
    }), {})

    sync_to_all = optional(list(object({
      source = string
      dest   = string
    })), [])

    repositories = any

    repository_owner = optional(string, "FlipsideCrypto")

    slack_notifications           = optional(bool, false)
    slack_webhook_url_secret_name = optional(string, "FLIPSIDE_SLACK_WEBHOOK_URL")
  })
}

variable "save_files" {
  type = bool

  default = false

  description = "Whether to save workflow files locally"
}

variable "rel_to_root" {
  type = string

  default = ""

  description = "Relative path to the repository root"
}
