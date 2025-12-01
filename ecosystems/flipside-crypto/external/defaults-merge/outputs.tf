output "results" {
  value = local.results_data

  description = "Results of merging defaults into the source map"
}

output "log_file" {
  value = local.log_file

  description = "Log file results were output to if logging was enabled"
}