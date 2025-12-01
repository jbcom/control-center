module "org_policy_boolean" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.2.0"

  for_each = var.boolean_constraints

  policy_root    = "project"
  policy_root_id = var.project_id
  constraint     = each.key
  policy_type    = "boolean"

  rules = [
    {
      enforcement = each.value
      allow       = []
      deny        = []
      conditions  = []
    }
  ]
}

module "org_policy_list" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.2.0"

  for_each = var.list_constraints

  policy_root    = "project"
  policy_root_id = var.project_id
  constraint     = each.key
  policy_type    = "list"

  rules = [
    {
      enforcement = each.value.enforcement
      allow       = each.value.allow
      deny        = each.value.deny
      conditions  = []
    }
  ]
}

resource "google_project_iam_member" "service_account_roles" {
  for_each = toset(var.roles)

  project = var.project_id
  role    = each.value
  member  = var.service_account_identifier
}
