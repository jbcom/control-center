output "account" {
  description = "The complete account record with both resource and processed labels"
  value       = module.account_labels.account
}
