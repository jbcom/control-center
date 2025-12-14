#!/usr/bin/env bash
#
# Apply bootstrap fix to update TFC workspace execution_mode
#
# This script updates all 18 TFC workspaces from execution_mode = "remote" to "local"
# to fix the "No Terraform configuration files found" error.
#
# Prerequisites:
#   - TF_API_TOKEN environment variable must be set
#   - Terraform and Terragrunt must be installed
#
# Usage:
#   export TF_API_TOKEN="your-terraform-cloud-token"
#   ./scripts/apply-bootstrap-fix.sh [--plan-only]
#
# Options:
#   --plan-only   Only show what would change (default: false)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (using $0 for POSIX compatibility)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BOOTSTRAP_DIR="${REPO_ROOT}/terragrunt-stacks/bootstrap"

# Parse arguments
PLAN_ONLY=false
if [[ "${1:-}" == "--plan-only" ]]; then
    PLAN_ONLY=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TFC Workspace Execution Mode Fix${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check TF_API_TOKEN
if [[ -z "${TF_API_TOKEN:-}" ]]; then
    echo -e "${RED}❌ TF_API_TOKEN environment variable is not set${NC}"
    echo ""
    echo "Please export your Terraform Cloud API token:"
    echo "  export TF_API_TOKEN=\"your-terraform-cloud-token\""
    echo ""
    echo "Get your token from: https://app.terraform.io/app/settings/tokens"
    exit 1
fi
echo -e "${GREEN}✓ TF_API_TOKEN is set${NC}"

# Check terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ terraform is not installed${NC}"
    echo "Install from: https://developer.hashicorp.com/terraform/install"
    exit 1
fi
TF_VERSION=$(terraform version 2>/dev/null | head -1 | sed 's/Terraform //' || echo "unknown")
if [ -n "$TF_VERSION" ] && [ "$TF_VERSION" != "unknown" ]; then
    echo -e "${GREEN}✓ terraform ${TF_VERSION}${NC}"
else
    echo -e "${GREEN}✓ terraform installed${NC}"
fi

# Check terragrunt
if ! command -v terragrunt &> /dev/null; then
    echo -e "${RED}❌ terragrunt is not installed${NC}"
    echo "Install from: https://terragrunt.gruntwork.io/docs/getting-started/install/"
    exit 1
fi
TG_VERSION=$(terragrunt --version 2>/dev/null | head -1 || echo "unknown")
if [ -n "$TG_VERSION" ] && [ "$TG_VERSION" != "unknown" ]; then
    echo -e "${GREEN}✓ terragrunt ${TG_VERSION}${NC}"
else
    echo -e "${GREEN}✓ terragrunt installed${NC}"
fi

echo ""
echo -e "${YELLOW}Issue Background:${NC}"
echo "  • TFC workspaces were configured with execution_mode = 'remote'"
echo "  • GitHub Actions runs Terragrunt locally (CLI-driven workflow)"
echo "  • TFC tried to execute Terraform but found no .tf files"
echo "  • Error: 'No Terraform configuration files found in working directory'"
echo ""
echo -e "${YELLOW}Solution:${NC}"
echo "  • Change execution_mode from 'remote' to 'local'"
echo "  • TFC will only store state, not execute Terraform"
echo "  • Updates all 18 repository workspaces"
echo ""

# Navigate to bootstrap directory
cd "${BOOTSTRAP_DIR}"
echo -e "${BLUE}Working directory: ${BOOTSTRAP_DIR}${NC}"
echo ""

# Initialize Terragrunt
echo -e "${YELLOW}Initializing Terragrunt...${NC}"
if ! terragrunt init; then
    echo -e "${RED}❌ Terragrunt init failed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Initialization complete${NC}"
echo ""

# Plan changes
echo -e "${YELLOW}Planning changes...${NC}"
echo ""
if ! terragrunt plan -out=tfplan; then
    echo -e "${RED}❌ Terragrunt plan failed${NC}"
    exit 1
fi
echo ""
echo -e "${GREEN}✓ Plan complete${NC}"
echo ""

# Check if this is plan-only mode
if [[ "${PLAN_ONLY}" == "true" ]]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Plan completed successfully!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "Review the changes above. If they look correct, run:"
    echo "  ./scripts/apply-bootstrap-fix.sh"
    echo ""
    echo "Or apply manually:"
    echo "  cd terragrunt-stacks/bootstrap"
    echo "  terragrunt apply tfplan"
    exit 0
fi

# Apply changes
echo -e "${YELLOW}Applying changes...${NC}"
echo ""
echo "This will update all 18 TFC workspaces with execution_mode = 'local'"
echo ""
read -p "Do you want to continue? (yes/y/no/n): " -r
echo ""

# Convert to lowercase for comparison (using tr for bash 3.x compatibility)
REPLY_LOWER=$(echo "${REPLY}" | tr '[:upper:]' '[:lower:]')
if [[ ! "${REPLY_LOWER}" =~ ^(y|yes)$ ]]; then
    echo -e "${YELLOW}Aborted by user${NC}"
    exit 0
fi

if ! terragrunt apply tfplan; then
    echo -e "${RED}❌ Terragrunt apply failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Bootstrap fix applied successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Verify workspaces in TFC UI:"
echo "     https://app.terraform.io/app/jbcom/workspaces"
echo ""
echo "  2. Test the terraform-sync workflow:"
echo "     • Go to Actions → 'Terragrunt Repository Sync'"
echo "     • Run workflow with apply: false (plan only)"
echo "     • Verify no 'No configuration files' errors"
echo ""
echo "  3. If successful, test with apply: true"
echo ""
echo -e "${GREEN}All 18 workspaces now use execution_mode = 'local'${NC}"
echo "TFC will only store state, GitHub Actions will execute Terraform"
