#!/bin/bash
# SSO Import Diagnostics Script
# This script helps diagnose issues with SSO admin resources that have broken imports
# Usage: ./sso_import_diagnostics.sh [resource_type] [resource_name]
# Example: ./sso_import_diagnostics.sh aws_ssoadmin_permission_set poweruseraccess

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

# Function to print success messages
print_success() {
  echo -e "${GREEN}✓ $1${RESET}"
}

# Function to print error messages
print_error() {
  echo -e "${RED}✗ $1${RESET}"
}

# Function to print warning messages
print_warning() {
  echo -e "${YELLOW}! $1${RESET}"
}

# Function to print info messages
print_info() {
  echo -e "${BLUE}ℹ $1${RESET}"
}

# Function to check if AWS CLI is installed
check_aws_cli() {
  print_header "Checking AWS CLI"
  if command -v aws &> /dev/null; then
    print_success "AWS CLI is installed"
    aws --version
  else
    print_error "AWS CLI is not installed"
    exit 1
  fi
}

# Function to check AWS credentials
check_aws_credentials() {
  print_header "Checking AWS Credentials"
  if aws sts get-caller-identity --no-cli-pager &> /dev/null; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text --no-cli-pager)
    print_success "AWS credentials are valid for account: $ACCOUNT_ID"
  else
    print_error "AWS credentials are not valid"
    exit 1
  fi
}

# Function to get SSO instance ARN
get_sso_instance_arn() {
  print_header "Getting SSO Instance ARN"
  SSO_INSTANCE_ARN=$(aws sso-admin list-instances --query "Instances[0].InstanceArn" --output text --no-cli-pager)
  
  if [[ -z "$SSO_INSTANCE_ARN" || "$SSO_INSTANCE_ARN" == "None" ]]; then
    print_error "No SSO instance found"
    exit 1
  else
    print_success "SSO instance found: $SSO_INSTANCE_ARN"
  fi
}

# Function to diagnose permission set
diagnose_permission_set() {
  local permission_set_name=$1
  print_header "Diagnosing Permission Set: $permission_set_name"
  
  # List all permission sets
  print_info "Listing all permission sets..."
  aws sso-admin list-permission-sets --instance-arn "$SSO_INSTANCE_ARN" --no-cli-pager
  
  # Try to find the permission set by name
  print_info "Searching for permission set by name: $permission_set_name"
  PERMISSION_SETS=$(aws sso-admin list-permission-sets --instance-arn "$SSO_INSTANCE_ARN" --no-cli-pager --query "PermissionSets" --output json)
  
  # For each permission set, get details and check if name matches
  echo "$PERMISSION_SETS" | jq -r '.[]' | while read -r PERMISSION_SET_ARN; do
    DETAILS=$(aws sso-admin describe-permission-set --instance-arn "$SSO_INSTANCE_ARN" --permission-set-arn "$PERMISSION_SET_ARN" --no-cli-pager)
    PS_NAME=$(echo "$DETAILS" | jq -r '.PermissionSet.Name')
    
    if [[ "$PS_NAME" == "$permission_set_name" || "$PS_NAME" =~ "$permission_set_name" ]]; then
      print_success "Found permission set: $PS_NAME with ARN: $PERMISSION_SET_ARN"
      
      # Print permission set details
      print_info "Permission Set Details:"
      echo "$DETAILS" | jq
      
      # List account assignments for this permission set
      print_info "Account Assignments for this Permission Set:"
      aws organizations list-accounts --no-cli-pager --query "Accounts[].Id" --output json | jq -r '.[]' | while read -r ACCOUNT_ID; do
        ASSIGNMENTS=$(aws sso-admin list-account-assignments --instance-arn "$SSO_INSTANCE_ARN" --permission-set-arn "$PERMISSION_SET_ARN" --account-id "$ACCOUNT_ID" --no-cli-pager 2>/dev/null || echo '{"AccountAssignments": []}')
        
        if [[ $(echo "$ASSIGNMENTS" | jq '.AccountAssignments | length') -gt 0 ]]; then
          print_success "Found assignments in account $ACCOUNT_ID:"
          echo "$ASSIGNMENTS" | jq
          
          # Generate import statement
          print_info "Terraform Import Statement:"
          echo "terraform import 'aws_ssoadmin_permission_set.this[\"$permission_set_name\"]' $SSO_INSTANCE_ARN,$PERMISSION_SET_ARN"
          
          # Generate account assignment import statements
          print_info "Account Assignment Import Statements:"
          echo "$ASSIGNMENTS" | jq -r '.AccountAssignments[] | "terraform import \"aws_ssoadmin_account_assignment.this[\"\(.PrincipalType)-\(.PrincipalId)-\(.AccountId)-\(.PermissionSetArn)\"]\" \(.InstanceArn),\(.AccountId),\(.PermissionSetArn),\(.PrincipalType),\(.PrincipalId)"'
        fi
      done
      
      return 0
    fi
  done
  
  print_error "Permission set not found: $permission_set_name"
  print_warning "Available permission sets:"
  echo "$PERMISSION_SETS" | jq -r '.[]' | while read -r PERMISSION_SET_ARN; do
    DETAILS=$(aws sso-admin describe-permission-set --instance-arn "$SSO_INSTANCE_ARN" --permission-set-arn "$PERMISSION_SET_ARN" --no-cli-pager)
    PS_NAME=$(echo "$DETAILS" | jq -r '.PermissionSet.Name')
    echo "  - $PS_NAME ($PERMISSION_SET_ARN)"
  done
}

# Function to diagnose organization policy
diagnose_organization_policy() {
  local policy_name=$1
  print_header "Diagnosing Organization Policy: $policy_name"
  
  # List all policies
  print_info "Listing all service control policies..."
  POLICIES=$(aws organizations list-policies --filter SERVICE_CONTROL_POLICY --no-cli-pager)
  
  # Try to find the policy by name
  print_info "Searching for policy by name: $policy_name"
  POLICY=$(echo "$POLICIES" | jq -r --arg name "$policy_name" '.Policies[] | select(.Name == $name or (.Name | contains($name)))')
  
  if [[ -n "$POLICY" ]]; then
    POLICY_ID=$(echo "$POLICY" | jq -r '.Id')
    print_success "Found policy: $policy_name with ID: $POLICY_ID"
    
    # Print policy details
    print_info "Policy Details:"
    aws organizations describe-policy --policy-id "$POLICY_ID" --no-cli-pager | jq
    
    # List policy targets
    print_info "Policy Targets:"
    aws organizations list-targets-for-policy --policy-id "$POLICY_ID" --no-cli-pager | jq
    
    # Generate import statement
    print_info "Terraform Import Statement:"
    echo "terraform import 'aws_organizations_policy.service_control[\"$policy_name\"]' $POLICY_ID"
    
    return 0
  fi
  
  print_error "Policy not found: $policy_name"
  print_warning "Available service control policies:"
  echo "$POLICIES" | jq -r '.Policies[] | "  - " + .Name + " (" + .Id + ")"'
}

# Main function
main() {
  print_header "SSO Import Diagnostics"
  
  # Check if resource type and name are provided
  if [[ $# -lt 2 ]]; then
    print_error "Usage: $0 [resource_type] [resource_name]"
    print_info "Example: $0 aws_ssoadmin_permission_set poweruseraccess"
    print_info "Example: $0 aws_organizations_policy FullAWSAccess"
    exit 1
  fi
  
  RESOURCE_TYPE=$1
  RESOURCE_NAME=$2
  
  # Check AWS CLI and credentials
  check_aws_cli
  check_aws_credentials
  
  # Process based on resource type
  case "$RESOURCE_TYPE" in
    aws_ssoadmin_permission_set)
      get_sso_instance_arn
      diagnose_permission_set "$RESOURCE_NAME"
      ;;
    aws_organizations_policy)
      diagnose_organization_policy "$RESOURCE_NAME"
      ;;
    *)
      print_error "Unsupported resource type: $RESOURCE_TYPE"
      print_info "Supported resource types: aws_ssoadmin_permission_set, aws_organizations_policy"
      exit 1
      ;;
  esac
}

# Run the script with all arguments
main "$@"
