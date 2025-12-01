# Service Accounts
moved {
  from = google_service_account.this
  to   = google_service_account.github
}

moved {
  from = google_service_account.hevo_service_account
  to   = google_service_account.hevo
}

# IAM Role Assignments
moved {
  from = google_project_iam_member.this
  to   = google_project_iam_member.github_owner
}

moved {
  from = google_project_iam_member.service_account_roles
  to   = google_project_iam_member.hevo_owner
}

# Custom IAM Role
moved {
  from = google_project_iam_custom_role.this
  to   = google_project_iam_custom_role.service_account_manager
}

# Service Account Key
moved {
  from = google_service_account_key.hevo_service_account_key
  to   = google_service_account_key.hevo
}

# API Services
moved {
  from = google_project_service.iam
  to   = google_project_service.apis["iam.googleapis.com"]
}

moved {
  from = google_project_service.iamcredentials
  to   = google_project_service.apis["iamcredentials.googleapis.com"]
}

moved {
  from = google_project_service.run
  to   = google_project_service.apis["run.googleapis.com"]
}

moved {
  from = google_project_service.cloudresourcemanager
  to   = google_project_service.apis["cloudresourcemanager.googleapis.com"]
}

moved {
  from = google_project_service.org_policy_api
  to   = google_project_service.apis["orgpolicy.googleapis.com"]
}

moved {
  from = google_project_service.sheets_api
  to   = google_project_service.apis["sheets.googleapis.com"]
}

moved {
  from = google_project_service.drive_api
  to   = google_project_service.apis["drive.googleapis.com"]
}
