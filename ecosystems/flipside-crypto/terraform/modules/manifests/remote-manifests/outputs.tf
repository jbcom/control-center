output "manifests" {
  value = merge([
    for _, manifests_data in data.kubectl_file_documents.this : manifests_data["manifests"]
  ]...)

  description = "Merged manifests"
}