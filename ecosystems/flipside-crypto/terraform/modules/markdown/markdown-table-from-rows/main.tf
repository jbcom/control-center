locals {
  table_data = {
    title = var.title

    description = var.description

    columns = [
      for header in var.order : {
        header = header
        rows = [
          for row_data in var.rows : lookup(row_data, header, "")
        ]
      }
    ]
  }
}