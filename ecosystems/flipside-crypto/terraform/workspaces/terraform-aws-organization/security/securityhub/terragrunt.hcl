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

dependency "delegation" {
  config_path = "../../../.././workspaces/aws/security/delegation"

  skip_outputs = true
}

