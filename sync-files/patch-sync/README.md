# Patch Sync Files

This directory contains **optional** files that repos can choose to implement.

## Purpose

Patch-sync files are:
- **Optional**: Repos opt-in via sync config or PR labels
- **Versioned**: Multiple versions available simultaneously
- **Flexible**: Repos pick which version to adopt

## Usage

### For Repository Maintainers

To adopt a patch-sync file:

1. **Find available versions**:
   ```bash
   ls sync-files/patch-sync/global/
   ```

2. **Add to your sync config** (in control-center):
   ```yaml
   your-org/your-repo:
     - source: sync-files/patch-sync/global/feature-v2.0.0.yml
       dest: .github/workflows/feature.yml
       labels: [patch-sync, optional]
   ```

3. **Review PR** when sync creates it
4. **Merge** if you want the feature

### For Control Center Maintainers

To release a new patch-sync file:

1. **Create file** in `sync-files/patch-sync/global/` (or language dir)

2. **Initialize version**:
   ```bash
   ./scripts/version-sync-file init sync-files/patch-sync/global/new-feature.yml
   ```

3. **Release versioned copy**:
   ```bash
   ./scripts/version-sync-file release-patch sync-files/patch-sync/global/new-feature.yml
   ```

4. **Commit**:
   ```bash
   git add sync-files/patch-sync/global/new-feature-v1.0.0.yml
   git commit -m "chore(sync): release new-feature v1.0.0 (patch-sync)"
   ```

5. **Update docs**: Document in CHANGELOG and sync config comments

## File Structure

```
patch-sync/
  ├── global/              # Universal optional features
  │   ├── feature-v1.0.0.yml
  │   ├── feature-v2.0.0.yml    # Multiple versions coexist
  │   └── advanced-ci-v1.0.0.yml
  ├── python/              # Python-specific optional
  ├── nodejs/              # Node.js-specific optional
  ├── go/                  # Go-specific optional
  ├── terraform/           # Terraform-specific optional
  └── rust/                # Rust-specific optional
```

## Versioning

- All files use semantic versioning (vX.Y.Z)
- Version in YAML front matter and filename
- See `docs/SYNC-FILE-VERSIONING.md` for details

## Examples

### Advanced CI Pipeline (Optional)

**File**: `advanced-ci-v1.0.0.yml`

Provides advanced CI features like:
- Multi-stage builds
- Parallel testing
- Advanced caching

Repos can adopt if they need these features.

### Experimental Features

**File**: `experimental-feature-v0.1.0.yml`

Beta features for early adopters:
- Marked as v0.x.x (pre-release)
- May have breaking changes
- Feedback welcome

### Language-Specific Tools

**File**: `python/advanced-testing-v1.0.0.yml`

Optional Python testing enhancements:
- Mutation testing
- Property-based testing
- Performance benchmarks

## See Also

- `docs/SYNC-FILE-VERSIONING.md` - Complete versioning guide
- `.github/sync.yml` - Sync configuration
- `sync-files/always-sync/` - Required files
- `sync-files/initial-only/` - Starter files
