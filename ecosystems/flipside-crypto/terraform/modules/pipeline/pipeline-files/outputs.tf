output "sync_targets" {
  value = local.sync_targets

  description = "Sync targets"
}

output "files" {
  value = module.files.raw

  description = "Files"
}

output "generator" {
  value = try(module.generator_pipeline[0], {})

  description = "Generator data, if any"
}