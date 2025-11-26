#!/usr/bin/env bash
# Strip public repos to RELEASE-ONLY containers
# All testing/review happens in control-center

set -e

REPOS=(
  "jbcom/extended-data-types"
  "jbcom/lifecyclelogging"
  "jbcom/directed-inputs-class"
  "jbcom/vendor-connectors"
)

# The ONLY workflow public repos need
RELEASE_WORKFLOW='name: Release

on:
  push:
    branches: [main]

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    environment: release
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build and Release
        run: |
          pip install build
          VERSION="$(date +%Y).$(date +%-m).${{ github.run_number }}"
          find src -name "__init__.py" -exec sed -i "s/__version__ = .*/__version__ = \"$VERSION\"/" {} \;
          python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
'

for repo in "${REPOS[@]}"; do
  echo "=== Stripping $repo to release-only ==="
  
  # 1. Remove branch protection
  echo "  Removing branch protection..."
  gh api "repos/$repo/branches/main/protection" -X DELETE 2>/dev/null || true
  
  # 2. Enable auto-merge
  echo "  Enabling auto-merge..."
  gh repo edit "$repo" --enable-auto-merge 2>/dev/null || true
  
  # 3. Delete ALL workflows except what we'll create
  echo "  Removing all workflows..."
  for workflow in $(gh api "repos/$repo/contents/.github/workflows" --jq '.[].name' 2>/dev/null); do
    sha=$(gh api "repos/$repo/contents/.github/workflows/$workflow" --jq '.sha' 2>/dev/null)
    gh api "repos/$repo/contents/.github/workflows/$workflow" \
      -X DELETE \
      -f message="Remove $workflow - all CI happens in control-center" \
      -f sha="$sha" 2>/dev/null || true
  done
  
  # 4. Create the release-only workflow
  echo "  Creating release-only workflow..."
  echo "$RELEASE_WORKFLOW" | base64 -w 0 > /tmp/release.yml.b64
  gh api "repos/$repo/contents/.github/workflows/release.yml" \
    -X PUT \
    -f message="Release-only workflow - all testing in control-center" \
    -f content="$(cat /tmp/release.yml.b64)" 2>/dev/null || true
  
  # 5. Delete CODEOWNERS (no reviews needed)
  echo "  Removing CODEOWNERS..."
  sha=$(gh api "repos/$repo/contents/.github/CODEOWNERS" --jq '.sha' 2>/dev/null || true)
  if [ -n "$sha" ]; then
    gh api "repos/$repo/contents/.github/CODEOWNERS" \
      -X DELETE \
      -f message="Remove CODEOWNERS - no reviews needed" \
      -f sha="$sha" 2>/dev/null || true
  fi
  
  # 6. Delete dependabot.yml (handled in control-center)
  echo "  Removing dependabot..."
  sha=$(gh api "repos/$repo/contents/.github/dependabot.yml" --jq '.sha' 2>/dev/null || true)
  if [ -n "$sha" ]; then
    gh api "repos/$repo/contents/.github/dependabot.yml" \
      -X DELETE \
      -f message="Remove dependabot - handled in control-center" \
      -f sha="$sha" 2>/dev/null || true
  fi
  
  echo "✓ $repo is now release-only"
  echo ""
done

echo "=== Done ==="
echo ""
echo "Public repos are now RELEASE-ONLY containers."
echo "All testing, reviews, and validation happen in control-center."
echo ""
echo "Flow:"
echo "1. Develop in control-center/packages/"
echo "2. Claude reviews & tests"
echo "3. Merge to main → sync pushes to public repos"
echo "4. Public repos just build & publish to PyPI"
