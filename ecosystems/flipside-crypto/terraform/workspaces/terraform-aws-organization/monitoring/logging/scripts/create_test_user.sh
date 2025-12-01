#!/bin/bash
set -e

# This script creates a test user in the Cognito user pool and adds them to the authorized group

# Parse command line arguments
EMAIL=""
PASSWORD=""
GROUP_NAME=""
USER_POOL_ID=""

print_usage() {
  echo "Usage: $0 -e EMAIL -p PASSWORD -g GROUP_NAME -u USER_POOL_ID"
  echo "  -e EMAIL         Email address for the test user"
  echo "  -p PASSWORD      Initial password for the test user"
  echo "  -g GROUP_NAME    Name of the authorized group"
  echo "  -u USER_POOL_ID  Cognito User Pool ID"
  exit 1
}

while getopts "e:p:g:u:" opt; do
  case ${opt} in
    e )
      EMAIL=$OPTARG
      ;;
    p )
      PASSWORD=$OPTARG
      ;;
    g )
      GROUP_NAME=$OPTARG
      ;;
    u )
      USER_POOL_ID=$OPTARG
      ;;
    \? )
      print_usage
      ;;
  esac
done

# Validate required arguments
if [[ -z "$EMAIL" || -z "$PASSWORD" || -z "$GROUP_NAME" || -z "$USER_POOL_ID" ]]; then
  echo "Error: Missing required arguments"
  print_usage
fi

# Extract username from email
USERNAME=$(echo "$EMAIL" | cut -d '@' -f 1)

echo "Creating user $USERNAME with email $EMAIL in user pool $USER_POOL_ID..."

# Create the user
aws cognito-idp admin-create-user \
  --user-pool-id "$USER_POOL_ID" \
  --username "$USERNAME" \
  --user-attributes \
    Name=email,Value="$EMAIL" \
    Name=email_verified,Value=true \
  --temporary-password "$PASSWORD" \
  --message-action SUPPRESS

echo "Setting permanent password for user $USERNAME..."

# Set a permanent password for the user
aws cognito-idp admin-set-user-password \
  --user-pool-id "$USER_POOL_ID" \
  --username "$USERNAME" \
  --password "$PASSWORD" \
  --permanent

echo "Adding user $USERNAME to group $GROUP_NAME..."

# Add the user to the authorized group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id "$USER_POOL_ID" \
  --username "$USERNAME" \
  --group-name "$GROUP_NAME"

echo "User $USERNAME created successfully and added to group $GROUP_NAME."
echo "Email: $EMAIL"
echo "Password: $PASSWORD"
echo "Please change the password after first login." 