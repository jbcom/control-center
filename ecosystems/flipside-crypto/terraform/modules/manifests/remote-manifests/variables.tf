variable "url" {
  type = string

  default = ""

  description = "Manifests URL"
}

variable "urls" {
  type = list(string)

  default = []

  description = "Manifest URLs"
}