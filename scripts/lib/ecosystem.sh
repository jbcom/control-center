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
#   GITHUB_ORG          - GitHub organization (default: jbdevprimary)
#   ECOSYSTEM_ROOT      - Path to ecosystems/oss (auto-detected)
#   TERRAGRUNT_ROOT     - Path to terragrunt-stacks (auto-detected)
#   GH_TOKEN            - GitHub token for API access
#   ECOSYSTEM_CACHE_TTL - Cache TTL in seconds (default: 300)
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

export GITHUB_ORG="${GITHUB_ORG:-jbdevprimary}"
export REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "/workspace")}"
export ECOSYSTEM_ROOT="${ECOSYSTEM_ROOT:-${REPO_ROOT}/ecosystems/oss}"
export TERRAGRUNT_ROOT="${TERRAGRUNT_ROOT:-${REPO_ROOT}/terragrunt-stacks}"
export ECOSYSTEM_CACHE_DIR="${REPO_ROOT}/.cache/ecosystem"
export ECOSYSTEM_CACHE_TTL="${ECOSYSTEM_CACHE_TTL:-300}"

# Ecosystem categories
declare -A ECOSYSTEM_LANGUAGES=(
  ["python"]="py"
  ["nodejs"]="ts"
  ["go"]="go"
  ["terraform"]="tf"
  ["rust"]="rs"
)

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
    if grep -q '"type": "module"' "$repo_path/package.json" 2>/dev/null || \
       [[ -f "$repo_path/tsconfig.json" ]]; then
      echo "nodejs"
    else
      echo "nodejs"
    fi
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

# List all submodules in ecosystems/oss
list_ecosystem_submodules() {
  git config --file "$REPO_ROOT/.gitmodules" --get-regexp 'submodule\.ecosystems/oss/.*.path' 2>/dev/null | \
    awk '{print $2}' | \
    xargs -I{} basename {} | \
    sort -u
}

# Get repos that are managed but not submodules
list_missing_submodules() {
  local managed
  local submodules
  
  managed=$(list_managed_repos | awk -F'/' '{print $2}' | sort -u)
  submodules=$(list_ecosystem_submodules)
  
  comm -23 <(echo "$managed") <(echo "$submodules")
}

# Get repos that are submodules but not managed
list_orphan_submodules() {
  local managed
  local submodules
  
  managed=$(list_managed_repos | awk -F'/' '{print $2}' | sort -u)
  submodules=$(list_ecosystem_submodules)
  
  comm -13 <(echo "$managed") <(echo "$submodules")
}

# =============================================================================
# Submodule Management Functions
# =============================================================================

# Add a repository as a submodule
submodule_add() {
  local repo_name="$1"
  local target_path="${ECOSYSTEM_ROOT}/${repo_name}"
  local repo_url="https://github.com/${GITHUB_ORG}/${repo_name}.git"
  
  if [[ -d "$target_path" ]]; then
    log_warn "Submodule already exists: $repo_name"
    return 0
  fi
  
  log_info "Adding submodule: $repo_name"
  git -C "$REPO_ROOT" submodule add "$repo_url" "ecosystems/oss/${repo_name}"
}

# Update a submodule to latest
submodule_update() {
  local repo_name="$1"
  local target_path="${ECOSYSTEM_ROOT}/${repo_name}"
  
  if [[ ! -d "$target_path" ]]; then
    log_error "Submodule not found: $repo_name"
    return 1
  fi
  
  log_info "Updating submodule: $repo_name"
  git -C "$target_path" fetch origin
  git -C "$target_path" checkout origin/main 2>/dev/null || \
    git -C "$target_path" checkout origin/master 2>/dev/null || \
    log_warn "Could not checkout main/master for $repo_name"
}

# Initialize all submodules
submodule_init_all() {
  log_info "Initializing all submodules..."
  git -C "$REPO_ROOT" submodule update --init --recursive
}

# Update all submodules to latest
submodule_update_all() {
  log_info "Updating all submodules to latest..."
  git -C "$REPO_ROOT" submodule update --remote --recursive
}

# Sync submodules with managed repos
submodule_sync() {
  local dry_run="${1:-false}"
  local missing
  
  missing=$(list_missing_submodules)
  
  if [[ -z "$missing" ]]; then
    log_info "All managed repos have submodules"
    return 0
  fi
  
  echo "$missing" | while read -r repo; do
    if [[ -n "$repo" ]]; then
      if [[ "$dry_run" == "true" ]]; then
        log_info "[DRY RUN] Would add submodule: $repo"
      else
        submodule_add "$repo"
      fi
    fi
  done
}

# =============================================================================
# Repository Classification
# =============================================================================

# Get all repos by ecosystem
get_repos_by_ecosystem() {
  local ecosystem="$1"
  list_managed_repos "$ecosystem"
}

# Build matrix JSON for GitHub Actions
build_matrix_json() {
  local include_skip="${1:-false}"
  
  echo "["
  local first=true
  
  for eco in python nodejs go terraform; do
    list_managed_repos "$eco" 2>/dev/null | while read -r entry; do
      local repo_name
      repo_name=$(basename "$entry")
      
      if [[ "$first" != "true" ]]; then
        echo ","
      fi
      first=false
      
      cat <<EOF
  {
    "ecosystem": "$eco",
    "repo": "${GITHUB_ORG}/${repo_name}",
    "downstream_package": "terragrunt-stacks/${eco}/${repo_name}",
    "submodule_path": "ecosystems/oss/${repo_name}"
  }
EOF
    done
  done
  
  if [[ "$include_skip" == "true" ]]; then
    echo ","
    cat <<EOF
  {
    "ecosystem": "rust",
    "repo": "",
    "downstream_package": "",
    "skip": true
  }
EOF
  fi
  
  echo "]"
}

# =============================================================================
# Downstream/Upstream Sync
# =============================================================================

# Sync files from control center to a downstream repo
sync_to_downstream() {
  local repo_name="$1"
  local files_dir="${2:-$REPO_ROOT/repository-files}"
  local target_path="${ECOSYSTEM_ROOT}/${repo_name}"
  local ecosystem
  
  if [[ ! -d "$target_path" ]]; then
    log_error "Target repo not found: $target_path"
    return 1
  fi
  
  ecosystem=$(detect_repo_ecosystem "$target_path")
  
  log_info "Syncing files to $repo_name (ecosystem: $ecosystem)"
  
  # Always sync files
  if [[ -d "$files_dir/always-sync" ]]; then
    cp -r "$files_dir/always-sync/." "$target_path/"
  fi
  
  # Ecosystem-specific files
  if [[ -d "$files_dir/$ecosystem" ]]; then
    cp -r "$files_dir/$ecosystem/." "$target_path/"
  fi
}

# Pull updates from upstream (the actual repo)
pull_from_upstream() {
  local repo_name="$1"
  local target_path="${ECOSYSTEM_ROOT}/${repo_name}"
  
  if [[ ! -d "$target_path" ]]; then
    log_error "Submodule not found: $target_path"
    return 1
  fi
  
  log_info "Pulling updates from upstream: $repo_name"
  git -C "$target_path" fetch origin
  git -C "$target_path" pull origin main 2>/dev/null || \
    git -C "$target_path" pull origin master 2>/dev/null || \
    log_warn "Could not pull from main/master for $repo_name"
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
    ((errors++))
  fi
  
  # Check if authenticated
  if ! gh auth status >/dev/null 2>&1; then
    log_error "Not authenticated with GitHub CLI"
    ((errors++))
  fi
  
  # Check for missing submodules
  local missing
  missing=$(list_missing_submodules | wc -l)
  if [[ "$missing" -gt 0 ]]; then
    log_warn "Missing submodules: $missing"
  fi
  
  # Check for orphan submodules
  local orphans
  orphans=$(list_orphan_submodules | wc -l)
  if [[ "$orphans" -gt 0 ]]; then
    log_warn "Orphan submodules (not in terragrunt): $orphans"
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
export -f detect_repo_ecosystem list_managed_repos list_ecosystem_submodules
export -f list_missing_submodules list_orphan_submodules
export -f submodule_add submodule_update submodule_init_all submodule_update_all submodule_sync
export -f get_repos_by_ecosystem build_matrix_json
export -f sync_to_downstream pull_from_upstream
export -f ecosystem_health
