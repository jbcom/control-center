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

dependency "bots" {
  config_path = "../.././workspaces/bots"

  skip_outputs = true
}

dependency "organization" {
  config_path = "../.././workspaces/organization"

  skip_outputs = true
}

