locals {
  tags = merge(var.tags, {
    Name = local.group_name
  })

  default_parameters = {
    shared_preload_libraries = join(",", var.shared_preload_libraries)
  }
}