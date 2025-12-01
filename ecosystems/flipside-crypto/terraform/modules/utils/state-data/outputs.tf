output "state" {
  value = local.state_data

  description = "State data"
}

output "raw" {
  value = {
    for state_path, state_data in data.terraform_remote_state.remote_context_data : state_path => state_data["outputs"]
  }

  description = "Raw state data"
}
