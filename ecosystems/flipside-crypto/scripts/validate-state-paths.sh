#!/bin/bash
# Validate that all workspace backend configurations match the state registry
# 
# Run this BEFORE any terraform operation after migration
# Exit code 0 = all paths validated
# Exit code 1 = mismatch detected (DO NOT PROCEED)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
STATE_REGISTRY="$REPO_ROOT/config/state-paths.yaml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "🔍 State Path Validation"
echo "=============================================="
echo ""

if [ ! -f "$STATE_REGISTRY" ]; then
    echo -e "${RED}❌ CRITICAL: State registry not found at $STATE_REGISTRY${NC}"
    exit 1
fi

# Check for yq
if ! command -v yq &> /dev/null; then
    echo -e "${YELLOW}⚠️  yq not installed, using grep fallback${NC}"
    USE_YQ=false
else
    USE_YQ=true
fi

errors=0
warnings=0
validated=0

# Find all terraform workspaces
for workspace_dir in $(find "$REPO_ROOT/terraform/workspaces" -name "backend.tf" -exec dirname {} \; 2>/dev/null); do
    workspace_name=$(echo "$workspace_dir" | sed "s|$REPO_ROOT/terraform/workspaces/||")
    
    echo -n "Checking $workspace_name... "
    
    # Extract declared state key from backend.tf
    declared_key=$(grep -oP 'key\s*=\s*"\K[^"]+' "$workspace_dir/backend.tf" 2>/dev/null || true)
    
    if [ -z "$declared_key" ]; then
        echo -e "${YELLOW}⚠️  No key found in backend.tf${NC}"
        ((warnings++))
        continue
    fi
    
    # Look up expected key from registry
    if [ "$USE_YQ" = true ]; then
        expected_key=$(yq ".workspaces[\"$workspace_name\"].state_key" "$STATE_REGISTRY" 2>/dev/null || echo "null")
    else
        # Fallback: simple grep
        expected_key=$(grep -A1 "^  $workspace_name:" "$STATE_REGISTRY" | grep "state_key:" | awk '{print $2}' || echo "null")
    fi
    
    if [ "$expected_key" = "null" ] || [ -z "$expected_key" ]; then
        echo -e "${YELLOW}⚠️  Not in registry (new workspace?)${NC}"
        ((warnings++))
        continue
    fi
    
    if [ "$declared_key" != "$expected_key" ]; then
        echo -e "${RED}❌ MISMATCH${NC}"
        echo -e "   Declared: $declared_key"
        echo -e "   Expected: $expected_key"
        ((errors++))
    else
        echo -e "${GREEN}✅${NC}"
        ((validated++))
    fi
done

echo ""
echo "=============================================="
echo "Summary:"
echo "  Validated: $validated"
echo "  Warnings:  $warnings"
echo "  Errors:    $errors"
echo "=============================================="

if [ $errors -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ CRITICAL: State path mismatches detected!${NC}"
    echo -e "${RED}   DO NOT run terraform apply until resolved.${NC}"
    echo -e "${RED}   Mismatched state paths WILL orphan resources.${NC}"
    exit 1
fi

if [ $warnings -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Warnings present - review before proceeding${NC}"
fi

echo ""
echo -e "${GREEN}✅ All state paths validated${NC}"
exit 0
