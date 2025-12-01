variable "state_sources" {
  type = map(string)

  default = {}

  description = "State sources to pull context from by path and key"
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

variable "verbose" {
  type = bool

  default = false

  description = "Whether to enable verbose debug output with full data dumps"
}