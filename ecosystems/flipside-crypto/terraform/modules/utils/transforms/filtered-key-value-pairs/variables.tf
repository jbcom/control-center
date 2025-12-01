variable "records" {
  type = any

  description = "Records to filter"
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