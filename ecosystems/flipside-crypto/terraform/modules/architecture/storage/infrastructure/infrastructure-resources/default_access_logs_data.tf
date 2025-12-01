locals {
  default_access_logs_bucket_data = var.context["access_logs"]
  default_access_logs_bucket_name = local.default_access_logs_bucket_data["bucket_id"]
}