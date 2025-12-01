variable "identifier" {
  type = string

  description = "Identifier"
}

variable "config" {
  type = map(object({
    exposed = bool

    ingress = object({
      port             = optional(number)
      protocol         = optional(string, "HTTP")
      protocol_version = optional(string, "HTTP1")
    })

    port_mappings = optional(list(object({
      containerPort = number
      hostPort      = optional(number)
      protocol      = optional(string, "tcp")
    })), [])
  }))

  description = "Networking configuration"
}
