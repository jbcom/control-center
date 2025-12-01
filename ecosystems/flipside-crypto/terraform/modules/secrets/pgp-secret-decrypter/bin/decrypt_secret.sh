#!/bin/bash

# Exit if any of the intermediate steps fail
set -e

# Parse input from stdin
eval "$(jq -r '@sh "ENCRYPTED_SECRET=\(.encrypted_secret)"')"

# Check if required inputs are provided
if [ -z "$ENCRYPTED_SECRET" ]; then
  echo "Error: Missing required input 'encrypted_secret'" >&2
  exit 1
fi

# Check if keybase is installed
if ! command -v keybase &> /dev/null; then
  echo "Error: keybase command not found. Please install Keybase CLI." >&2
  exit 1
fi

# Check if keybase is logged in
if ! keybase status | grep -q "Logged in"; then
  echo "Error: Not logged in to Keybase. Please log in first." >&2
  exit 1
fi

# Try to decrypt the secret
DECRYPTED_SECRET=""
if echo "$ENCRYPTED_SECRET" | base64 --decode | keybase pgp decrypt 2>/dev/null; then
  DECRYPTED_SECRET=$(echo "$ENCRYPTED_SECRET" | base64 --decode | keybase pgp decrypt 2>/dev/null)
else
  echo "Error: Failed to decrypt the secret. Make sure you have access to the PGP key." >&2
  exit 1
fi

# Output the result as JSON
jq -n --arg secret "$DECRYPTED_SECRET" '{"secret": $secret}'
