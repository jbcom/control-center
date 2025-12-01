output "manifests" {
  value = {
    for manifest_key, file_data in local_file.this : manifest_key => basename(file_data["filename"])
  }

  description = "Manifests"
}