locals {
  files = {
    for file_path in fileset("${var.rel_to_root}/${var.docs_dir}", var.pattern) : file_path => {
      category = dirname(file_path)
      title    = trimsuffix(basename(file_path), ".md")
      url      = format("./%s/%s", var.docs_dir, file_path)
    }
  }

  index = {
    for file_path, file_data in local.files : file_data["category"] => file_data...
  }
}