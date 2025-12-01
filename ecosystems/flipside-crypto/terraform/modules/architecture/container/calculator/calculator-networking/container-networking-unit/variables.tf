variable "identifier" {
  type = string

  description = "Identifier"
}

variable "config" {
  type = object({
    exposed = bool

    ingress = object({
      port             = number
      protocol         = string
      protocol_version = string
    })

    port_mappings = list(object({
      containerPort = number
      hostPort      = number
      protocol      = string
    }))
  })

  description = "Networking configuration"
}
