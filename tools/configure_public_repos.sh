#!/usr/bin/env bash
# Strip public repos to PURE CODE MIRRORS
# NO workflows - releases happen from control center

set -e

REPOS=(
  "jbcom/extended-data-types"
  "jbcom/lifecyclelogging"
  "jbcom/directed-inputs-class"
  "jbcom/vendor-connectors"
)

for repo in "${REPOS[@]}"; do
  echo "=== Stripping $repo to code-only mirror ==="
  
  # 1. Remove branch protection
  echo "  Removing branch protection..."
  gh api "repos/$repo/branches/main/protection" -X DELETE 2>/dev/null || true
  
  # 2. Delete ALL workflows - releases happen from control center
  echo "  Removing ALL workflows..."
  for workflow in $(gh api "repos/$repo/contents/.github/workflows" --jq '.[].name' 2>/dev/null); do
    sha=$(gh api "repos/$repo/contents/.github/workflows/$workflow" --jq '.sha' 2>/dev/null)
    gh api "repos/$repo/contents/.github/workflows/$workflow" \
      -X DELETE \
      -f message="Remove $workflow - releases from control-center" \
      -f sha="$sha" 2>/dev/null || true
    echo "    Deleted $workflow"
  done
  
  # 3. Delete .github/workflows directory if empty
  gh api "repos/$repo/contents/.github/workflows" 2>/dev/null && \
    echo "  Note: .github/workflows still has files" || \
    echo "  ✓ All workflows removed"
  
  # 4. Delete CODEOWNERS
  echo "  Removing CODEOWNERS..."
  sha=$(gh api "repos/$repo/contents/.github/CODEOWNERS" --jq '.sha' 2>/dev/null || true)
  if [ -n "$sha" ]; then
    gh api "repos/$repo/contents/.github/CODEOWNERS" \
      -X DELETE -f message="Remove CODEOWNERS" -f sha="$sha" 2>/dev/null || true
  fi
  
  # 5. Delete dependabot.yml
  echo "  Removing dependabot..."
  sha=$(gh api "repos/$repo/contents/.github/dependabot.yml" --jq '.sha' 2>/dev/null || true)
  if [ -n "$sha" ]; then
    gh api "repos/$repo/contents/.github/dependabot.yml" \
      -X DELETE -f message="Remove dependabot" -f sha="$sha" 2>/dev/null || true
  fi
  
  echo "✓ $repo is now a pure code mirror"
  echo ""
done

echo "=== Done ==="
echo ""
echo "Public repos are now PURE CODE MIRRORS."
echo "NO workflows, NO CI, NO reviews."
echo ""
echo "Everything happens in control-center:"
echo "1. Develop in packages/"
echo "2. Claude reviews & tests"  
echo "3. Merge → sync pushes code to public repos"
echo "4. Control center publishes to PyPI"
