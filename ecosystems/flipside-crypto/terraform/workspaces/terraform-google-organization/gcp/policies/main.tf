module "cs-org-policy-essentialcontacts_allowedContactDomains" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.0.0"

  policy_root      = "organization"
  policy_root_id   = local.org_id
  constraint       = "essentialcontacts.allowedContactDomains"
  policy_type      = "list"
  exclude_folders  = []
  exclude_projects = []

  rules = [
    {
      enforcement = false
      allow = [
        "@flipsidecrypto.com",
      ]
      deny       = []
      conditions = []
  }, ]
}

module "cs-org-policy-iam_allowedPolicyMemberDomains" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.0.0"

  policy_root      = "organization"
  policy_root_id   = local.org_id
  constraint       = "iam.allowedPolicyMemberDomains"
  policy_type      = "list"
  exclude_folders  = []
  exclude_projects = []

  rules = [
    {
      enforcement = false
      allow = [
        "C00m3i1uh",
      ]
      deny       = []
      conditions = []
  }, ]
}

module "cs-org-policy-iam_disableServiceAccountKeyCreation" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.0.0"

  policy_root      = "organization"
  policy_root_id   = local.org_id
  constraint       = "iam.disableServiceAccountKeyCreation"
  policy_type      = "boolean"
  exclude_folders  = []
  exclude_projects = []

  rules = [
    {
      enforcement = false
      allow       = []
      deny        = []
      conditions  = []
  }, ]
}

module "cs-org-policy-iam_disableServiceAccountKeyUpload" {
  source  = "terraform-google-modules/org-policy/google//modules/org_policy_v2"
  version = "7.0.0"

  policy_root      = "organization"
  policy_root_id   = local.org_id
  constraint       = "iam.disableServiceAccountKeyUpload"
  policy_type      = "boolean"
  exclude_folders  = []
  exclude_projects = []

  rules = [
    {
      enforcement = false
      allow       = []
      deny        = []
      conditions  = []
  }, ]
}
