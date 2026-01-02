#!/usr/bin/env bash
# =============================================================================
# ecosystem.sh - Core ecosystem management library
# =============================================================================
# This is the foundational bash library for jbcom-control-center.
# All other scripts and workflows should source this library.
#
# Usage:
#   source "$(dirname "$0")/lib/ecosystem.sh"
#
# Environment Variables:
#   GITHUB_ORG          - GitHub organization (default: jbcom)
#   TERRAGRUNT_ROOT     - Path to terragrunt-stacks (auto-detected)
#   GH_TOKEN            - GitHub token for API access
#   ECOSYSTEM_CACHE_TTL - Cache TTL in seconds (default: 300)
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

export GITHUB_ORG="${GITHUB_ORG:-jbcom}"
export REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "/workspace")}"
export TERRAGRUNT_ROOT="${TERRAGRUNT_ROOT:-${REPO_ROOT}/terragrunt-stacks}"
export ECOSYSTEM_CACHE_DIR="${REPO_ROOT}/.cache/ecosystem"
export ECOSYSTEM_CACHE_TTL="${ECOSYSTEM_CACHE_TTL:-300}"

# Ecosystem categories are defined in repo-config.json

# =============================================================================
# Logging
# =============================================================================

_log() {
  local level="$1"
  shift
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" >&2
}

log_info()  { _log "INFO" "$@"; }
log_warn()  { _log "WARN" "$@"; }
log_error() { _log "ERROR" "$@"; }
log_debug() { [[ "${DEBUG:-}" == "1" ]] && _log "DEBUG" "$@" || true; }

# =============================================================================
# Cache Management
# =============================================================================

_cache_path() {
  local key="$1"
  echo "${ECOSYSTEM_CACHE_DIR}/${key}.cache"
}

_cache_valid() {
  local cache_file="$1"
  if [[ ! -f "$cache_file" ]]; then
    return 1
  fi
  local cache_age=$(($(date +%s) - $(stat -c %Y "$cache_file" 2>/dev/null || stat -f %m "$cache_file" 2>/dev/null || echo 0)))
  [[ $cache_age -lt $ECOSYSTEM_CACHE_TTL ]]
}

cache_get() {
  local key="$1"
  local cache_file
  cache_file=$(_cache_path "$key")
  if _cache_valid "$cache_file"; then
    cat "$cache_file"
    return 0
  fi
  return 1
}

cache_set() {
  local key="$1"
  local value="$2"
  mkdir -p "$ECOSYSTEM_CACHE_DIR"
  echo "$value" > "$(_cache_path "$key")"
}

cache_clear() {
  rm -rf "$ECOSYSTEM_CACHE_DIR"
  log_info "Cache cleared"
}

# =============================================================================
# GitHub API Functions
# =============================================================================

# List all repositories in the organization
gh_list_org_repos() {
  local org="${1:-$GITHUB_ORG}"
  local cache_key="repos_${org}"

  if repos=$(cache_get "$cache_key" 2>/dev/null); then
    echo "$repos"
    return 0
  fi

  log_info "Fetching repositories from GitHub org: $org"
  repos=$(gh repo list "$org" --json name,url,isArchived,primaryLanguage,pushedAt \
    --limit 1000 \
    --jq '.[] | select(.isArchived == false) | "\(.name)\t\(.url)\t\(.primaryLanguage.name // "unknown")\t\(.pushedAt)"' \
    2>/dev/null || echo "")

  if [[ -n "$repos" ]]; then
    cache_set "$cache_key" "$repos"
  fi

  echo "$repos"
}

# Get repository details
gh_repo_info() {
  local repo="$1"
  local full_repo="${GITHUB_ORG}/${repo}"

  gh repo view "$full_repo" --json name,url,description,primaryLanguage,defaultBranchRef,pushedAt,isArchived \
    2>/dev/null || echo "{}"
}

# Check if a repository exists
gh_repo_exists() {
  local repo="$1"
  local full_repo="${GITHUB_ORG}/${repo}"
  gh repo view "$full_repo" --json name >/dev/null 2>&1
}

# =============================================================================
# Ecosystem Discovery Functions
# =============================================================================

# Detect language/ecosystem for a repository
detect_repo_ecosystem() {
  local repo_path="$1"

  if [[ -f "$repo_path/pyproject.toml" ]] || [[ -f "$repo_path/setup.py" ]] || [[ -f "$repo_path/requirements.txt" ]]; then
    echo "python"
  elif [[ -f "$repo_path/package.json" ]]; then
    echo "nodejs"
  elif [[ -f "$repo_path/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_path/Cargo.toml" ]]; then
    echo "rust"
  elif ls "$repo_path"/*.tf >/dev/null 2>&1 || [[ -f "$repo_path/main.tf" ]]; then
    echo "terraform"
  else
    echo "unknown"
  fi
}

# List all managed repositories (from terragrunt stacks)
list_managed_repos() {
  local ecosystem="${1:-}"

  if [[ -n "$ecosystem" ]]; then
    find "$TERRAGRUNT_ROOT/$ecosystem" -name "terragrunt.hcl" -type f 2>/dev/null | \
      xargs -I{} dirname {} | \
      xargs -I{} basename {} | \
      sort -u
  else
    for eco in python nodejs go terraform; do
      if [[ -d "$TERRAGRUNT_ROOT/$eco" ]]; then
        find "$TERRAGRUNT_ROOT/$eco" -name "terragrunt.hcl" -type f 2>/dev/null | \
          while read -r hcl; do
            local repo_name
            repo_name=$(basename "$(dirname "$hcl")")
            echo "$eco/$repo_name"
          done
      fi
    done | sort -u
  fi
}


# =============================================================================
# Repository Classification
# =============================================================================

# Get all repos by ecosystem
get_repos_by_ecosystem() {
  local ecosystem="$1"
  list_managed_repos "$ecosystem"
}


# =============================================================================
# Health Checks
# =============================================================================

# Check ecosystem health
ecosystem_health() {
  local errors=0

  log_info "Running ecosystem health check..."

  # Check if gh is available
  if ! command -v gh >/dev/null 2>&1; then
    log_error "GitHub CLI (gh) not found"
    errors=$((errors + 1))
  fi

  # Check if authenticated
  if ! gh auth status >/dev/null 2>&1; then
    log_error "Not authenticated with GitHub CLI"
    errors=$((errors + 1))
  fi

  if [[ $errors -eq 0 ]]; then
    log_info "Ecosystem health: OK"
    return 0
  else
    log_error "Ecosystem health: $errors errors"
    return 1
  fi
}

# =============================================================================
# Export functions for subshells
# =============================================================================

export -f log_info log_warn log_error log_debug
export -f cache_get cache_set cache_clear
export -f gh_list_org_repos gh_repo_info gh_repo_exists
export -f detect_repo_ecosystem list_managed_repos
export -f get_repos_by_ecosystem
export -f ecosystem_health
