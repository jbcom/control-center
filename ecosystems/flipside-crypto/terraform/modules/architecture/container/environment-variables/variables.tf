variable "config" {
  type = object({
    files   = optional(list(string), [])
    context = optional(map(string), {})
    inline  = optional(map(string), {})
  })

  description = "Environment variable sources configuration"
}

variable "context" {
  type = any

  description = "Context data"
}

variable "environment_variables_dir" {
  type = string

  default = "environment-variables"

  description = "Environment variables directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}
