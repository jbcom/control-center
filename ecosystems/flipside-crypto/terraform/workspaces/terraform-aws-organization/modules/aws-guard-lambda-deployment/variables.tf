variable "rel_to_root" {
  description = "Relative path from workspace to repository root"
  type        = string
  default     = "../.."
}

variable "base_src_dir" {
  description = "Base directory for guard source code relative to repository root"
  type        = string
  default     = "src/guards"
}
