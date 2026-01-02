#!/bin/bash
set -euo pipefail

# Function to post a comment and exit on failure
post_comment_and_exit() {
  local message="$1"
  echo "$message"
  gh issue comment "$ISSUE_NUMBER" --body "$message" || echo "Failed to post comment to issue #$ISSUE_NUMBER"
  exit 1
}

# General validation for all commands
if [[ -z "$ISSUE_NUMBER" ]]; then
  echo "Error: Required environment variable ISSUE_NUMBER is not set."
  exit 1
fi

# Validate required environment variables
MISSING_ENV=0

if [[ -z "$COMMENT_BODY" ]]; then
  echo "Error: COMMENT_BODY environment variable is required but not set." >&2
  MISSING_ENV=1
fi

if [[ -z "$ISSUE_NUMBER" ]]; then
  echo "Error: ISSUE_NUMBER environment variable is required but not set." >&2
  MISSING_ENV=1
fi

if [[ -z "$REPOSITORY" ]]; then
  echo "Error: REPOSITORY environment variable is required but not set." >&2
  MISSING_ENV=1
fi

if [[ -z "$DEFAULT_BRANCH" ]]; then
  echo "Error: DEFAULT_BRANCH environment variable is required but not set." >&2
  MISSING_ENV=1
fi

if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "Error: GITHUB_TOKEN environment variable is required but not set." >&2
  MISSING_ENV=1
fi

if [[ "$MISSING_ENV" -ne 0 ]]; then
  echo "One or more required environment variables are missing. Exiting." >&2
  exit 1
fi
# If /jules command is present, delegate to Google Jules
if [[ "$COMMENT_BODY" == *"/jules"* ]]; then
  echo "🤖 Received '/jules' command. Delegating to Google Jules..."

  # Validate required environment variables for Jules
  if [[ -z "$GOOGLE_JULES_API_KEY" ]]; then
    post_comment_and_exit "⚠️ GOOGLE_JULES_API_KEY not configured. Cannot delegate to Jules."
  fi
  if [[ -z "$JULES_PROJECT_ID" ]]; then
    post_comment_and_exit "⚠️ JULES_PROJECT_ID not configured. Cannot delegate to Jules."
  fi
  if [[ -z "$REPOSITORY" ]]; then
    post_comment_and_exit "⚠️ REPOSITORY not configured. Cannot delegate to Jules."
  fi
  if [[ -z "$DEFAULT_BRANCH" ]]; then
    post_comment_and_exit "⚠️ DEFAULT_BRANCH not configured. Cannot delegate to Jules."
  fi

  gh issue comment "$ISSUE_NUMBER" --body "🤖 Received '/jules' command. Creating Jules session..."

  TASK=$(echo "$COMMENT_BODY" | sed 's|/jules[[:space:]]*||' | python - << 'PY'
import sys
s = sys.stdin.read()
print(s[:1000])
PY
  )
  [ -z "$TASK" ] && TASK="Fix issue #$ISSUE_NUMBER"

  RESPONSE=$(curl -s -X POST "https://jules.googleapis.com/v1alpha/projects/${JULES_PROJECT_ID}/sessions" \
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

  SESSION_URL=$(echo "$RESPONSE" | jq -r '.url // empty')

  if [ -n "$SESSION_URL" ]; then
    gh issue comment "$ISSUE_NUMBER" --body "## 🤖 Jules Session Created

  ➡️ **[Monitor Session]($SESSION_URL)**

  Jules will analyze the issue and create a PR." || post_comment_and_exit "❌ Failed to post Jules session URL to issue."
  else
    # Avoid logging the full raw API response, which may contain sensitive information.
    # Try to extract a minimal error message if the response is JSON.
    ERROR_MESSAGE=$(echo "$RESPONSE" 2>/dev/null | jq -r '.error.message // empty' 2>/dev/null || true)
    if [ -n "$ERROR_MESSAGE" ]; then
      echo "Failed to create Jules session. Error: $ERROR_MESSAGE"
    else
      echo "Failed to create Jules session. The Jules API returned an unexpected response."
    fi
    post_comment_and_exit "❌ Failed to create Jules session. Please check logs."
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
