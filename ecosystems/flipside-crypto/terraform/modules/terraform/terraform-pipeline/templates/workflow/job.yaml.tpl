%{ if conditions == {} ~}
%{ if workspace_depends_on_conditional_workspaces ~}
if : $${{always() && !contains(needs.*.result, 'cancelled')}}
%{ endif ~}
%{ else ~}
%{ if workspace_depends_on_conditional_workspaces ~}
if : $${{always() && inputs.${job_conditional_key} == true && !contains(needs.*.result, 'cancelled')}}
%{ else ~}
if : $${{inputs.${job_conditional_key} == true}}
%{ endif ~}
%{ endif ~}
runs-on: ${runner_label}
%{ if length(dependencies) > 0 ~}
needs:
%{ for dependency in dependencies ~}
  - '${dependency}'
%{ endfor ~}
%{ endif ~}
defaults:
  run:
    shell: bash
    working-directory: ${workspace_dir}
%{ for k, v in environment_variables ~}
  ${k}: "${v}"
%{ endfor ~}