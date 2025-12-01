variable "identifier" {
  type = string

  description = "Identifier"
}

variable "total_cpu" {
  type = number

  default = null

  description = "Current fixed CPU value"
}

variable "unit_cpu" {
  type = number

  default = null

  description = "Current calculated CPU value"
}

variable "cpu_cushion" {
  type = number

  default = 256

  description = "CPU cushion"
}

variable "total_memory" {
  type = number

  default = null

  description = "Current fixed memory value"
}

variable "unit_memory" {
  type = number

  default = null

  description = "Current calculated memory value"
}

variable "memory_cushion" {
  type = number

  default = 512

  description = "Memory cushion"
}

variable "scale" {
  type = number

  default = 1

  description = "Scale for the CPU and memory"
}
