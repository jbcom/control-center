variable "name" {
  type        = string
  description = "The website subdomain name"
}

variable "redirect_target" {
  type        = string
  description = "The FQDN to redirect to"
}

variable "force_destroy" {
  type        = bool
  description = "The force_destroy argument of the S3 bucket"
  default     = true
}

variable "web_acl_id" {
  type        = string
  description = "WAF Web ACL ID to attach to the CloudFront distribution, optional"
  default     = ""
}

variable "acm_certificate_arn" {
  type        = string
  description = "ACM certificate ARN"
}

variable "context" {
  type = any

  description = "Context data"
}
