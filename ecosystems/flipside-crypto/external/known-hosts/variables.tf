variable "site" {
  type = string

  default = "github"

  description = "Site to pull known-hosts for. Must match a file in .github/known-hosts"
}