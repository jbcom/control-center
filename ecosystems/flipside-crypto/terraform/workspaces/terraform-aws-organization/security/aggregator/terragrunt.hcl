terraform {
  extra_arguments "init_args" {
    commands = [
      "init"
    ]

    arguments = [
      "-upgrade",
    ]
  }
}

dependency "config" {
  config_path = "../../../.././workspaces/aws/security/config"

  skip_outputs = true
}

dependency "delegation" {
  config_path = "../../../.././workspaces/aws/security/delegation"

  skip_outputs = true
}

dependency "guardduty" {
  config_path = "../../../.././workspaces/aws/security/guardduty"

  skip_outputs = true
}

dependency "macie" {
  config_path = "../../../.././workspaces/aws/security/macie"

  skip_outputs = true
}

dependency "securityhub" {
  config_path = "../../../.././workspaces/aws/security/securityhub"

  skip_outputs = true
}

