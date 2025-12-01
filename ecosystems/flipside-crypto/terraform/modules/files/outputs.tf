output "raw" {
  value = local.raw_files_data

  description = "Raw files data with no path manipulation"
}

output "files" {
  value = local.files_data

  description = "Files data"
}

output "file_base_path" {
  value = var.file_base_path

  description = "Passthrough of file base path"
}

output "file_path_depth" {
  value = local.file_path_rel_to_root

  description = "File path depth"
}