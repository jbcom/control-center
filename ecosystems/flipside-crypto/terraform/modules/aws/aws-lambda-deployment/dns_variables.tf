# DNS Configuration Variables

variable "create_dns" {
  type        = bool
  default     = true
  description = "Controls whether DNS records should be created. This is a master switch that can disable all DNS record creation."
}

variable "dns_ttl" {
  type        = number
  default     = 300
  description = "TTL (Time To Live) for DNS records in seconds. Only applies to non-alias records."
}

variable "dns_record_type" {
  type        = string
  default     = "A"
  description = "Type of DNS record to create. Default is 'A'. Only applies to non-alias records."
  validation {
    condition     = contains(["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SRV", "PTR", "CAA", "SPF"], var.dns_record_type)
    error_message = "DNS record type must be one of: A, AAAA, CNAME, MX, TXT, NS, SRV, PTR, CAA, SPF."
  }
}

variable "create_api_gateway_dns_records" {
  type        = bool
  default     = true
  description = "Controls whether DNS records should be created for API Gateway. This is in addition to api_gateway_create_domain_records."
}

variable "create_s3_cdn_dns_records" {
  type        = bool
  default     = true
  description = "Controls whether DNS records should be created for S3 CDN. This is in addition to s3_cdn_dns_alias_enabled."
}

variable "create_ipv6_records" {
  type        = bool
  default     = true
  description = "Controls whether IPv6 (AAAA) records should be created in addition to IPv4 (A) records."
}

variable "dns_alias_evaluate_target_health" {
  type        = bool
  default     = false
  description = "Whether to evaluate the target health of DNS alias records."
}
