data "googleworkspace_groups" "all" {}

data "googleworkspace_users" "all" {}

data "google_projects" "active_projects" {
  filter = "lifecycleState:ACTIVE"
}

locals {
  gws_groups = {
    for group in data.googleworkspace_groups.all.groups :
    group.email => group
  }

  gws_users = {
    for user in data.googleworkspace_users.all.users :
    user.primary_email => user
  }

  gcp_active_projects = {
    for project in data.google_projects.active_projects.projects :
    project.project_id => project
  }
}
