# No Symlinks Policy

## Policy Statement

**Symlinks must NEVER be used in this repository, especially in the `sync-files/` directory.**

This is a hard requirement enforced by automated checks. Pull requests containing symlinks will fail CI validation.

## Why No Symlinks?

### 1. GitHub Actions Checkout Issues

GitHub Actions `actions/checkout` does not preserve symlinks by default. When workflows check out code:
- Symlinks may be converted to regular files
- Symlinks may be broken entirely
- Behavior is inconsistent across runners

### 2. Sync Reliability

When syncing files to managed repositories:
- `rsync` behavior with symlinks is unpredictable
- Target repositories would receive broken symlinks
- File sync operations become non-deterministic

### 3. Cross-Platform Compatibility

- Windows handles symlinks differently than Unix systems
- Symlinks require special permissions on Windows
- Git's handling of symlinks varies by platform

### 4. Security Concerns

- Symlinks can be exploited for path traversal attacks
- Hard to audit what files are actually being deployed
- Increases attack surface for malicious commits

## What To Do Instead

### Problem: Need the same file in multiple locations

❌ **Wrong:**
```bash
cd sync-files/always-sync/python/.github/workflows/
ln -s ../../shared/ci.yml ci.yml
```

✅ **Correct:**
```bash
cd sync-files/always-sync/python/.github/workflows/
cp ../../shared/ci.yml ci.yml
```

### Problem: Want to maintain a single source of truth

Use one of these approaches:

1. **Template Generation**: Generate files from templates using scripts
2. **Build-Time Copy**: Copy files during build/deploy process
3. **Accept Duplication**: Small duplication cost vs. reliability benefits

### Problem: Already have symlinks

Run the cleanup script:

```bash
./scripts/cleanup-symlinks
```

This script will:
1. Find all symlinks in the repository
2. Replace each symlink with a copy of its target
3. Remove any broken symlinks

## Enforcement

### Automated Checks

1. **Pre-commit**: Local git hook (optional, recommended)
2. **CI Lint**: `lint-config.yml` workflow checks on every PR
3. **Sync Guard**: `sync.yml` checks before syncing files

### Manual Check

```bash
./scripts/check-symlinks
```

This script:
- Returns exit code 0 if no symlinks found
- Returns exit code 1 and lists symlinks if found
- Provides guidance on how to fix

## Best Practices

### When Adding New Files

1. **Always copy, never link**
   ```bash
   cp source.yml target.yml
   ```

2. **Use rsync with --copy-links**
   ```bash
   rsync -av --copy-links source/ dest/
   ```

3. **Verify no symlinks before committing**
   ```bash
   ./scripts/check-symlinks
   ```

### When Syncing Files

1. **Always use --copy-links flag**
   ```bash
   rsync -av --copy-links source/ dest/
   ```

2. **Use -L with cp**
   ```bash
   cp -L source dest
   ```

3. **Use -L with find**
   ```bash
   find -L . -type f
   ```

## Examples

### Correct: Copying Shared Workflow

```bash
# Copy workflow to all ecosystem directories
for ecosystem in python nodejs go terraform; do
  cp sync-files/always-sync/global/ci.yml \
     sync-files/$ecosystem/.github/workflows/ci.yml
done
```

### Correct: Maintaining Duplicate Files

```bash
# Script to update all copies of a file
#!/bin/bash
SOURCE="sync-files/always-sync/global/pr-template.md"

for target in sync-files/*/.github/PULL_REQUEST_TEMPLATE.md; do
  cp "$SOURCE" "$target"
  echo "Updated: $target"
done
```

### Incorrect: Using Symlinks

```bash
# ❌ DON'T DO THIS
ln -s ../../shared/workflow.yml \
     sync-files/always-sync/python/.github/workflows/workflow.yml
```

## Troubleshooting

### CI Check Fails: "Symlinks detected"

1. Run `./scripts/check-symlinks` to see which symlinks exist
2. Run `./scripts/cleanup-symlinks` to automatically fix them
3. Review and commit the changes
4. Push to trigger CI again

### Symlink Was Created Accidentally

```bash
# Find it
./scripts/check-symlinks

# Remove it
rm path/to/symlink

# Replace with actual file
cp path/to/target path/to/symlink

# Commit
git add path/to/symlink
git commit -m "fix: replace symlink with actual file"
```

### Need to Maintain Many Copies

Consider:
1. Creating a script that copies files in bulk
2. Running the script before committing
3. Documenting the copy process in comments

Example:
```bash
#!/bin/bash
# sync-shared-workflows.sh
# Copies shared workflows to all ecosystems

SHARED_DIR="sync-files/always-sync/global"
ECOSYSTEMS=(python nodejs go terraform)

for workflow in "$SHARED_DIR"/*.yml; do
  filename=$(basename "$workflow")
  for ecosystem in "${ECOSYSTEMS[@]}"; do
    target="sync-files/$ecosystem/.github/workflows/$filename"
    cp "$workflow" "$target"
    echo "Copied $filename to $ecosystem"
  done
done
```

## Related Documentation

- [Workflow Sync Process](WORKFLOW-SYNC.md)
- [Repository Configuration](../repo-config.json)
- [Sync Scripts](../scripts/)

## Questions?

If you have questions about this policy or need help fixing symlinks, please:
1. Check the troubleshooting section above
2. Run `./scripts/check-symlinks` for diagnostics
3. Open an issue if you need clarification
