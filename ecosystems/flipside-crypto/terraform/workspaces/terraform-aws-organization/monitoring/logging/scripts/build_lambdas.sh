#!/bin/bash
set -e

# Parse input from Terraform
eval "$(jq -r '@sh "LAMBDAS_DIR=\(.lambdas_dir) COGNITO_REGION=\(.cognito_region) COGNITO_USER_POOL_ID=\(.cognito_user_pool_id) COGNITO_APP_CLIENT_ID=\(.cognito_app_client_id) COGNITO_DOMAIN=\(.cognito_domain) COOKIE_DOMAIN=\(.cookie_domain)"')"

# Create temp directory for builds
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Function to build and package a Lambda function
build_lambda() {
  local function_dir=$1
  local function_name=$(basename "$function_dir")
  local build_dir="$TEMP_DIR/$function_name"
  local zip_file="$TEMP_DIR/${function_name}.zip"
  
  echo "Building $function_name Lambda..."
  
  # Create build directory and copy function code
  mkdir -p "$build_dir"
  cp -r "$function_dir"/* "$build_dir/"
  
  # Install dependencies using npm
  cd "$build_dir"
  
  # Create/update package.json if it doesn't exist with correct dependencies
  if [ ! -f "package.json" ]; then
    cat > package.json << EOF
{
  "name": "taxonomy-${function_name}-handler",
  "version": "1.0.0",
  "description": "Lambda@Edge handler for taxonomy website authentication",
  "main": "index.js",
  "license": "MIT",
  "dependencies": {}
}
EOF
  fi
  
  # Install cognito-at-edge package
  npm install --save cognito-at-edge@latest
  
  # Create zip file
  zip -r "$zip_file" ./* > /dev/null
  
  # Return path to the zip file
  echo "$zip_file"
}

# Build all Lambda functions
VIEWER_REQUEST_ZIP=$(build_lambda "$LAMBDAS_DIR/viewer-request")
PARSE_AUTH_ZIP=$(build_lambda "$LAMBDAS_DIR/parse-auth")
REFRESH_AUTH_ZIP=$(build_lambda "$LAMBDAS_DIR/refresh-auth")
SIGN_OUT_ZIP=$(build_lambda "$LAMBDAS_DIR/sign-out")
HTTP_HEADERS_ZIP=$(build_lambda "$LAMBDAS_DIR/http-headers")

# Output the results as JSON for Terraform
jq -n \
  --arg viewer_request_zip "$VIEWER_REQUEST_ZIP" \
  --arg parse_auth_zip "$PARSE_AUTH_ZIP" \
  --arg refresh_auth_zip "$REFRESH_AUTH_ZIP" \
  --arg sign_out_zip "$SIGN_OUT_ZIP" \
  --arg http_headers_zip "$HTTP_HEADERS_ZIP" \
  '{
    "viewer_request_zip": $viewer_request_zip,
    "parse_auth_zip": $parse_auth_zip,
    "refresh_auth_zip": $refresh_auth_zip,
    "sign_out_zip": $sign_out_zip,
    "http_headers_zip": $http_headers_zip
  }' 