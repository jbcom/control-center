# Github Sync Workflow

## Configuration

The **config** variable has the following parameters:

* skip_pr: Whether to skip creating the pull request or not
* commit_each_file: Whether to commit each file individually or not
* commit_prefix: Commit prefix
* branch_prefix: Optional override for the default branch prefix
* config_path: Path to the repo-file-sync configuration file
* workflow_file_name: Workflow file name
* sync_to_all: Objects to sync to all repositories
* repositories: Map of repositories and objects by source and destination to sync to
* sync_on_push: Whether to sync on push
* sync_on_call: Whether to sync on call
* sync_on_dispatch: Whether to sync on dispatch
* push_triggers: Paths and branches to use for push activities
* autopopulate_push_path_triggers: Whether to autopopulate push path triggers with the workflow path and sync configuration
* repository_owner: Repository owner to preface every repository with - Leave empty to specify owner in the name of the repositories
* slack_notifications: Whether to send Slack notifications
* slack_webhook_url_secret_name: Slack webhook URL secret name
