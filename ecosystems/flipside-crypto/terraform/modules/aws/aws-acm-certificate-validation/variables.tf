variable "zone_id" {
  type = string

  description = "Zone ID"
}

variable "ttl" {
  type = number

  default = 300

  description = "TTL"
}

variable "domain_validation_options" {
  type = list(object({
    domain_name           = string
    resource_record_name  = string
    resource_record_type  = string
    resource_record_value = string
  }))

  description = "Domain validation options"
}