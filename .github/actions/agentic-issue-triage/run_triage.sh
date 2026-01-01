#!/bin/bash
set -eo pipefail

# Trim leading/trailing whitespace from the comment body
COMMENT_BODY=$(echo "$COMMENT_BODY" | xargs)

# If /jules command is present, delegate to Google Jules
if [[ "$COMMENT_BODY" =~ ^/jules ]]; then
  echo "🤖 Received '/jules' command. Delegating to Google Jules..."

  if [[ -z "$GOOGLE_JULES_API_KEY" ]]; then
    gh issue comment "$ISSUE_NUMBER" --body "⚠️ GOOGLE_JULES_API_KEY not configured. Cannot delegate to Jules."
    exit 1
  fi

  TASK=$(echo "$COMMENT_BODY" | sed -e 's|^/jules[[:space:]]*||')
  TASK=$(echo "$TASK" | xargs)

  if [[ -z "$TASK" ]]; then
    gh issue comment "$ISSUE_NUMBER" --body "⚠️ Missing prompt for '/jules' command.

    **Usage:** \`/jules <Your detailed request>\`

    Please provide a clear description of the task you want Jules to perform."
    exit 0
  fi

  gh issue comment "$ISSUE_NUMBER" --body "🤖 Received '/jules' command. Creating Jules session for: \"$TASK\"..."

  RESPONSE=$(curl -s -X POST "https://jules.googleapis.com/v1alpha/sessions" \
    -H "X-Goog-Api-Key: $GOOGLE_JULES_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n \
      --arg task "Fix issue #$ISSUE_NUMBER: $TASK" \
      --arg repo "$REPOSITORY" \
      --arg branch "$DEFAULT_BRANCH" \
      '{
        prompt: $task,
        sourceContext: {
          source: ("sources/github/" + ($repo | split("/")[0]) + "/" + ($repo | split("/")[1])),
          githubRepoContext: { startingBranch: $branch }
        },
        automationMode: "AUTO_CREATE_PR"
      }')")

  SESSION_ID=$(echo "$RESPONSE" | jq -r '.id // empty')
  if [ -z "$SESSION_ID" ]; then
     SESSION_ID=$(echo "$RESPONSE" | jq -r '.name // empty' | xargs basename)
  fi
  SESSION_URL="https://console.google.com/jules/session/$SESSION_ID"

  if [ -n "$SESSION_ID" ]; then
    gh issue comment "$ISSUE_NUMBER" --body "## 🤖 Jules Session Created

  ➡️ **[Monitor Session]($SESSION_URL)**

  Jules will analyze the issue and create a PR."
  else
    echo "Failed to create Jules session: $RESPONSE"
    gh issue comment "$ISSUE_NUMBER" --body "❌ Failed to create Jules session. Please check logs."
    exit 1
  fi
  exit 0
fi

# If /cursor command is present, delegate to Cursor
if [[ "$COMMENT_BODY" =~ ^/cursor ]]; then
  echo "🤖 Received '/cursor' command. Delegating to Cursor Cloud Agent..."
  # ... logic for Cursor delegation if needed ...
  gh issue comment "$ISSUE_NUMBER" --body "🤖 Received '/cursor' command. Cursor delegation is handled by the orchestrator."
  exit 0
fi

# Fallback to standard triage if no specific command
echo "Performing standard issue triage..."
# agentic-control@1.1.0 doesn't have issue-triage command yet
# For now, we'll just acknowledge the issue
# agentic triage quick "$COMMENT_BODY"
gh issue comment "$ISSUE_NUMBER" --body "🤖 Issue received and queued for triage."
