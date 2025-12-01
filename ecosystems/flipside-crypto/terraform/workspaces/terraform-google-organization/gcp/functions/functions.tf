# Shared Cloud Storage bucket for all function source code
module "function_source_bucket" {
  source  = "terraform-google-modules/cloud-storage/google"
  version = "11.0.0"

  project_id = "flipsidecrypto"
  names      = ["fsc-cloud-function-builds"]
  location   = "US"

  # Lifecycle management - keep source code for 30 days
  lifecycle_rules = [{
    action = {
      type = "Delete"
    }
    condition = {
      age = 30
    }
  }]

  labels = {
    purpose     = "cloud-function-source"
    environment = "production"
    team        = "devops"
  }
}

# Generic Cloud Functions deployment using for_each
# Deploys all functions defined in local.context.gcp.functions
module "functions" {
  source = "../../../modules/scheduled-function-deployment"

  for_each = local.context.gcp.functions

  project_id  = "flipsidecrypto"
  source_dir  = "${path.module}/${each.key}"
  bucket_name = module.function_source_bucket.names_list[0]

  config = each.value

  depends_on = [module.function_source_bucket]
}

# Outputs for all deployed functions
output "functions" {
  description = "Details of all deployed Cloud Functions"
  value = {
    for name, function in module.functions : name => {
      function_name          = function.function_name
      function_uri           = function.function_uri
      topic_name             = function.topic_name
      schedule_name          = function.schedule_name
      manual_trigger_command = function.manual_trigger_command
      function_logs_command  = function.function_logs_command
    }
  }
}

# Shared bucket output
output "function_source_bucket" {
  description = "Shared Cloud Storage bucket for function source code"
  value = {
    name = module.function_source_bucket.names_list[0]
    url  = module.function_source_bucket.urls_list[0]
  }
}

# Individual outputs for backward compatibility
output "gws_user_sync_function_name" {
  description = "Name of the GWS User Sync Cloud Function"
  value       = module.functions["gws_user_sync"].function_name
}

output "gws_user_sync_function_uri" {
  description = "URI of the GWS User Sync Cloud Function"
  value       = module.functions["gws_user_sync"].function_uri
}

output "gws_user_sync_topic_name" {
  description = "Name of the Pub/Sub topic for triggering the function"
  value       = module.functions["gws_user_sync"].topic_name
}

output "gws_user_sync_schedule_name" {
  description = "Name of the Cloud Scheduler job"
  value       = module.functions["gws_user_sync"].schedule_name
}

output "manual_trigger_command" {
  description = "Command to manually trigger the GWS User Sync function"
  value       = module.functions["gws_user_sync"].manual_trigger_command
}
