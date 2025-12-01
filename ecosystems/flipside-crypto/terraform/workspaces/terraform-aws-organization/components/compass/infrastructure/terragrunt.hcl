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

dependency "database-monitoring-prod" {
  config_path = "../.././terraform/database-monitoring/prod"

  skip_outputs = true
}

dependency "database-monitoring-stg" {
  config_path = "../.././terraform/database-monitoring/stg"

  skip_outputs = true
}

