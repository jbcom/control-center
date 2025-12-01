locals {
  # Basic account information - handle both AWS account and Control Tower account types
  account_id = try(var.account.account_id, var.account.id)
  provisioned_product_id = try(var.account.provisioned_product_id,
    startswith(try(var.account.id, ""), "pp-") ? var.account.id : null
  )
  account_name    = var.account.name
  is_root_account = local.account_id == var.caller_account_id

  # Name normalization (only where needed for technical reasons)
  normalized_name = replace(local.account_name, " ", "")
  json_key        = replace(local.normalized_name, "-", "_")
  network_name    = lower(replace(local.normalized_name, "_", "-"))

  # Find matching organizational unit
  matching_unit = {
    for unit_name, unit in var.units : unit_name => unit
    if try(var.account.parent_id, null) != null && unit.id == var.account.parent_id
  }

  # Get the first matching unit or empty map
  unit      = length(local.matching_unit) > 0 ? values(local.matching_unit)[0] : {}
  unit_tags = try(local.unit.tags, {})

  # Process tags and environment
  tags = try(var.account.tags, {})
  environment = coalesce(
    try(local.tags["Environment"], null),
    try(var.account.environment, null),
    startswith(local.account_name, "User-") ? "dev" : "global"
  )

  # Domain resolution
  domain = try(var.domains[local.environment], null)
  subdomain = local.domain == null ? null : (
    !contains(["stg", "prod"], local.environment) || startswith(local.domain, local.network_name)
    ? local.domain
    : "${local.network_name}.${local.domain}"
  )

  # Process classifications
  classification_pattern      = "/[^A-Za-z0-9_-]+/"
  raw_account_classifications = compact(split(" ", try(local.tags["Classifications"], "")))
  raw_unit_classifications    = compact(split(" ", try(local.unit_tags["Classifications"], "")))

  processed_classifications = distinct(concat(
    [for c in local.raw_account_classifications : lower(replace(replace(c, "_accounts$", ""), local.classification_pattern, "_"))],
    [for c in local.raw_unit_classifications : lower(replace(replace(c, "_accounts$", ""), local.classification_pattern, "_"))]
  ))

  # Role information
  execution_role_name = local.is_root_account ? "" : coalesce(try(local.tags["ExecutionRoleName"], null), "AWSControlTowerExecution")
  execution_role_arn  = local.execution_role_name == "" ? "" : "arn:aws:iam::${local.account_id}:role/${local.execution_role_name}"

  # Spoke status
  spoke = tobool(coalesce(
    try(local.tags["Spoke"], null),
    try(var.account.spoke, null),
    try(local.unit_tags["Spoke"], null),
    "false"
  ))
}

# Validation checks using preconditions
check "account_validation" {
  assert {
    condition     = can(regex("^\\d{12}$|^pp-", local.account_id))
    error_message = "Account ID must be either a 12-digit number or start with 'pp-'"
  }

  assert {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9\\- ]+$", var.account.name))
    error_message = "Account name must start with a letter and contain only alphanumeric characters, hyphens, and spaces"
  }

  assert {
    condition     = var.account.parent_id == null ? true : can(regex("^ou-[a-z0-9]{4,32}-[a-z0-9]{8,32}$|^r-[a-z0-9]{4,32}$", var.account.parent_id))
    error_message = "Parent ID must be a valid organizational unit ID (ou-) or root ID (r-)"
  }

  assert {
    condition     = var.account.organizational_unit == null ? true : can(regex("^[A-Za-z][A-Za-z0-9\\- ]+\\([ou-][a-z0-9]{4,32}-[a-z0-9]{8,32}\\)$", var.account.organizational_unit))
    error_message = "Organizational unit must be in the format 'Name (ou-xxxx-xxxxxxxx)'"
  }

  assert {
    condition     = try(var.account.tags["Environment"], null) == null ? true : contains(["dev", "stg", "prod", "global", "network", "compass", "indexers", "Sandbox"], var.account.tags["Environment"])
    error_message = "Environment tag must be one of: dev, stg, prod, global, network, compass, indexers, Sandbox"
  }

  assert {
    condition     = length(local.matching_unit) > 0 || (var.account.parent_id == null)
    error_message = "No matching organizational unit found for the provided parent_id"
  }

  assert {
    condition     = local.domain == null ? true : can(regex("^[a-z0-9][a-z0-9.-]+\\.[a-z]{2,}$", local.domain))
    error_message = "Domain must be a valid domain name"
  }
} 