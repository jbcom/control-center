module "raw_files_data" {
  source = "../os/os-group-and-format-files"

  files = var.files

  preserve_names_as_is = var.preserve_names_as_is
}

locals {
  raw_files_data = jsondecode(module.raw_files_data.files)

  root_path_prefix = var.rel_to_root != "" ? "${path.root}/${var.rel_to_root}" : ""

  file_path_depth = {
    for file_path, _ in local.raw_files_data : file_path => length([
      for component in split("/", dirname(file_path)) : component if component != "."
    ])
  }

  file_path_rel_to_root = {
    for file_path, path_depth in local.file_path_depth : file_path => join("/", [
      for i in range(0, path_depth) : ".."
    ])
  }

  base_files_data = {
    for file_path, file_data in local.raw_files_data : (join("/", compact([
      local.root_path_prefix, var.file_base_path, file_path
      ]))) => replace(file_data, "$${REL_TO_ROOT}", local.file_path_rel_to_root[file_path]) if !anytrue([
      for path_prefix in var.denylist : startswith(file_path, path_prefix)
      ]) && (length(var.allowlist) == 0 || anytrue([
        for path_prefix in var.allowlist : startswith(file_path, path_prefix)
    ]))
  }

  files_data = {
    for file_path, file_data in local.base_files_data : (var.file_path_trim_prefix != "" ? trimprefix(file_path, var.file_path_trim_prefix) : file_path) => file_data
  }
}

resource "local_sensitive_file" "this" {
  for_each = {
    for file_name, file_data in local.files_data : file_name => file_data if var.write_files
  }

  filename = each.key

  content = each.value
}

module "gitkeep_records" {
  for_each = {
    for record_dir, new_file_names in jsondecode(module.raw_files_data.gitkeep_records) : record_dir => new_file_names if var.save_gitkeep_record
  }

  source = "../git/git-update-gitkeep-record"

  record_dir = each.key

  new_file_names = each.value
}