${job_name}:
  runs-on: ubuntu-latest
  needs:
%{ for dependency in dependencies ~}
    - '${dependency}'
%{ endfor ~}
  steps:
    - name: Dispatch ${workflow} in ${organization}/${repository}/${branch}
      run: |
        curl -X POST \
          -H "Authorization: Bearer $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}" \
          -H "Accept: application/vnd.github.v3+json" \
          https://api.github.com/repos/${organization}/${repository}/actions/workflows/${workflow}/dispatches \
          -d '{"ref": "${branch}"}'