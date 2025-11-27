#!/bin/bash
# Assume the Cursor IAM role and export credentials
# Usage: source .cursor/scripts/assume-cursor-role.sh

set -e

if [ -z "$CURSOR_AWS_ASSUME_IAM_ROLE_ARN" ]; then
    echo "❌ CURSOR_AWS_ASSUME_IAM_ROLE_ARN not set"
    exit 1
fi

echo "🔑 Assuming role: $CURSOR_AWS_ASSUME_IAM_ROLE_ARN"

# This won't work without base credentials, but documenting the intended flow
echo "⚠️  Note: This requires base AWS credentials to assume the role"
echo "   The IAM role will be automatically used by AWS MCP servers in process-compose"
echo ""
echo "   For manual AWS CLI usage, you need base credentials first."
