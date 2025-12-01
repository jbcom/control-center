variable "config" {
  type = object({
    cloudflare_domains = list(string)
    route53_domains    = list(string)
  })
}