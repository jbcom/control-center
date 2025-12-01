module "table_data" {
  source = "../../utils/deepmerge"

  source_maps = var.tables
}

locals {
  raw_table_data = module.table_data.merged_maps

  table_data = {
    for table_name, table_data in local.raw_table_data : table_name => {
      columns = [
        for column_name in distinct(table_data["order"]) : {
          header = column_name
          rows   = table_data["columns"][column_name]
        }
      ]
    }
  }
}