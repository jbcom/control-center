variable "tables" {
  type = list(map(object({
    order = list(string)

    columns = map(list(string))
  })))

  description = <<EOT
List of tables by name, column order, and column data by header and value.
Each value must be a single value inside a list.
The reason is that these will be merged, meaning each entry in the list should represent another row of data for each column of each table.
EOT
}