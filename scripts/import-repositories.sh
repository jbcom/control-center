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

# Validate repository name for security
validate_repo_name() {
  local repo="$1"
  if [[ ! "$repo" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "    ERROR: Invalid repository name: $repo"
    return 1
  fi
  return 0
}

# Check if resource already exists in state
resource_in_state() {
  local resource_address="$1"
  terraform state show "$resource_address" &>/dev/null
}

# Import resource if not already in state
import_if_needed() {
  local resource_address="$1"
  local import_id="$2"
  
  if resource_in_state "$resource_address"; then
    echo "    (already in state)"
    return 0
  fi
  
  if terraform import "$resource_address" "$import_id"; then
    echo "    ✓ imported successfully"
    return 0
  else
    echo "    ✗ import failed (resource may not exist)"
    return 1
  fi
}

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

# Track import results
imported=0
skipped=0
failed=0

for repo in "${REPOS[@]}"; do
  echo ""
  echo "==> Importing $repo..."
  
  # Validate repository name
  if ! validate_repo_name "$repo"; then
    ((failed++))
    continue
  fi
  
  # Import repository settings
  echo "  - Repository settings"
  if import_if_needed "github_repository.managed[\"$repo\"]" "$repo"; then
    ((imported++))
  else
    ((failed++))
  fi
  
  # Import branch protection
  echo "  - Branch protection"
  if import_if_needed "github_branch_protection.main[\"$repo\"]" "$repo:main"; then
    ((imported++))
  else
    # Branch protection may not exist yet, which is not a failure
    ((skipped++))
  fi
  
  # Note: github_repository_security_and_analysis and github_repository_pages
  # are managed inline and don't need separate imports
done

echo ""
echo "=== Import Complete ==="
echo ""
echo "Results:"
echo "  - Imported: $imported resources"
echo "  - Skipped (already in state): $skipped resources"
echo "  - Failed: $failed resources"
echo ""
echo "Next steps:"
echo "  1. Run 'terraform plan' to review the configuration"
echo "  2. Run 'terraform apply' to align repositories with desired state"
