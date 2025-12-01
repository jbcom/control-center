variable "order" {
  type = list(string)

  description = "Column order"
}

variable "rows" {
  type = list(map(string))

  description = "Rows by column header and value"
}