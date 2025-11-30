# CI Release Fix Summary

## Problem Statement
The CI workflow didn't actually release packages to PyPI and used "hacky custom bullshit" instead of proper GitHub Actions and python-semantic-release (PSR).

## Root Causes Identified

### 1. Manual Version Parsing (Lines 177-188)
**Before:**
```bash
CURRENT=$(grep '^version = ' pyproject.toml | head -1 | sed 's/version = "\([^"]*\)"/\1/')
NEW=$(semantic-release --noop version --print 2>/dev/null || echo "$CURRENT")
# Complex logic to compare versions
```

**After:**
```bash
NEW_VERSION=$(semantic-release --noop version --print 2>/dev/null || true)
if [ -n "$NEW_VERSION" ]; then
  echo "should_release=true"
fi
```

**Why:** PSR already handles version detection. Just check if it outputs a version.

### 2. Manual Git Operations (Lines 190-200)
**Before:**
```bash
semantic-release version --no-vcs-release
git push origin main --follow-tags -o ci.skip
```

**After:**
```bash
semantic-release version
# PSR handles commit, tag, and push automatically
```

**Why:** The `--no-vcs-release` flag disables PSR's git operations, forcing manual push. This is exactly backwards - let PSR do what it's designed to do!

### 3. Custom Sync Script Instead of Action
**Before:**
```bash
git clone "https://x-access-token:${GH_TOKEN}@github.com/${{ matrix.repo }}.git" target
cd target
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -r ../packages/${{ matrix.package }}/* .
git config user.name "jbcom-bot"
git config user.email "jbcom-bot@users.noreply.github.com"
git add -A
(git diff --staged --quiet || git commit -m "🚀 v${{ steps.check.outputs.version }}") && git push
```

**After:**
```yaml
- uses: BetaHuhn/repo-file-sync-action@v1
  with:
    GH_PAT: ${{ secrets.CI_GITHUB_TOKEN }}
    CONFIG_PATH: .github/sync/${{ matrix.package }}.yml
```

**Why:** Use proper GitHub Action with declarative config instead of hacky bash script!

### 4. Custom Docs Deployment Script Instead of Action
**Before:**
```bash
git clone --branch gh-pages --depth 1 "..." gh-pages 2>/dev/null || {
  mkdir gh-pages && cd gh-pages && git init -b gh-pages
  # ... more manual git operations
}
find gh-pages -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
cp -r packages/${{ matrix.package }}/docs/_build/* gh-pages/
# ... more manual operations
git push -uf origin gh-pages
```

**After:**
```yaml
- uses: peaceiris/actions-gh-pages@v4
  with:
    personal_token: ${{ secrets.CI_GITHUB_TOKEN }}
    external_repository: ${{ matrix.repo }}
    publish_branch: gh-pages
    publish_dir: packages/${{ matrix.package }}/docs/_build
```

**Why:** Use proper GitHub Action instead of hacky bash script!

### 5. grep/sed Version Parsing in Docs Job
**Before:**
```bash
V=$(grep '^version = ' packages/${{ matrix.package }}/pyproject.toml | head -1 | sed 's/version = "\([^"]*\)"/\1/')
```

**After:**
```bash
V=$(python -c "import tomllib; print(tomllib.load(open('packages/${{ matrix.package }}/pyproject.toml', 'rb'))['project']['version'])")
```

**Why:** Use Python's standard library instead of fragile regex parsing!

## Changes Made

### Release Job (.github/workflows/ci.yml)
1. ✅ Simplified version checking using PSR's `--noop version --print`
2. ✅ Removed `--no-vcs-release` flag - let PSR handle git operations
3. ✅ Added `softprops/action-gh-release` for GitHub releases
4. ✅ Kept `pypa/gh-action-pypi-publish` for PyPI (PSR only does VCS releases)
5. ✅ **Replaced custom sync script with `BetaHuhn/repo-file-sync-action`**
6. ✅ Created sync config files in `.github/sync/` for each package

### Docs Job (.github/workflows/ci.yml)
1. ✅ Replaced `grep`/`sed` version parsing with Python `tomllib`
2. ✅ **Replaced custom gh-pages deployment script with `peaceiris/actions-gh-pages`**

### New Files Created
- `.github/sync/extended-data-types.yml` - Sync config for extended-data-types
- `.github/sync/lifecyclelogging.yml` - Sync config for lifecyclelogging
- `.github/sync/directed-inputs-class.yml` - Sync config for directed-inputs-class
- `.github/sync/python-terraform-bridge.yml` - Sync config for python-terraform-bridge
- `.github/sync/vendor-connectors.yml` - Sync config for vendor-connectors

## Versioning Scheme Clarification

**NOT CalVer!** The version format `202511.6.0` is **standard SemVer**:
- `202511` = MAJOR version (happens to be date-like, but it's just a number)
- `6` = MINOR version
- `0` = PATCH version

PSR handles this correctly with no special configuration needed. Version constraints:
- `fix` commits → PATCH bump (202511.6.0 → 202511.6.1)
- `feat` commits → MINOR bump (202511.6.0 → 202511.7.0)
- Breaking changes → MAJOR bump (202511.6.0 → 202512.0.0)

## Why This Approach is Correct

Following the [Medium article on monorepo releases](https://medium.com/@asaf.shakarzy/releasing-a-monorepo-using-uv-workspace-and-python-semantic-release):

1. **Use PSR for what it's designed for:**
   - Version detection based on conventional commits
   - Version bumping in pyproject.toml and __init__.py
   - Git commit, tag, and push operations

2. **Use official GitHub Actions wherever possible:**
   - `pypa/gh-action-pypi-publish` for PyPI uploads
   - `softprops/action-gh-release` for GitHub releases
   - `BetaHuhn/repo-file-sync-action` for syncing to public repos
   - `peaceiris/actions-gh-pages` for gh-pages deployment

3. **Use declarative configs instead of imperative scripts:**
   - Sync configs in `.github/sync/` instead of bash scripts
   - Action parameters instead of git commands

## Workflow Flow

```mermaid
graph TD
    A[Push to main] --> B[Tests pass]
    B --> C[PSR checks if release needed]
    C -->|No changes| D[Skip release]
    C -->|Changes detected| E[PSR bumps version, commits, tags, pushes]
    E --> F[Download pre-built packages]
    F --> G[Publish to PyPI]
    G --> H[Create GitHub Release]
    H --> I[Sync to public repos via repo-file-sync-action]
    I --> J[Build and deploy docs via actions-gh-pages]
```

## Expected Results

After merge to main with conventional commits:
1. ✅ PSR detects version bump needed
2. ✅ PSR bumps version in pyproject.toml and __init__.py
3. ✅ PSR creates commit with message like "chore(edt-release): release extended-data-types v202511.7.0 [skip ci]"
4. ✅ PSR creates git tag like "extended-data-types-v202511.7.0"
5. ✅ PSR pushes commit and tag to GitHub
6. ✅ Package is published to PyPI
7. ✅ GitHub release is created with artifacts
8. ✅ Code is synced to public repo (jbcom/extended-data-types) via repo-file-sync-action
9. ✅ Docs are built and deployed to gh-pages branch via peaceiris/actions-gh-pages

## Testing

This can only be fully tested by:
1. Merging this PR to main
2. Making a commit with conventional commit format (e.g., `feat(edt): add new feature`)
3. Pushing to main
4. Verifying the release workflow runs and packages appear on PyPI

## Files Changed
- `.github/workflows/ci.yml` - Release and docs jobs
- `.github/sync/*.yml` - Sync configs for each package (NEW)

