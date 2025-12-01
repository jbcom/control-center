variable "zone_id" {
  type = string

  description = "Zone ID"
}

variable "certificates" {
  type = any

  description = "Certificates data across AWS accounts"
}