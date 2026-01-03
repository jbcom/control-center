# Sync File Versioning Policy

## Overview

All sync files use semantic versioning with YAML front matter. This ensures controlled, trackable distribution of configuration files across the ecosystem.

## Three Sync Types

### 1. Always-Sync (`sync-files/always-sync/`)

**Purpose**: Files that every repo MUST always have and stay current with.

**Characteristics**:
- Auto-updates via ecosystem sync
- Latest version always deployed
- Old versions preserved in **git history only**
- Examples: CI workflows, cursor rules, CONTRIBUTING.md

**Versioning**:
- Version stored in YAML front matter
- Bump version → create git tag → swap file
- Tag format: `sync-file/{filename}-v{version}`

**Release Process**:
```bash
# 1. Bump version
./scripts/version-sync-file bump sync-files/always-sync/global/CONTRIBUTING.md patch

# 2. Release (creates instructions for git tag)
./scripts/version-sync-file release-always sync-files/always-sync/global/CONTRIBUTING.md

# 3. Follow printed instructions to commit and tag
```

### 2. Initial-Only (`sync-files/initial-only/`)

**Purpose**: Files that repos MUST start with but never auto-update.

**Characteristics**:
- Synced once on first PR
- Repos modify locally after initial sync
- New versions available as patches
- Examples: LICENSE, base config templates, AGENTS.md

**Versioning**:
- Version stored in YAML front matter
- Each version explicitly stored in repo with suffix
- Format: `filename-v{version}.ext`

**Release Process**:
```bash
# 1. Bump version in base file
./scripts/version-sync-file bump sync-files/initial-only/global/AGENTS.md minor

# 2. Create versioned copy
./scripts/version-sync-file release-patch sync-files/initial-only/global/AGENTS.md

# 3. Creates: AGENTS-v1.1.0.md
# 4. Commit versioned file, update sync.yml
```

### 3. Patch-Sync (`sync-files/patch-sync/`)

**Purpose**: Optional files repos CAN choose to implement.

**Characteristics**:
- Opt-in via PR labels or sync config
- Multiple versions available simultaneously
- Repos pick which version to adopt
- Examples: Advanced CI templates, optional tooling configs

**Versioning**:
- Same as initial-only
- Explicit versioned files in repo
- Format: `filename-v{version}.ext`

**Release Process**:
```bash
# Same as initial-only
./scripts/version-sync-file bump sync-files/patch-sync/global/advanced-ci.yml major
./scripts/version-sync-file release-patch sync-files/patch-sync/global/advanced-ci.yml
```

## YAML Front Matter Format

All sync files include:

```yaml
---
version: 1.2.3
last_updated: 2026-01-03T12:00:00Z
sync_type: always|initial|patch
description: Brief description of file purpose (optional)
breaking_changes: Description if major version bump (optional)
---
```

## Version Management Script

### Installation

```bash
# Make executable
chmod +x scripts/version-sync-file
```

### Commands

```bash
# Initialize file with v1.0.0
./scripts/version-sync-file init <file>

# Bump version (major|minor|patch)
./scripts/version-sync-file bump <file> <type>

# Release always-sync (git tag approach)
./scripts/version-sync-file release-always <file>

# Release initial/patch-sync (versioned copy)
./scripts/version-sync-file release-patch <file>

# Show version history
./scripts/version-sync-file list <file>
```

### Examples

```bash
# Always-sync workflow file
./scripts/version-sync-file init sync-files/always-sync/global/.github/workflows/ai-reviewer.yml
./scripts/version-sync-file bump sync-files/always-sync/global/.github/workflows/ai-reviewer.yml patch
./scripts/version-sync-file release-always sync-files/always-sync/global/.github/workflows/ai-reviewer.yml

# Initial-only documentation
./scripts/version-sync-file init sync-files/initial-only/global/CLAUDE.md
./scripts/version-sync-file bump sync-files/initial-only/global/CLAUDE.md minor
./scripts/version-sync-file release-patch sync-files/initial-only/global/CLAUDE.md
# Creates: CLAUDE-v1.1.0.md

# Patch-sync optional feature
./scripts/version-sync-file init sync-files/patch-sync/global/experimental-feature.yml
./scripts/version-sync-file bump sync-files/patch-sync/global/experimental-feature.yml major
./scripts/version-sync-file release-patch sync-files/patch-sync/global/experimental-feature.yml
# Creates: experimental-feature-v2.0.0.yml
```

## Integration with repo-file-sync-action

### Always-Sync

In `.github/sync.yml`:
```yaml
group:
  - files:
      - source: sync-files/always-sync/global/
        dest: ./
    repos: |
      org/*
```

### Initial-Only

Mark PRs with `initial-only` label. Repos review and merge once.

```yaml
specific-repo:
  - source: sync-files/initial-only/global/
    dest: ./
    labels: [initial-only, manual-review]
```

### Patch-Sync

Reference specific versions in sync config:

```yaml
repos-that-want-feature-v2:
  - source: sync-files/patch-sync/global/feature-v2.0.0.yml
    dest: .github/workflows/feature.yml
    labels: [patch-sync, optional]
```

## Release Integration

File version releases integrate with control-center's release system:

1. Version bump triggers chore release
2. Git tags track always-sync versions
3. Versioned files track initial/patch versions
4. Release notes document file changes

## Best Practices

### When to Bump Versions

**Major (X.0.0)**:
- Breaking changes requiring manual intervention
- File structure changes
- Incompatible with previous version

**Minor (x.Y.0)**:
- New features/additions
- Backwards compatible changes
- New optional sections

**Patch (x.y.Z)**:
- Bug fixes
- Documentation updates
- Typo corrections

### Documentation

Always document changes in:
- Commit message
- Front matter `breaking_changes` field (if major)
- Release notes
- Sync config comments

### Testing

Before release:
1. Test in a sandbox repo
2. Verify version front matter correct
3. Check backwards compatibility
4. Review sync config updates

## Migration Guide

### Existing Files

```bash
# Initialize all existing files
find sync-files -type f \( -name "*.yml" -o -name "*.md" -o -name "*.js" \) | while read file; do
  ./scripts/version-sync-file init "$file"
done
```

### Creating Versioned Copies

For initial-only and patch-sync files, create v1.0.0 copies:

```bash
# Example
./scripts/version-sync-file release-patch sync-files/initial-only/global/AGENTS.md
# Creates: AGENTS-v1.0.0.md
```

## Troubleshooting

**Q: How do I downgrade a file?**
A: For always-sync, use git history. For initial/patch-sync, reference older versioned file in sync config.

**Q: Can repos use different versions?**
A: Yes for initial/patch-sync (reference specific version). No for always-sync (always latest).

**Q: How to handle breaking changes?**
A: Bump major version, document in `breaking_changes` field, notify via PR description.

**Q: What if front matter conflicts with file format?**
A: Use comments for non-YAML files:
- `<!-- version: 1.0.0 -->` for HTML/Markdown
- `# version: 1.0.0` for shell/Python
- `// version: 1.0.0` for JS/Go

## See Also

- `.github/sync.yml` - Sync configuration
- `docs/SYNC-ARCHITECTURE.md` - Sync architecture overview
- `docs/ECOSYSTEM.md` - Ecosystem management guide
