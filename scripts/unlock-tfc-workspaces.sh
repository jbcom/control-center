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
#
# Exit Codes:
#   0 - Success (no locked workspaces or all unlocked)
#   1 - Found locked workspaces (dry-run only) or failed to unlock some
#   2 - API error or configuration error

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
    local http_code
    local response
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" --fail-with-body -X "$method" \
            --header "Authorization: Bearer $TOKEN" \
            --header "Content-Type: application/vnd.api+json" \
            --data "$data" \
            "${TFC_API_BASE}${endpoint}" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" --fail-with-body -X "$method" \
            --header "Authorization: Bearer $TOKEN" \
            --header "Content-Type: application/vnd.api+json" \
            "${TFC_API_BASE}${endpoint}" 2>&1)
    fi
    
    # Check curl exit code
    local curl_exit=$?
    if [ $curl_exit -ne 0 ]; then
        echo -e "${RED}Error: API call failed (curl exit code: $curl_exit)${NC}" >&2
        return 1
    fi
    
    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n1)
    response=$(echo "$response" | sed '$d')
    
    # Check HTTP status
    if [[ ! "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo -e "${RED}Error: API returned HTTP $http_code${NC}" >&2
        echo "$response" >&2
        return 1
    fi
    
    # Validate JSON
    if ! echo "$response" | jq empty 2>/dev/null; then
        echo -e "${RED}Error: Invalid JSON response from API${NC}" >&2
        return 1
    fi
    
    echo "$response"
}

# Function to list workspaces
list_workspaces() {
    local page=1
    local all_workspaces="[]"
    local page_size=100
    
    while true; do
        # URL encode the query parameters
        local query="page[number]=${page}&page[size]=${page_size}"
        local encoded_query=$(echo "$query" | sed 's/\[/%5B/g; s/\]/%5D/g')
        
        local response
        if ! response=$(tfc_api GET "/organizations/${ORG}/workspaces?${encoded_query}"); then
            echo -e "${RED}Error: Failed to list workspaces${NC}" >&2
            return 1
        fi
        
        # Safely extract data array
        local workspaces
        if ! workspaces=$(echo "$response" | jq -r '.data // empty' 2>/dev/null); then
            echo -e "${RED}Error: Failed to parse workspace data${NC}" >&2
            return 1
        fi
        
        if [ -z "$workspaces" ] || [ "$workspaces" = "null" ] || [ "$workspaces" = "[]" ]; then
            break
        fi
        
        # Merge workspaces
        if ! all_workspaces=$(echo "$all_workspaces" | jq ". + $workspaces" 2>/dev/null); then
            echo -e "${RED}Error: Failed to merge workspace data${NC}" >&2
            return 1
        fi
        
        # Check if there are more pages
        local next_page
        next_page=$(echo "$response" | jq -r '.meta.pagination."next-page" // empty' 2>/dev/null)
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
    
    local response
    if ! response=$(tfc_api POST "/workspaces/${workspace_id}/actions/force-unlock"); then
        echo -e "${RED}Failed to unlock ${workspace_name}: API call failed${NC}"
        return 1
    fi
    
    # Check for errors in response
    if echo "$response" | jq -e '.errors' > /dev/null 2>&1; then
        local error_message=$(echo "$response" | jq -r '.errors[0].detail // "Unknown error"')
        echo -e "${RED}Failed to unlock ${workspace_name}: ${error_message}${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Successfully unlocked: ${workspace_name}${NC}"
    return 0
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
if ! workspaces=$(list_workspaces); then
    echo -e "${RED}Failed to fetch workspaces from organization: $ORG${NC}"
    exit 2
fi

if [ "$workspaces" = "[]" ] || [ -z "$workspaces" ]; then
    echo -e "${RED}No workspaces found in organization: $ORG${NC}"
    exit 2
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
    exit 0  # Success - no locks
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
    echo "=========================================="
    exit 1  # Exit with 1 to signal locks found (allows automation to detect locks)
else
    echo -e "${GREEN}Successfully unlocked: ${unlocked}${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "${RED}Failed to unlock: ${failed}${NC}"
        echo "=========================================="
        exit 1  # Exit with 1 to signal partial failure
    fi
    echo "=========================================="
    exit 0  # Success - all unlocked
fi
