#!/bin/bash
# unlock-tfc-workspaces.sh
# Unlocks Terraform Cloud workspaces that are in a locked state
#
# Usage:
#   export TF_API_TOKEN="your-token"  # or TF_TOKEN_app_terraform_io or TFE_TOKEN
#   ./scripts/unlock-tfc-workspaces.sh [--dry-run] [--workspace WORKSPACE_NAME]
#
# Options:
#   --dry-run              List locked workspaces without unlocking
#   --workspace NAME       Unlock only specific workspace (default: all)
#   --organization ORG     TFC organization (default: jbcom)

set -euo pipefail

# Configuration
ORG="${TFC_ORGANIZATION:-jbcom}"
DRY_RUN=false
SPECIFIC_WORKSPACE=""
TFC_API_BASE="https://app.terraform.io/api/v2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --workspace)
            SPECIFIC_WORKSPACE="$2"
            shift 2
            ;;
        --organization)
            ORG="$2"
            shift 2
            ;;
        -h|--help)
            head -n 20 "$0" | grep "^#" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check for TFC token
if [ -z "${TF_TOKEN_app_terraform_io:-}" ] && [ -z "${TF_API_TOKEN:-}" ] && [ -z "${TFE_TOKEN:-}" ]; then
    echo -e "${RED}Error: No TFC token found in environment${NC}"
    echo "Expected one of: TF_TOKEN_app_terraform_io, TF_API_TOKEN, TFE_TOKEN"
    exit 1
fi

# Use whichever token is available
TOKEN="${TF_TOKEN_app_terraform_io:-${TF_API_TOKEN:-${TFE_TOKEN:-}}}"

# Function to make TFC API calls
tfc_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            --header "Authorization: Bearer $TOKEN" \
            --header "Content-Type: application/vnd.api+json" \
            --data "$data" \
            "${TFC_API_BASE}${endpoint}"
    else
        curl -s -X "$method" \
            --header "Authorization: Bearer $TOKEN" \
            --header "Content-Type: application/vnd.api+json" \
            "${TFC_API_BASE}${endpoint}"
    fi
}

# Function to list workspaces
list_workspaces() {
    local page=1
    local all_workspaces="[]"
    
    while true; do
        local response=$(tfc_api GET "/organizations/${ORG}/workspaces?page%5Bnumber%5D=${page}&page%5Bsize%5D=100")
        local workspaces=$(echo "$response" | jq -r '.data')
        
        if [ "$workspaces" = "null" ] || [ "$workspaces" = "[]" ]; then
            break
        fi
        
        all_workspaces=$(echo "$all_workspaces" | jq ". + $workspaces")
        
        # Check if there are more pages
        local next_page=$(echo "$response" | jq -r '.meta.pagination."next-page" // empty')
        if [ -z "$next_page" ]; then
            break
        fi
        
        page=$((page + 1))
    done
    
    echo "$all_workspaces"
}

# Function to unlock a workspace
unlock_workspace() {
    local workspace_id="$1"
    local workspace_name="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would unlock workspace: ${workspace_name}${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Unlocking workspace: ${workspace_name}${NC}"
    
    local response=$(tfc_api POST "/workspaces/${workspace_id}/actions/force-unlock")
    
    if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
        local error_message=$(echo "$response" | jq -r '.errors[0].detail')
        echo -e "${RED}Failed to unlock ${workspace_name}: ${error_message}${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Successfully unlocked: ${workspace_name}${NC}"
        return 0
    fi
}

# Main execution
echo "=========================================="
echo "Terraform Cloud Workspace Unlocker"
echo "=========================================="
echo "Organization: $ORG"
if [ -n "$SPECIFIC_WORKSPACE" ]; then
    echo "Target: $SPECIFIC_WORKSPACE"
else
    echo "Target: All workspaces"
fi
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
else
    echo -e "${RED}Mode: LIVE (workspaces will be unlocked)${NC}"
fi
echo "=========================================="
echo ""

echo "Fetching workspaces..."
workspaces=$(list_workspaces)

if [ "$workspaces" = "[]" ] || [ -z "$workspaces" ]; then
    echo -e "${RED}No workspaces found in organization: $ORG${NC}"
    exit 1
fi

total_count=$(echo "$workspaces" | jq 'length')
echo -e "Found ${BLUE}${total_count}${NC} workspaces"
echo ""

# Filter for locked workspaces
if [ -n "$SPECIFIC_WORKSPACE" ]; then
    locked_workspaces=$(echo "$workspaces" | jq --arg name "$SPECIFIC_WORKSPACE" '[.[] | select(.attributes.name == $name and .attributes.locked == true)]')
else
    locked_workspaces=$(echo "$workspaces" | jq '[.[] | select(.attributes.locked == true)]')
fi

locked_count=$(echo "$locked_workspaces" | jq 'length')

if [ "$locked_count" -eq 0 ]; then
    if [ -n "$SPECIFIC_WORKSPACE" ]; then
        echo -e "${GREEN}Workspace '${SPECIFIC_WORKSPACE}' is not locked or does not exist${NC}"
    else
        echo -e "${GREEN}No locked workspaces found!${NC}"
    fi
    exit 0
fi

echo -e "${YELLOW}Found ${locked_count} locked workspace(s):${NC}"
echo "$locked_workspaces" | jq -r '.[] | "  - \(.attributes.name) (ID: \(.id))"'
echo ""

# Unlock workspaces
unlocked=0
failed=0

while IFS=$'\t' read -r workspace_id workspace_name; do
    if unlock_workspace "$workspace_id" "$workspace_name"; then
        ((unlocked++))
    else
        ((failed++))
    fi
done < <(echo "$locked_workspaces" | jq -r '.[] | "\(.id)\t\(.attributes.name)"')

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Total workspaces: $total_count"
echo "Locked workspaces: $locked_count"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Would unlock: ${locked_count}${NC}"
else
    echo -e "${GREEN}Successfully unlocked: ${unlocked}${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "${RED}Failed to unlock: ${failed}${NC}"
        exit 1
    fi
fi
echo "=========================================="
