variable "config" {
  type = object({
    modules_dir = optional(string, "terraform/modules")
    base_dir    = optional(string, "infrastructure")

    generated_module_name_prefix = optional(string, "infrastructure")

    modules = any

    extra_merged_resources = optional(list(string), [])

    metadata_infrastructure_record = optional(string, "infrastructure.json")

    allowlist = optional(list(string), [])
    denylist  = optional(list(string), [])
  })

  description = "CloudPosse module config"
}

variable "modules_dir" {
  type = string

  default = null

  description = "Modules directory"
}

variable "rel_to_root" {
  type = string

  description = "Relative path to the repository root"
}

variable "file_base_path" {
  type = string

  default = "."

  description = "Base path for generated files"
}