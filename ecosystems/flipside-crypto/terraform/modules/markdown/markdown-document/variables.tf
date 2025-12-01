variable "config" {
  type = object({
    title         = optional(string)
    description   = optional(string)
    path          = optional(string)
    template      = optional(string)
    template_vars = optional(map(string), {})

    format_headings = optional(bool, true)

    collapsible_index = optional(bool, true)

    index = optional(map(list(object({
      url   = string
      title = string
    }))), {})

    sections = optional(list(object({
      title       = string
      description = optional(string)

      format_headings = optional(bool)

      snippets = optional(list(object({
        title          = string
        format_heading = optional(bool)
        content        = string
      })), [])

      tables = optional(list(object({
        title          = string
        format_heading = optional(bool)
        description    = optional(string)

        columns = list(object({
          header = string
          rows   = list(string)
        }))
      })), [])
    })), [])
  })

  description = "Markdown document configuration"
}