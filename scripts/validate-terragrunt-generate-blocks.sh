#!/bin/bash
# Validate that no Terragrunt stacks have duplicate generate block names
# This prevents the error: "Detected generate blocks with the same name"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAGRUNT_STACKS_DIR="$REPO_ROOT/terragrunt-stacks"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Validating Terragrunt generate blocks in $TERRAGRUNT_STACKS_DIR"
echo

# Track overall status
has_errors=0

# Find all terragrunt.hcl files
while IFS= read -r -d '' terragrunt_file; do
    # Get the directory containing this terragrunt.hcl
    stack_dir=$(dirname "$terragrunt_file")
    # Portable relative path calculation
    stack_name="${stack_dir#$TERRAGRUNT_STACKS_DIR/}"
    
    # Skip if this is the root config (it's meant to be inherited)
    if [ "$terragrunt_file" = "$TERRAGRUNT_STACKS_DIR/terragrunt.hcl" ]; then
        continue
    fi
    
    # Check if this stack includes the root config
    if grep -q 'include "root"' "$terragrunt_file" 2>/dev/null; then
        # This stack inherits from root - check for conflicting generate blocks
        root_generates=$(grep '^generate "' "$TERRAGRUNT_STACKS_DIR/terragrunt.hcl" 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
        local_generates=$(grep '^generate "' "$terragrunt_file" 2>/dev/null | sed 's/generate "\([^"]*\)".*/\1/' || true)
        
        if [ -n "$local_generates" ]; then
            # Check for conflicts
            for local_gen in $local_generates; do
                if echo "$root_generates" | grep -q "^${local_gen}$"; then
                    echo -e "${RED}ERROR${NC}: Stack '$stack_name' has generate block '$local_gen' that conflicts with root config"
                    echo "  File: $terragrunt_file"
                    echo "  Root also defines: generate \"$local_gen\""
                    echo "  Solution: Rename to a unique name (e.g., '${stack_name}_${local_gen}')"
                    echo
                    has_errors=1
                fi
            done
        fi
    fi
    
done < <(find "$TERRAGRUNT_STACKS_DIR" -name "terragrunt.hcl" -print0)

# Summary
echo "---"
if [ $has_errors -eq 0 ]; then
    echo -e "${GREEN}✓ No duplicate generate block names found${NC}"
    exit 0
else
    echo -e "${RED}✗ Found duplicate generate block names${NC}"
    echo "  Run 'terragrunt run-all plan' to see the full error"
    exit 1
fi
