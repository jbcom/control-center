#!/bin/bash

# Create directories
mkdir -p lambda_function
cd lambda_function

# Create package.json
cat > package.json << EOF
{
  "name": "quicksight-setup-lambda",
  "version": "1.0.0",
  "description": "Lambda function to set up QuickSight subscription and resources",
  "main": "index.js",
  "author": "",
  "license": "ISC",
  "dependencies": {
    "aws-sdk": "^2.1030.0"
  }
}
EOF

# Install dependencies
npm install

# Create parent directory for zip file
cd ..
mkdir -p dist

# Zip the Lambda function code
zip -r dist/lambda_function.zip lambda_function/node_modules lambda_function/index.js

echo "Lambda function package created at dist/lambda_function.zip" 