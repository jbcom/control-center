variable "config" {
  type = object({
    state_path           = optional(string)
    state_paths          = optional(map(string))
    state_key            = optional(string)
    nest_state_under_key = optional(string)

    merge_record       = optional(string)
    merge_records      = optional(list(string))
    record_directories = optional(map(string))
    extra_record_categories = optional(map(object({
      records_path = string
      pattern      = optional(string, "*.json")
    })))
    nest_records_under_key = optional(string)

    config_dir            = optional(string)
    nest_config_under_key = optional(string)
    config_dirs           = optional(list(string))

    ordered_state_merge   = optional(bool)
    ordered_records_merge = optional(bool)
    ordered_config_merge  = optional(bool)

    nest_sources_under_key = optional(string)
    ordered_sources_merge  = optional(bool)

    parent_records                   = optional(list(string))
    parent_config_dirs               = optional(list(string))
    ordered_parent_records_merge     = optional(bool)
    ordered_parent_config_dirs_merge = optional(bool)
    ordered_parent_sources_merge     = optional(bool)

    allowlist = optional(list(string))
    denylist  = optional(list(string))

    debug         = optional(bool)
    verbose_debug = optional(bool)
  })

  default = {}

  description = "Configuration for the context record"
}

variable "passthrough_data_channel" {
  type = any

  default = {}

  description = "Passthrough data channel for whatever module is calling this one. Cannot be set by user configuration."
}

variable "state_path" {
  type = string

  default = ""

  description = "State path to pull additional context from"
}

variable "state_key" {
  type = string

  default = "context"

  description = "State key to pull additional context from"
}

variable "state_paths" {
  type = map(string)

  default = {}

  description = "State paths to pull additional context from by path and key"
}

variable "nest_state_under_key" {
  type = string

  default = ""

  description = "Key to nest loaded state data under"
}

variable "ordered_state_merge" {
  type = bool

  default = true

  description = "Whether to merge the state elements in a predetermined order or whether to instead merge them all together, joining data under shared keys"
}

variable "merge_record" {
  type = string

  default = ""

  description = "Record to merge on top of the context object"

}

variable "merge_records" {
  type = list(string)

  default = []

  description = "Record(s) to merge on top of the context object"
}

variable "record_directories" {
  type = map(string)

  default = {}

  description = "Record directories to search for files to merge along with the pattern to use when searching"
}

variable "extra_record_categories" {
  type = map(object({
    records_path = string
    pattern      = optional(string, "*.json")
  }))

  default = {}

  description = <<-EOT
  Extra record categories:

  These categories are specified by key, which will be injected into the final context object as such,
  and for each key, a path to a directory containing the records,
  and optionally a pattern for the record files.

  JSON and YAML decoding will be attempted depending on the file extension.
  EOT
}

variable "nest_records_under_key" {
  type = string

  default = ""

  description = "Key to nest loaded records under"
}

variable "ordered_records_merge" {
  type = bool

  default = false

  description = "Whether to merge the record(s) in their list order or whether to instead merge them all together, joining data under shared keys"
}

variable "config_dir" {
  type = string

  default = ""

  description = "Directory, if any, to search for configuration files to add to the context"
}

variable "nest_config_under_key" {
  type = string

  default = ""

  description = "Key to nest loaded configuration under"
}

variable "config_dirs" {
  type = list(string)

  default = []

  description = "Directories, if any, to search for configuration files to add to the context"
}

variable "ordered_config_merge" {
  type = bool

  default = true

  description = "Whether to merge the config file(s) in their list order or whether to instead merge them all together, joining data under shared keys"
}

variable "nest_sources_under_key" {
  type = string

  default = ""

  description = "Key to nest loaded sources under"
}

variable "ordered_sources_merge" {
  type = bool

  default = true

  description = "Whether to merge all sources ordered or not"
}

variable "parent_records" {
  type = list(string)

  default = []

  description = "Parent record(s) to use as a base for the context object"
}

variable "parent_config_dirs" {
  type = list(string)

  default = []

  description = "Parent config directories to use as a base for the context object"
}

variable "ordered_parent_records_merge" {
  type = bool

  default = false

  description = "Whether to merge the parent record(s) in their list order or whether to instead merge them all together, joining data under shared keys"
}

variable "ordered_parent_config_dirs_merge" {
  type = bool

  default = true

  description = "Whether to merge the parent config file(s) in their list order or whether to instead merge them all together, joining data under shared keys"
}

variable "ordered_parent_sources_merge" {
  type = bool

  default = true

  description = "Whether to merge all parent sources ordered or not"
}

variable "ordered" {
  type = bool

  default = null

  description = "Global override for whether to merge ordered or not"
}

variable "allowlist" {
  type = list(string)

  default = []

  description = "Allowlist of keys to not merge from the record"
}

variable "denylist" {
  type = list(string)

  default = []

  description = "Denylist of keys to not merge from the record"
}