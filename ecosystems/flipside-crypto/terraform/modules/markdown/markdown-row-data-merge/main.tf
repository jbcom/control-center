locals {
  columns = [
    for header in var.order : {
      header = header
      rows = compact([
        for row_data in var.rows : try(row_data[header], "")
      ])
    }
  ]
}