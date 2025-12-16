# Control Center issue review playbook

The control center must keep all open and closed GitHub issues in view when coordinating triage and release orchestration.
Use the helper script below to export a current snapshot from the private GitHub repository so downstream agentic-triage
flows can ingest and consider them alongside ecosystem tasks.

## How to export the issue snapshot

1. Install the GitHub CLI if it is not already available:
   ```bash
   # For installation instructions, see the official GitHub CLI documentation:
   # https://cli.github.com/
   ```

2. Export the issues using a token that can read `jbcom/jbcom-control-center`:
   ```bash
   # Requires a GitHub token with access to jbcom/jbcom-control-center
   export GITHUB_TOKEN="<token>"

   # Optional: override repo name (defaults to jbcom/jbcom-control-center)
   # export REPO="jbcom/jbcom-control-center"

   # Write the snapshot to docs/CONTROL-CENTER-ISSUES.md (default)
   ./scripts/export-control-center-issues.sh

   # Or write to a custom path
   ./scripts/export-control-center-issues.sh /tmp/control-center-issues.md
   ```

The script authenticates `gh` for the current shell when a token is provided so pagination works without manual login. It fails fast if `gh` is missing or no token is set.

The snapshot groups open and closed issues separately and omits pull requests to keep the list focused on work tracking.

## Integrating with triage workflows
- Generate a fresh snapshot before running agentic-triage so the flow has the latest control-center constraints.
- Attach or reference the generated markdown in triage prompts so support agents account for active goals.
- Re-run after triage to capture any new issues opened during the session and keep the hub state synchronized.
