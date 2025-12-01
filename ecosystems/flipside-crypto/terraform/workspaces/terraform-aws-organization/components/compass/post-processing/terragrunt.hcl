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

dependency "infrastructure" {
  config_path = "../.././terraform/infrastructure"

  skip_outputs = true
}

