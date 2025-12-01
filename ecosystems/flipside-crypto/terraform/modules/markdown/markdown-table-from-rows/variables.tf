variable "title" {
  type = string

  default = null

  description = "Title"
}

variable "description" {
  type = string

  default = null

  description = "Description"
}

variable "order" {
  type = list(string)

  description = "Order for the columns by header"
}

variable "rows" {
  type = list(map(string))

  description = "Rows of data by column header and value for the header at each row"
}