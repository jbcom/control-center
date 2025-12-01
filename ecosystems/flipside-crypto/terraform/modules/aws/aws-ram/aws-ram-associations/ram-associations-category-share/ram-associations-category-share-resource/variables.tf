variable "resource_arn" {
  type = string

  description = "Resource ARN"
}

variable "resource_share_arns" {
  type = list(string)

  description = "Associated resource share ARNs"
}