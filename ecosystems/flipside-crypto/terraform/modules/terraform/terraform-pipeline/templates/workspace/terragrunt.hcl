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

%{ if dependencies == {} ~}
# Root workspace
%{ else ~}
%{ for workspace_name, workspace_path in dependencies ~}
%{ if !contains(terragrunt_dependencies, workspace_path) ~}
dependency "${workspace_name}" {
  config_path = "$${REL_TO_ROOT}/${workspace_path}"

  skip_outputs = true
}
%{ endif ~}

%{ endfor ~}
%{ endif ~}
%{ if length(terragrunt_dependencies) > 0 ~}
dependencies {
  paths = [
%{ for workspace_path in terragrunt_dependencies ~}
    "$${REL_TO_ROOT}/${workspace_path}",
%{ endfor ~}
  ]
}
%{ endif ~}
%{ if try(coalesce(extra_terragrunt_hcl), null) != null ~}

${extra_terragrunt_hcl}
%{ endif ~}
