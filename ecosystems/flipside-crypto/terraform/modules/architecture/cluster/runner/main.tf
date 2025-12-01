data "kubectl_file_documents" "default" {
  content = var.manifest
}

resource "kubectl_manifest" "default" {
  for_each = data.kubectl_file_documents.default.manifests

  yaml_body = each.value

  override_namespace = var.namespace
}