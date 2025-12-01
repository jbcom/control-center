variable "name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "sentry_dsn_rpc" {
  type = string
}

variable "sentry_dsn_workers" {
  type = string
}

variable "datadog_api_key" {
  type = string
}
