locals {
  urls = distinct(compact(concat([
    var.url,
  ], var.urls)))
}

data "curl" "manifests" {
  for_each = toset(local.urls)

  http_method = "GET"
  uri         = each.key
}

data "kubectl_file_documents" "this" {
  for_each = data.curl.manifests

  content = each.value["response"]
}