variable "records" {
  type = any

  default = {}

  description = "Record data to merge"
}

variable "record_files" {
  type = list(string)

  default = []

  description = "Record file(s) to merge"
}

variable "record_directories" {
  type = map(string)

  default = {}

  description = "Record directories to search for files to merge along with the pattern to use when searching"
}

variable "record_categories" {
  type = map(object({
    records_path = string
    pattern      = optional(string, "*.json")
  }))

  default = {}

  description = <<-EOT
  Record categories:

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

variable "ordered_records_merge" {
  type = bool

  default = true

  description = "Whether to merge the record(s) in their list order or whether to instead merge them all together, joining data under shared keys"
}

variable "verbose" {
  type = bool

  default = false

  description = "Whether to enable verbose debug output with full data dumps"
}