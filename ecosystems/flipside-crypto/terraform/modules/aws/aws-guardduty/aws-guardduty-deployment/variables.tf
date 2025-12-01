variable "gd_finding_publishing_frequency" {
  type = string

  default = "SIX_HOURS"

  description = "Specifies the frequency of notifications sent for subsequent finding occurrences"
}

variable "context" {
  type = any

  description = "Context data"
}