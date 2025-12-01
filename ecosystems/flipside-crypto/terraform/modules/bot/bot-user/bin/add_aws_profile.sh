#!/usr/bin/env bash

set -exo pipefail

if [[ -z "$PROFILE_NAME" || -z "$AWS_ACCESS_KEY" || -z "$AWS_SECRET_ACCESS_KEY" ]]; then
  echo "Must set PROFILE_NAME, AWS_ACCESS_KEY, and AWS_SECRET_ACCESS_KEY as environment variables"
  exit 1
fi

CREDENTIALS_FILE="$HOME"/.aws/credentials
touch "$CREDENTIALS_FILE"

if grep -q "\[${PROFILE_NAME}]" < "$CREDENTIALS_FILE"; then
  echo "Found profile matching ${PROFILE_NAME}, deleting it"
  sed -ie "/\[${PROFILE_NAME}]/,+2d" "$CREDENTIALS_FILE"
else
  echo "No profile found matching ${PROFILE_NAME}"
fi

cat <<EOF >> "$CREDENTIALS_FILE"
[${PROFILE_NAME}]
aws_access_key_id = ${AWS_ACCESS_KEY}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF