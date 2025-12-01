
variable "name" {
  type    = string
  default = "compass"
}

variable "env" {
  type    = string
  default = "prod"
}

variable "db_password" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_write_host" {
  type = string
}

variable "db_port" {
  type = number
}

variable "db_write_url" {
  type = string
}
