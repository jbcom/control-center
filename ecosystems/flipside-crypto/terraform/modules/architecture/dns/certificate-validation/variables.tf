variable "domain_validation_options" {
  type = any

  description = "Domain validation options"
}

variable "acm_certificate_arn" {
  type = string

  description = "ACM certificate ARN"
}

variable "zone_id" {
  type = string

  description = "Zone ID"
}