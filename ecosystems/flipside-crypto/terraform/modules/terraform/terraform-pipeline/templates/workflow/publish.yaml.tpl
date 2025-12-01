${job_name}:
  runs-on: ubuntu-latest
  needs:
%{ for dependency in dependencies ~}
    - '${dependency}'
%{ endfor ~}
  steps:
    - name: Bump version and push tag
      id: bump-version-and-push
      uses: hennejg/github-tag-action@v4.4.0
      with:
        github_token: $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}
    - name: Release
      uses: softprops/action-gh-release@v2
      with:
        name: $${{ steps.bump-version-and-push.outputs.new_tag }}
        tag_name: $${{ steps.bump-version-and-push.outputs.new_tag }}
        body: $${{ steps.bump-version-and-push.outputs.changelog }}
        tag_prefix: '${prefix}'
        generate_release_notes: true
        token: $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}