setup:
  - uses: actions/checkout@v6
    with:
      ref: $${{env.BRANCH}}
      token: $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}
  - name: Get any new changes from other workspaces
    run: |
      if [[ "$GITHUB_EVENT_NAME" == "release" ]]; then
        git pull --rebase --autostash origin $${{github.event.release.target_commitish}}
      else
        git pull --rebase --autostash
      fi
%{ if use_https_git_auth ~}
  - name: Configure git to use HTTPS with token
    run: |
      # Use HTTPS with token instead of SSH to access FlipsideCrypto repos
      # This avoids issues with SSH key syncing across orgs (PRIVATE visibility secrets)
      git config --global url."https://x-access-token:$${{ secrets.FLIPSIDE_GITHUB_TOKEN }}@github.com/".insteadOf "git@github.com:"
      git config --global url."https://x-access-token:$${{ secrets.FLIPSIDE_GITHUB_TOKEN }}@github.com/".insteadOf "ssh://git@github.com/"
%{ else ~}
  - name: Install SSH key
    uses: shimataro/ssh-key-action@v2
    with:
      key: $${{secrets.EXTERNAL_CI_BOT_SSH_PRIVATE_KEY}}
      known_hosts: $${{secrets.EXTERNAL_CI_BOT_SSH_KNOWN_HOSTS}}
      if_key_exists: replace
%{ endif ~}
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v5
    with:
%{ if use_oidc_auth ~}
      role-to-assume: $${{secrets.AWS_OIDC_ROLE_ARN}}
%{ else ~}
      aws-access-key-id: $${{secrets.EXTERNAL_CI_ACCESS_KEY}}
      aws-secret-access-key: $${{secrets.EXTERNAL_CI_SECRET_KEY}}
%{ endif ~}
      aws-region: us-east-1
      mask-aws-account-id: false
%{ if enable_docker_images ~}
  - name: Login to Amazon ECR
    id: login-ecr
    uses: aws-actions/amazon-ecr-login@v2
    with:
      registries: "${join(",", registry_accounts)}"
  - uses: docker/setup-buildx-action@v3
%{ if run_before_docker != null ~}
  ${indent(2, run_before_docker)}
%{ endif ~}
%{ for repository_name, build_config in docker_images ~}
  - name: Build and push ${repository_name}
    id: docker-build-and-push-${repository_name}
    uses: docker/build-push-action@v6
    with:
      context: ${try(coalesce(build_config["docker"]["context"]), ".")}
      file: ${try(coalesce(build_config["docker"]["file"]), "Dockerfile")}
      platforms: ${try(coalesce(build_config["docker"]["platform"]), "linux/amd64")}
      push: true
      tags: |
        ${build_config["account_id"]}.dkr.ecr.us-east-1.amazonaws.com/${repository_name}:$${{github.sha}}
      cache-from: |
        type=gha,scope=$${{github.ref_name}}-${repository_name}
      cache-to: |
        type=gha,mode=max,scope=$${{github.ref_name}}-${repository_name}
%{ if try(coalesce(build_config["docker"]["build_args"]), null) != null ~}
      build-args: |
%{ for arg_name, arg_val in build_config["docker"]["build_args"] ~}
        ${arg_name}=${arg_val}
%{ endfor ~}
%{ endif ~}
%{ endfor ~}
%{ if run_after_docker != null ~}
  ${indent(2, run_after_docker)}
%{ endif ~}
%{ endif ~}
  - name: Setup Sops
    uses: mdgreenwald/mozilla-sops-action@v1.6.0
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
%{ if install_terraform_modules_library ~}
  - name: Setup Python
    uses: actions/setup-python@v6
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    with:
      python-version: '${python_version}'
  - name: Install Terraform Modules Library
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    run: 'pip install git+ssh://git@github.com/FlipsideCrypto/terraform-modules.git'
%{ endif ~}
  - name: Use Node.js 18.x
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: actions/setup-node@v6
    with:
      node-version: '18.x'
  - name: Setup Terraform
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: hashicorp/setup-terraform@v3
    with:
      terraform_version: '${terraform_version}'
      terraform_wrapper: false
  - name: Cache Terragrunt
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: actions/cache@v4
    id: cache-terragrunt
    with:
      path: $${{runner.tool_cache}}/terragrunt
      key: $${{runner.os}}-terragrunt-${terragrunt_version}
  - uses: nick-fields/retry@v3
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false && steps.cache-terragrunt.outputs.cache-hit != 'true'}}
%{ else ~}
    if: steps.cache-terragrunt.outputs.cache-hit != 'true'
%{ endif ~}
    with:
      timeout_seconds: 15
      max_attempts: 3
      command: |
        mkdir --parents $${{runner.tool_cache}}/terragrunt
        wget https://github.com/gruntwork-io/terragrunt/releases/download/${terragrunt_version}/terragrunt_linux_amd64 -P $${{runner.tool_cache}}/terragrunt
        ls -lhat $${{runner.tool_cache}}/terragrunt
  - name: Setup Terragrunt
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    working-directory: $${{runner.tool_cache}}/terragrunt
    run: |
      sudo cp terragrunt_linux_amd64 /usr/local/bin/terragrunt
      sudo chmod a+x /usr/local/bin/terragrunt
  - name: Create Terraform Plugin Cache Dir
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    run: |
      mkdir --parents $TF_PLUGIN_CACHE_DIR
      mkdir --parents $TERRAGRUNT_DOWNLOAD
  - name: Cache Terraform
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: actions/cache@v4
    with:
      path: $${{env.TF_PLUGIN_CACHE_DIR}}
      key: $${{runner.os}}-terraform-$${{hashFiles('${workspace_dir}/.terraform.lock.hcl')}}
  - name: Cache Terragrunt
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: actions/cache@v4
    with:
      path: $${{env.TERRAGRUNT_DOWNLOAD}}
      key: $${{runner.os}}-terragrunt-$${{hashFiles('${workspace_dir}/.terraform.lock.hcl')}}
  - name: Terraform Format
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    id: fmt
    run: |
      echo 'stdout<<EOF' >> $GITHUB_OUTPUT
      terraform fmt -check -recursive >> $GITHUB_OUTPUT
      echo 'EOF' >> $GITHUB_OUTPUT
    continue-on-error: true
  - name: Terraform Init
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    id: init
    run: terragrunt init --upgrade
%{ if validate_workspace ~}
  - name: Terraform Validate
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    id: validate
    run: |
      echo 'stdout<<EOF' >> $GITHUB_OUTPUT
      terragrunt validate -no-color >> $GITHUB_OUTPUT
      echo 'EOF' >> $GITHUB_OUTPUT
%{ endif ~}
push:
%{ if run_before_apply != null ~}
  ${indent(2, run_before_apply)}
%{ endif ~}
  - name: Terraform Apply
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    run: terragrunt apply -no-color -auto-approve -input=false
    env:
%{ for input_key, tfvar_key in tfvar_inputs ~}
      TF_VAR_${tfvar_key}: $${{inputs.${input_key}}}
%{ endfor ~}
      GITHUB_TOKEN: $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}
      GITHUB_OWNER: "FlipsideCrypto"
%{ if enable_docker_images ~}
      TF_VAR_image_tag: $${{github.sha}}
%{ endif ~}
  - name: Generate artifact UUID
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ else ~}
    if: $${{ always() }}
%{ endif ~}
    id: generate-artifact-uuid
    uses: filipstefansson/uuid-action@v1
    with:
      namespace: '${workspace_name}-$${{github.run_id}}-$${{github.run_attempt}}'
  - uses: actions/upload-artifact@v5
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ else ~}
    if: $${{ always() }}
%{ endif ~}
    with:
      name: $${{ steps.generate-artifact-uuid.outputs.uuid }}-logs
      path: |
        '${workspace_dir}/**/*.log'
      if-no-files-found: ignore
      retention-days: 7
  - uses: actions/upload-artifact@v5
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ else ~}
    if: $${{ always() }}
%{ endif ~}
    with:
      name: $${{ steps.generate-artifact-uuid.outputs.uuid }}-tfstate
      path: '${workspace_dir}/*.tfstate'
      if-no-files-found: ignore
%{ if run_after_apply != null ~}
  ${indent(2, run_after_apply)}
%{ endif ~}
pull_request:
  - name: Terraform Plan
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    id: plan
    run: |
      echo 'stdout<<EOF' >> $GITHUB_OUTPUT
      terragrunt plan -no-color >> $GITHUB_OUTPUT
      echo 'EOF' >> $GITHUB_OUTPUT
    continue-on-error: true
    env:
%{ for input_key, tfvar_key in tfvar_inputs ~}
      TF_VAR_${tfvar_key}: $${{inputs.${input_key}}}
%{ endfor ~}
      GITHUB_TOKEN: $${{secrets.FLIPSIDE_GITHUB_TOKEN || github.token}}
      GITHUB_OWNER: "FlipsideCrypto"
%{ if enable_docker_images ~}
      TF_VAR_image_tag: $${{github.sha}}
%{ endif ~}
  - uses: actions/github-script@v7
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false && github.event_name == 'pull_request'}}
%{ else ~}
    if: github.event_name == 'pull_request'
%{ endif ~}
    with:
      github-token: $${{secrets.GITHUB_TOKEN}}
      script: |
        // 1. Retrieve existing bot comments for the PR
        const { data: comments } = await github.rest.issues.listComments({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: context.issue.number,
        })
        const botComment = comments.find(comment => {
          return comment.user.type === 'Bot' && comment.body.includes('Terraform Format and Style')
        })

        // 2. Prepare format of the comment
        const output = `#### Terraform Format and Style 🖌\`$${{steps.fmt.outcome}}\`
        #### Terraform Initialization ⚙️\`$${{steps.init.outcome}}\`
        #### Terraform Validation 🤖\`$${{steps.validate.outcome}}\`
        <details><summary>Validation Output</summary>

        \`\`\`\n
        $${{steps.validate.outputs.stdout}}
        \`\`\`

        </details>

        #### Terraform Plan 📖\`$${{steps.plan.outcome}}\`

        <details><summary>Show Plan</summary>

        \`\`\`\n
        terraform
        $${{steps.plan.outputs.stdout}}
        \`\`\`

        </details>

        *Pusher: @$${{github.actor}}, Action: \`$${{github.event_name}}\`, Working Directory: \`${workspace_dir}\`, Workflow: \`$${{github.workflow}}\`*`;

        // 3. If we have a comment, update it, otherwise create a new one
        if (botComment) {
          github.rest.issues.updateComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            comment_id: botComment.id,
            body: output
          })
        } else {
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: output
          })
        }
save:
  - name: Set repository ownership
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    working-directory: .
    run: |
      pwd
      sudo chown -R "$USER" "$GITHUB_WORKSPACE"
      git config --global user.name "devops-flipsidecrypto"
      git config --global user.email devops-flipsidecrypto@users.noreply.github.com
  - name: Verify Changed files
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    uses: tj-actions/verify-changed-files@v20
    id: verify-changed-files
  - name: List all changed tracked and untracked files
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false}}
%{ endif ~}
    env:
      CHANGED_FILES: $${{steps.verify-changed-files.outputs.changed_files}}
    run: |
      echo "Changed files: $CHANGED_FILES"
  - name: Push any changes
%{ if allow_build_and_push_only ~}
    if : $${{inputs.build-and-push-only == false && steps.verify-changed-files.outputs.files_changed}}
%{ else ~}
    if: steps.verify-changed-files.outputs.files_changed
%{ endif ~}
    uses: nick-fields/retry@v3
    with:
      timeout_seconds: 30
      max_attempts: 10
      retry_wait_seconds: 30
      command: |
        git add -A
        git commit -m "Terraform repository changes from the ${job_name} workspace [skip actions]"

        if [[ "$GITHUB_EVENT_NAME" == "release" ]]; then
          git push origin HEAD:$${{github.event.release.target_commitish}}
        else
          git push
        fi
      new_command_on_retry: |
        if [[ "$GITHUB_EVENT_NAME" == "release" ]]; then
          git pull --rebase --autostash origin $${{github.event.release.target_commitish}}
        else
          git pull --rebase --autostash
        fi

        git add -A

        git commit -m "Terraform repository changes from the ${job_name} workspace [skip actions]"

        if [[ "$GITHUB_EVENT_NAME" == "release" ]]; then
          git push origin HEAD:$${{github.event.release.target_commitish}}
        else
          git push
        fi
