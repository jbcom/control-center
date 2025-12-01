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

