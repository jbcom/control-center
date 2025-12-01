#!/bin/bash

# Script to generate Terraform import statements for AWS SSO resources
# This script uses the AWS CLI and jq to generate import statements in JSON format

# Ensure AWS CLI doesn't use a pager
export AWS_PAGER=""

# Output file for the import statements
IMPORT_FILE="workspaces/aws/organization/sso_imports.tf"

# Get the SSO instance ARN
INSTANCE_ARN=$(aws sso-admin list-instances | jq -r '.Instances[0].InstanceArn')
echo "SSO Instance ARN: $INSTANCE_ARN"

# Create the import file with header
cat > $IMPORT_FILE << EOF
# AWS SSO Import Statements
# This file was generated automatically by the generate_sso_imports.sh script
# Generated on: $(date)

EOF

# Function to add import statements to the file
add_import() {
  local resource_type=$1
  local resource_name=$2
  local import_id=$3
  
  cat >> $IMPORT_FILE << EOF
import {
  to = $resource_type.$resource_name
  id = "$import_id"
}

EOF
}

# Get all permission sets
echo "Fetching permission sets..."
PERMISSION_SETS=$(aws sso-admin list-permission-sets --instance-arn $INSTANCE_ARN | jq -r '.PermissionSets[]')

# Process each permission set
for PS_ARN in $PERMISSION_SETS; do
  echo "Processing permission set: $PS_ARN"
  
  # Get permission set details
  PS_DETAILS=$(aws sso-admin describe-permission-set --instance-arn $INSTANCE_ARN --permission-set-arn $PS_ARN)
  PS_NAME=$(echo $PS_DETAILS | jq -r '.PermissionSet.Name')
  
  # Clean the name for Terraform resource naming
  CLEAN_NAME=$(echo $PS_NAME | tr '[:upper:]' '[:lower:]' | tr -d ' ' | tr -d '-')
  
  # Add import statement for the permission set
  add_import "aws_ssoadmin_permission_set" "this[\"$CLEAN_NAME\"]" "$INSTANCE_ARN,$PS_ARN"
  
  # Get managed policies attached to this permission set
  MANAGED_POLICIES=$(aws sso-admin list-managed-policies-in-permission-set --instance-arn $INSTANCE_ARN --permission-set-arn $PS_ARN)
  
  # Process each managed policy
  for POLICY_ARN in $(echo $MANAGED_POLICIES | jq -r '.AttachedManagedPolicies[].Arn'); do
    POLICY_NAME=$(basename $POLICY_ARN)
    echo "  Processing managed policy: $POLICY_NAME"
    
    # Add import statement for the managed policy attachment
    add_import "aws_ssoadmin_managed_policy_attachment" "this[\"$CLEAN_NAME-$POLICY_NAME\"]" "$INSTANCE_ARN,$PS_ARN,$POLICY_ARN"
  done
  
  # Check if there's an inline policy
  INLINE_POLICY=$(aws sso-admin get-inline-policy-for-permission-set --instance-arn $INSTANCE_ARN --permission-set-arn $PS_ARN 2>/dev/null)
  if [ $? -eq 0 ] && [ "$(echo $INLINE_POLICY | jq -r '.InlinePolicy')" != "null" ]; then
    echo "  Processing inline policy"
    
    # Add import statement for the inline policy
    add_import "aws_ssoadmin_permission_set_inline_policy" "this[\"$CLEAN_NAME\"]" "$INSTANCE_ARN,$PS_ARN"
  fi
done

# Get all account assignments
echo "Fetching account assignments..."

# Get all AWS accounts
ACCOUNTS=$(aws organizations list-accounts | jq -r '.Accounts[].Id')

for ACCOUNT_ID in $ACCOUNTS; do
  echo "Processing account: $ACCOUNT_ID"
  
  # Get permission sets provisioned to this account
  ACCOUNT_PS=$(aws sso-admin list-permission-sets-provisioned-to-account --instance-arn $INSTANCE_ARN --account-id $ACCOUNT_ID | jq -r '.PermissionSets[]')
  
  for PS_ARN in $ACCOUNT_PS; do
    echo "  Processing permission set: $PS_ARN"
    
    # Get permission set details
    PS_DETAILS=$(aws sso-admin describe-permission-set --instance-arn $INSTANCE_ARN --permission-set-arn $PS_ARN)
    PS_NAME=$(echo $PS_DETAILS | jq -r '.PermissionSet.Name')
    CLEAN_NAME=$(echo $PS_NAME | tr '[:upper:]' '[:lower:]' | tr -d ' ' | tr -d '-')
    
    # Get account assignments for this permission set
    ASSIGNMENTS=$(aws sso-admin list-account-assignments --instance-arn $INSTANCE_ARN --account-id $ACCOUNT_ID --permission-set-arn $PS_ARN)
    
    for ASSIGNMENT in $(echo $ASSIGNMENTS | jq -c '.AccountAssignments[]'); do
      PRINCIPAL_TYPE=$(echo $ASSIGNMENT | jq -r '.PrincipalType')
      PRINCIPAL_ID=$(echo $ASSIGNMENT | jq -r '.PrincipalId')
      
      echo "    Processing assignment: $PRINCIPAL_TYPE/$PRINCIPAL_ID"
      
      # Create a unique name for the assignment
      ASSIGNMENT_NAME="${ACCOUNT_ID}-${CLEAN_NAME}-${PRINCIPAL_TYPE}-${PRINCIPAL_ID}"
      
      # Add import statement for the account assignment
      add_import "aws_ssoadmin_account_assignment" "this[\"$ASSIGNMENT_NAME\"]" "$INSTANCE_ARN,$ACCOUNT_ID,AWS_ACCOUNT,$PRINCIPAL_TYPE,$PRINCIPAL_ID,$PS_ARN"
    done
  done
done

echo "Import statements have been written to $IMPORT_FILE"
