variable "manifests" {
  type = map(string)

  description = "Manifests to save locally"
}

variable "local_dir" {
  type = string

  description = "Local directory to save the manifests into"
}