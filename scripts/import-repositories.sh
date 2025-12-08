#!/usr/bin/env bash
# Import all existing repositories into Terraform state
# This script should be run once to import existing resources

set -e

REPOS=(
  # Python
  "agentic-crew"
  "ai_game_dev"
  "directed-inputs-class"
  "extended-data-types"
  "lifecyclelogging"
  "python-terraform-bridge"
  "rivers-of-reckoning"
  "vendor-connectors"
  # Node.js
  "agentic-control"
  "otter-river-rush"
  "otterfall"
  "pixels-pygame-palace"
  "rivermarsh"
  "strata"
  # Go
  "port-api"
  "vault-secret-sync"
  # Terraform
  "terraform-github-markdown"
  "terraform-repository-automation"
)

echo "=== Importing GitHub Repositories into Terraform State ==="
echo ""
echo "This script will import ${#REPOS[@]} repositories and their configurations."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

cd "$(dirname "$0")/../terraform"

for repo in "${REPOS[@]}"; do
  echo ""
  echo "==> Importing $repo..."
  
  # Import repository
  echo "  - Repository settings"
  # Import repository (validate repo name for security)
  echo "  - Repository settings"
  if [[ ! "$repo" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "    ERROR: Invalid repository name: $repo"
    continue
  fi
  terraform import "github_repository.managed[\"$repo\"]" "$repo" || echo "    (already imported or doesn't exist)"
  
  # Import branch protection (using node_id pattern)
  echo "  - Branch protection"
  # Import branch protection (validate repo name for security)
  echo "  - Branch protection"
  if [[ ! "$repo" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "    ERROR: Invalid repository name: $repo"
    continue
  fi
  terraform import "github_branch_protection.main[\"$repo\"]" "$repo:main" || echo "    (already imported or doesn't exist)"
  
  # Note: github_repository_security_and_analysis and github_repository_pages
  # are managed inline and don't need separate imports
done

echo ""
echo "=== Import Complete ==="
echo ""
echo "Next steps:"
echo "  1. Run 'terraform plan' to review the configuration"
echo "  2. Run 'terraform apply' to align repositories with desired state"
