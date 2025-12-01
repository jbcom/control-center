locals {
  files = merge([
    for folder_name, file in var.files : {
      for file_name, file_data in file : "${folder_name}/${file_name}" => file_data if file_data != ""
    }
  ]...)
}

resource "local_file" "this" {
  for_each = local.files

  filename = "${local.root_dir}/${each.key}"

  content = each.value
}