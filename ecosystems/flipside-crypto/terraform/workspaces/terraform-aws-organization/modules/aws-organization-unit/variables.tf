variable "name" {
  description = "The name of the organizational unit"
  type        = string
}

variable "parent_id" {
  description = "The ID of the parent organizational unit or root"
  type        = string
}

variable "tags" {
  description = "Tags to apply to the organizational unit"
  type        = map(string)
  default     = {}
}

variable "classifications" {
  description = "List of classifications for this organizational unit"
  type        = list(string)
  default     = []
}

variable "classifications_delimiter" {
  description = "Delimiter to use when joining classifications"
  type        = string
  default     = " "
} 