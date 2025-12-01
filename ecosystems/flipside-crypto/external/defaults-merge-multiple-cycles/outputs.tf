output "cycles" {
  value = {
    for cycle_name, cycle_data in module.this : cycle_name => cycle_data["results"] if cycle_data["results"] != {}
  }

  description = "Results of merging defaults into the source map for each cycle"
}