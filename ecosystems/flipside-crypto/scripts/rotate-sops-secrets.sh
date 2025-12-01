#!/usr/bin/env bash
# ----------------------------------------------------------------------
# rotate-sops-secrets.sh
# Re-encrypt every SOPS file under the secrets directory with the KMS key
# specified in .sops.yaml
# ----------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS_DIR="${SECRETS_DIR:-${REPO_ROOT}/secrets}"
SOPS_CONFIG="${SOPS_CONFIG:-${REPO_ROOT}/.sops.yaml}"

usage() {
  cat <<'EOF'
Usage: scripts/rotate-sops-secrets.sh [--verify]

Re-encrypts all SOPS-managed files in the secrets directory with the
KMS key specified in .sops.yaml

Options:
  --verify   Only verify that all secrets decrypt successfully.
  -h, --help Show this message.

Environment Variables:
  SECRETS_DIR   Path to secrets directory (default: secrets/)
  SOPS_CONFIG   Path to SOPS config file (default: .sops.yaml)

Requirements:
  Requires sops installed.
  Requires .sops.yaml to exist with KMS configuration.

Examples:
  scripts/rotate-sops-secrets.sh
EOF
}

VERIFY_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --verify)
      VERIFY_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_tool() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required tool: $1" >&2
    exit 1
  fi
}

require_tool sops

if [[ ! -d "$SECRETS_DIR" ]]; then
  echo "Secrets directory not found at $SECRETS_DIR" >&2
  exit 1
fi

if [[ ! -f "$SOPS_CONFIG" ]]; then
  echo "SOPS config not found at $SOPS_CONFIG" >&2
  exit 1
fi

echo "Using SOPS config: $SOPS_CONFIG"

mapfile -t SOPS_FILES < <(grep -RIl '"sops"' "$SECRETS_DIR" || true)

if [[ ${#SOPS_FILES[@]} -eq 0 ]]; then
  echo "No SOPS encrypted files found in $SECRETS_DIR"
  exit 0
fi

export SOPS_CONFIG="$SOPS_CONFIG"

if [[ $VERIFY_ONLY -eq 1 ]]; then
  echo "Verifying ${#SOPS_FILES[@]} secrets decrypt successfully..."
  for file in "${SOPS_FILES[@]}"; do
    sops --decrypt "$file" >/dev/null
  done
  echo "All secrets decrypted without error."
  exit 0
fi

echo "Rotating ${#SOPS_FILES[@]} secrets using keys from .sops.yaml..."
echo ""

for file in "${SOPS_FILES[@]}"; do
  echo "→ $file"
  if ! sops updatekeys --yes "$file" >/dev/null; then
    echo "Failed to rotate $file" >&2
    exit 1
  fi
done

echo ""
echo "Rotation complete. Updated ${#SOPS_FILES[@]} files."
