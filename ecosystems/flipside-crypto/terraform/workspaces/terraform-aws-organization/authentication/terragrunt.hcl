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

dependency "organization" {
  config_path = "../.././workspaces/organization"

  skip_outputs = true
}

