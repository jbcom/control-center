variable "cloudflare_domain" {
  type = string

  description = "Cloudflare domain"
}

variable "tags" {
  type = map(string)

  description = "Tags"
}