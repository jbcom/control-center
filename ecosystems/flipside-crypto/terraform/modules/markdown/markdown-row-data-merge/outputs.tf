output "tables" {
  value = [
    {
      columns = local.columns
    }
  ]

  description = "Tables data"
}

output "columns" {
  value = local.columns

  description = "Column data for the rows"
}