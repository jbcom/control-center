protection_rules = optional(map(object({
  pattern                         = optional(string, "")
  enforce_admins                  = optional(bool, false)
  require_signed_commits          = optional(bool, false)
  required_linear_history         = optional(bool, false)
  require_conversation_resolution = optional(bool, false)
  /*
  object({
    strict   = optional(bool)
    contexts = optional(list(string))
  })*/
  required_status_checks = optional(any, {})

  /*
  object({
    dismiss_stale_reviews           = optional(bool, false)
    restrict_dismissals             = optional(bool, false)
    dismissal_restrictions          = optional(list(string), [])
    pull_request_bypassers          = optional(list(string), [])
    require_code_owner_reviews      = optional(bool, false)
    required_approving_review_count = optional(number, 0)
  })
  */
  required_pull_request_reviews = optional(any, {})

  push_restrictions   = optional(list(string), [])
  allows_deletions    = optional(bool, false)
  allows_force_pushes = optional(bool, false)
})), {})