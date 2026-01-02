#!/bin/bash

set -euo pipefail

# Trim leading/trailing whitespace from comment body
COMMENT_BODY_TRIMMED=$(echo "$COMMENT_BODY" | xargs)

# If /jules command is present, delegate to Google Jules
if [[ "$COMMENT_BODY_TRIMMED" == /jules* ]]; then
  echo "🤖 Received '/jules' command. Delegating to Google Jules..."

  if [[ -z "$GOOGLE_JULES_API_KEY" ]]; then
    gh issue comment "$ISSUE_NUMBER" --body "⚠️ GOOGLE_JULES_API_KEY not configured. Cannot delegate to Jules."
    exit 1
  fi

  TASK=$(echo "$COMMENT_BODY_TRIMMED" | sed -E 's|^/jules[[:space:]]*||')

  if [[ -z "$TASK" ]]; then
    gh issue comment "$ISSUE_NUMBER" --body "🤖 Received an empty '/jules' command. Please provide a task, e.g., \`/jules Implement the new feature.\`"
    exit 0
  fi

  gh issue comment "$ISSUE_NUMBER" --body "🤖 Received '/jules $TASK' command. Creating Jules session..."

  JSON_PAYLOAD=$(jq -n \
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
    }')

  RESPONSE=$(curl -s -X POST "https://jules.googleapis.com/v1alpha/sessions" \
    -H "X-Goog-Api-Key: $GOOGLE_JULES_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD")

  SESSION_URL=$(echo "$RESPONSE" | jq -r '.url // empty')

  if [ -n "$SESSION_URL" ]; then
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
if [[ "$COMMENT_BODY" == *"/cursor"* ]]; then
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
