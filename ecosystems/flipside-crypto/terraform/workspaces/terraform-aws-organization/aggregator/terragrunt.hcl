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

dependency "authentication" {
  config_path = "../.././workspaces/authentication"

  skip_outputs = true
}

dependency "bots" {
  config_path = "../.././workspaces/bots"

  skip_outputs = true
}

dependency "organization" {
  config_path = "../.././workspaces/organization"

  skip_outputs = true
}

dependency "secrets" {
  config_path = "../.././workspaces/secrets"

  skip_outputs = true
}

dependency "sso" {
  config_path = "../.././workspaces/sso"

  skip_outputs = true
}

