# The account output provides processed and validated information about an AWS account.
# This includes normalized names, domain information, role configurations, and classifications
# derived from both account-level and organizational unit-level tags.
output "account" {
  description = <<-EOT
    Processed account information with the following attributes:
    * id - The AWS account ID or provisioned product ID
    * account_id - The AWS account ID (different from id for Control Tower accounts)
    * name - The human-readable account name
    * account_name - Same as name, provided for backwards compatibility
    * json_key - Normalized account name suitable for JSON keys (spaces and hyphens replaced)
    * network_name - Normalized account name suitable for DNS and networking (lowercase, hyphens)
    * domain - The base domain for the account based on its environment
    * subdomain - The full subdomain for the account, including network name prefix if needed
    * spoke - Boolean indicating if this is a spoke account
    * classifications - List of normalized classification tags from account and OU
    * execution_role_name - Name of the execution role (empty for root account)
    * execution_role_arn - Full ARN of the execution role (empty for root account)
    * provisioned_product_id - Control Tower provisioned product ID if applicable
    * original - The original input account data
  EOT

  value = {
    id                     = local.account_id
    account_id             = local.account_id
    name                   = local.account_name
    account_name           = local.account_name
    json_key               = local.json_key
    network_name           = local.network_name
    domain                 = local.domain
    subdomain              = local.subdomain
    spoke                  = local.spoke
    classifications        = local.processed_classifications
    execution_role_name    = local.execution_role_name
    execution_role_arn     = local.execution_role_arn
    provisioned_product_id = local.provisioned_product_id

    # Keep original values from input
    original = var.account
  }

  # Validate output structure and format
  precondition {
    condition     = local.json_key != "" && local.network_name != ""
    error_message = "Failed to generate valid json_key and network_name from account name"
  }

  precondition {
    condition     = local.subdomain == null || can(regex("^[a-z0-9][a-z0-9.-]+\\.[a-z]{2,}$", local.subdomain))
    error_message = "Generated subdomain is not valid"
  }

  precondition {
    condition     = local.execution_role_arn == "" || can(regex("^arn:aws:iam::(\\d{12}|pp-[a-z0-9]+):role/[\\w+=,.@-]+$", local.execution_role_arn))
    error_message = "Generated execution role ARN is not valid"
  }
} 