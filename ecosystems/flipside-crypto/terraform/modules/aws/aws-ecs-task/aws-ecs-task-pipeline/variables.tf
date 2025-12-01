variable "name" {
  type = string

  description = "Pipeline name"
}

variable "config" {
  type = object({
    name        = optional(string)
    enabled     = optional(bool, false)
    stage       = optional(string)
    environment = string

    execution_role_arn = string

    build = object({
      ecr_repository = string
      repository_url = string
      pre_build      = optional(string, "")

      docker = object({
        add-hosts        = optional(list(string))
        attests          = optional(list(string))
        build-args       = optional(list(string))
        build-contexts   = optional(list(string))
        cgroup-parent    = optional(string)
        context          = optional(string, ".")
        file             = optional(string, "Dockerfile")
        labels           = optional(list(string))
        network          = optional(string)
        cache-from       = optional(string, "type=gha")
        cache-to         = optional(string, "type=gha,mode=max")
        no-cache         = optional(bool, false)
        no-cache-filters = optional(list(string))
        platforms        = optional(list(string), ["linux/amd64"])
        pull             = optional(bool, false)
        push             = optional(bool, true)
        shm-size         = optional(string)
        tags             = optional(list(string), [])
        target           = optional(string)
        ulimit           = optional(list(string))
      })
    })

    workflow = object({
      branches = optional(list(string), ["main"])
      paths    = optional(list(string), [])
    })

    deploy = map(object({
      container_definitions  = list(string)
      cluster_name           = string
      service_name           = string
      task_definition_family = string
    }))
  })

  description = "Pipeline config"
}

variable "tasks" {
  type = any

  description = "Tasks environment configuration"
}