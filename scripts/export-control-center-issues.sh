#!/usr/bin/env bash
set -euo pipefail

REPO=${REPO:-jbcom/jbcom-control-center}
GH_TOKEN_VALUE=${GITHUB_JBCOM_TOKEN:-${GITHUB_TOKEN:-${GH_TOKEN:-}}}
OUTPUT_PATH=${1:-docs/CONTROL-CENTER-ISSUES.md}

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI is required (https://cli.github.com/)" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required (https://stedolan.github.io/jq/)" >&2
  exit 1
fi

if [[ -z "${GH_TOKEN_VALUE}" ]]; then
  echo "ERROR: Set GITHUB_JBCOM_TOKEN, GITHUB_TOKEN, or GH_TOKEN to access ${REPO}" >&2
  exit 1
fi

export GH_TOKEN="${GH_TOKEN_VALUE}"

# Ensure the GitHub CLI session is authenticated for this shell so pagination works reliably.
if ! gh auth status -h github.com >/dev/null 2>&1; then
  printf '%s' "${GH_TOKEN_VALUE}" | gh auth login --with-token --hostname github.com --git-protocol https >/dev/null
fi

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%SZ")

{
  echo "# jbcom-control-center issue snapshot"
  echo
  echo "- Repository: ${REPO}"
  echo "- Generated at: ${TIMESTAMP}"
  echo
  echo "## Open issues"
  gh api "/repos/${REPO}/issues?state=open&per_page=100" --paginate \
    | jq -r '.[] | select(.pull_request|not) | "- #\(.number) \(.title) (labels: \([.labels[].name] | join(", ")))"' \
    || echo "(no open issues found)"
  echo
  echo "## Closed issues"
  gh api "/repos/${REPO}/issues?state=closed&per_page=100" --paginate \
    | jq -r '.[] | select(.pull_request|not) | "- #\(.number) \(.title) (closed: \(.closed_at | split("T")[0]))"' \
    || echo "(no closed issues found)"
} > "${OUTPUT_PATH}"

echo "Wrote issue snapshot to ${OUTPUT_PATH}" >&2
