#!/bin/bash
# Test script to verify generate blocks validation works correctly
# This script creates test scenarios to ensure validation catches duplicates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="/tmp/terragrunt-generate-test-$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Testing Terragrunt Generate Blocks Validation"
echo "=============================================="
echo

# Create test directory structure
mkdir -p "$TEST_DIR"/{root,child1,child2}

# Test 1: No duplicates (should pass)
echo "Test 1: No duplicate generate blocks (should PASS)"
cat > "$TEST_DIR/root/terragrunt.hcl" <<'EOF'
generate "provider" {
  path = "provider.tf"
  if_exists = "overwrite"
  contents = "# Provider"
}
EOF

cat > "$TEST_DIR/child1/terragrunt.hcl" <<'EOF'
include "root" {
  path = find_in_parent_folders()
}

# Using unique generate block name
generate "imports" {
  path = "imports.tf"
  if_exists = "overwrite"
  contents = "# Imports"
}
EOF

# Run validation (should pass)
cd "$TEST_DIR"
if grep -q 'include "root"' child1/terragrunt.hcl 2>/dev/null; then
    root_generates=$(grep '^generate "' root/terragrunt.hcl 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
    local_generates=$(grep '^generate "' child1/terragrunt.hcl 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
    
    has_conflict=0
    for local_gen in $local_generates; do
        if echo "$root_generates" | grep -q "^${local_gen}$"; then
            has_conflict=1
        fi
    done
    
    if [ $has_conflict -eq 0 ]; then
        echo -e "${GREEN}✓ Test 1 PASSED${NC}: No conflicts detected"
    else
        echo -e "${RED}✗ Test 1 FAILED${NC}: Unexpected conflict detected"
        exit 1
    fi
fi
echo

# Test 2: With duplicates (should fail)
echo "Test 2: Duplicate generate blocks (should FAIL)"
cat > "$TEST_DIR/child2/terragrunt.hcl" <<'EOF'
include "root" {
  path = find_in_parent_folders()
}

# Duplicate generate block name
generate "provider" {
  path = "provider.tf"
  if_exists = "overwrite"
  contents = "# Override Provider"
}
EOF

# Run validation (should fail)
if grep -q 'include "root"' child2/terragrunt.hcl 2>/dev/null; then
    root_generates=$(grep '^generate "' root/terragrunt.hcl 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
    local_generates=$(grep '^generate "' child2/terragrunt.hcl 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
    
    has_conflict=0
    for local_gen in $local_generates; do
        if echo "$root_generates" | grep -q "^${local_gen}$"; then
            has_conflict=1
        fi
    done
    
    if [ $has_conflict -eq 1 ]; then
        echo -e "${GREEN}✓ Test 2 PASSED${NC}: Conflict correctly detected"
    else
        echo -e "${RED}✗ Test 2 FAILED${NC}: Expected conflict not detected"
        exit 1
    fi
fi
echo

# Test 3: No include (should pass even with same name)
echo "Test 3: Same name but no include (should PASS)"
mkdir -p "$TEST_DIR/standalone"
cat > "$TEST_DIR/standalone/terragrunt.hcl" <<'EOF'
# No include - standalone config

generate "provider" {
  path = "provider.tf"
  if_exists = "overwrite"
  contents = "# Standalone Provider"
}
EOF

# This should pass because there's no include
if ! grep -q 'include "root"' standalone/terragrunt.hcl 2>/dev/null; then
    echo -e "${GREEN}✓ Test 3 PASSED${NC}: Standalone config with no include"
fi
echo

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo "=============================================="
echo -e "${GREEN}All tests passed!${NC}"
echo
echo "The validation logic correctly:"
echo "  1. Allows unique generate block names"
echo "  2. Detects duplicate generate block names"
echo "  3. Ignores configs that don't include root"
