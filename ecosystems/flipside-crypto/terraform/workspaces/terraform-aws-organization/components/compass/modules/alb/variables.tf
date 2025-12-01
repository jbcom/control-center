variable "name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "vpc_name" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "subdomain" {
  type = string
}

variable "cloudflare_zone" {
  type = string
}

variable "rpc_port" {
  type    = number
  default = 8000
}

variable "acm_certificate_arn" {
  type = string
}

variable "sg_egress_all_name" {
  type = string
}

variable "sg_http_name" {
  type = string
}

variable "sg_https_name" {
  type = string
}
