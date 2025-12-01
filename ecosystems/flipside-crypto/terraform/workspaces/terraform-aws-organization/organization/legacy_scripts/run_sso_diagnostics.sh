#!/bin/bash
# Run SSO Diagnostics Script
# This script runs diagnostics for multiple SSO admin resources with broken imports
# Usage: ./run_sso_diagnostics.sh

set -e

# Text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RESET="\033[0m"

# Function to print section headers
print_header() {
  echo -e "\n${BOLD}${BLUE}=== $1 ===${RESET}\n"
}

# Function to print info messages
print_info() {
  echo -e "${BLUE}ℹ $1${RESET}"
}

# Check if the diagnostics script exists
if [[ ! -f "./sso_import_diagnostics.sh" ]]; then
  echo -e "${RED}Error: sso_import_diagnostics.sh not found in the current directory${RESET}"
  exit 1
fi

# Make sure the diagnostics script is executable
chmod +x ./sso_import_diagnostics.sh

# List of resources to diagnose
# Format: "resource_type:resource_name"
RESOURCES=(
  "aws_ssoadmin_permission_set:poweruseraccess"
  "aws_ssoadmin_permission_set:administratoraccess"
  "aws_ssoadmin_permission_set:viewonlyaccess"
  "aws_organizations_policy:FullAWSAccess"
)

# Run diagnostics for each resource
print_header "Running SSO Import Diagnostics for Multiple Resources"

for resource in "${RESOURCES[@]}"; do
  # Split the resource into type and name
  IFS=':' read -r resource_type resource_name <<< "$resource"
  
  print_info "Running diagnostics for $resource_type:$resource_name"
  
  # Run the diagnostics script for this resource
  ./sso_import_diagnostics.sh "$resource_type" "$resource_name"
  
  # Add a separator between resources
  echo -e "\n${YELLOW}----------------------------------------${RESET}\n"
done

print_header "Diagnostics Complete"
print_info "All diagnostics have been completed. Review the output above for import statements and resource details."
