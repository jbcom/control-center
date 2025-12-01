resource "local_file" "this" {
  for_each = var.manifests

  filename = "${var.local_dir}/${basename(each.key)}.yaml"

  content = each.value
}