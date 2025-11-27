# Automated Dependency Management Configuration

**Date**: 2025-11-27
**Status**: Complete

## Overview

This repository now has comprehensive automated dependency management configured across three complementary tools:

1. **hadolint** - Pre-commit Dockerfile linting
2. **Dependabot** - GitHub-native dependency updates
3. **Renovate** - Advanced dependency management with custom rules

## Pre-commit Hooks (.pre-commit-config.yaml)

### Dockerfile Validation
- **Tool**: hadolint v2.12.0
- **Purpose**: Lint Dockerfile for best practices and security issues
- **When**: On every commit touching Dockerfile
- **Ignored Rules**:
  - `DL3008`: Pin versions in apt-get install (we use --no-install-recommends)
  - `DL3009`: Delete apt cache (we use rm -rf /var/lib/apt/lists/*)

### Usage
```bash
# Run manually
pre-commit run hadolint --all-files

# Run all hooks
pre-commit run --all-files

# Install hooks
pre-commit install
```

## Dependabot (.github/dependabot.yml)

### Configuration

| Ecosystem | Directory | Schedule | PR Limit |
|-----------|-----------|----------|----------|
| github-actions | / | Daily | 10 |
| pip | / | Daily | 10 |
| docker | /.cursor | Weekly | 5 |

### What It Updates
- **GitHub Actions**: All workflow dependencies
- **Python packages**: Requirements files, pyproject.toml
- **Docker**: Base image in `.cursor/Dockerfile`

### Labels Applied
- `dependencies` (all updates)
- `docker` (Docker-specific updates)

### Why Weekly for Docker?
- Docker base images change frequently
- Weekly schedule prevents PR spam
- Still provides timely security updates

## Renovate (renovate.json)

### Configuration Overview
- **Schedule**: Before 5am on Monday (weekly)
- **Timezone**: America/New_York
- **Auto-merge**: Disabled (manual review required)

### What It Updates

#### 1. Docker Base Images
- **Source**: `.cursor/Dockerfile`
- **Image**: `jdxcode/mise:latest`
- **Schedule**: Weekly
- **Labels**: `dependencies`, `docker`

#### 2. Go Tools in Dockerfile
- **Pattern**: `go install github.com/user/tool@vX.Y.Z`
- **Tools Managed**:
  - `github.com/mikefarah/yq/v4`
  - `github.com/jesseduffield/lazygit`
  - `github.com/charmbracelet/glow`
- **Datasource**: Go modules
- **Versioning**: Semver

#### 3. mise Tool Versions (.mise.toml)

##### just (Task Runner)
- **Current**: 1.43.1
- **Datasource**: github-releases (casey/just)
- **Pattern**: `just = "X.Y.Z"`

##### Python Runtime
- **Current**: 3.13
- **Datasource**: github-releases (python/cpython)
- **Pattern**: `python = "X.Y"`

##### Node.js Runtime
- **Current**: 24
- **Datasource**: github-releases (nodejs/node)
- **Pattern**: `node = "XX"`
- **Versioning**: node (major versions)

##### Go Runtime
- **Current**: 1.23.4
- **Datasource**: github-releases (golang/go)
- **Pattern**: `go = "X.Y.Z"`
- **Version Extraction**: Strips "go" prefix

##### Rust Runtime
- **Current**: stable
- **Management**: Not version-pinned (uses stable channel)

### Custom Regex Managers

Renovate uses custom regex patterns to detect dependencies in non-standard formats:

1. **Go tools in Dockerfile**
   ```regex
   go install (?<depName>github\.com/[^@]+)@(?<currentValue>v?[0-9]+\.[0-9]+\.[0-9]+)
   ```

2. **just in .mise.toml**
   ```regex
   just\s*=\s*"(?<currentValue>[^"]+)"
   ```

3. **Language runtimes in .mise.toml**
   ```regex
   python\s*=\s*"(?<currentValue>[^"]+)"
   node\s*=\s*"(?<currentValue>[^"]+)"
   go\s*=\s*"(?<currentValue>[^"]+)"
   ```

### Why Renovate AND Dependabot?

**Dependabot Strengths:**
- Native GitHub integration
- Simple configuration
- Reliable for standard ecosystems
- Great for GitHub Actions and pip

**Renovate Strengths:**
- Advanced pattern matching (regex managers)
- Multi-file dependency tracking
- Custom datasources
- Better for complex scenarios

**Together:**
- Comprehensive coverage
- Redundancy for critical dependencies
- Best tool for each job

## Dependency Update Workflow

### Weekly Cycle (Monday 5am ET)
1. Renovate scans for updates
2. Creates PRs for:
   - Docker base image changes
   - Go tool version updates
   - mise tool version updates
   - Language runtime updates

### Daily Cycle
1. Dependabot scans for updates
2. Creates PRs for:
   - GitHub Actions updates
   - Python package updates

### Manual Review Required
All PRs require manual approval before merge:
1. Review changelog/release notes
2. Check for breaking changes
3. Validate CI passes
4. Merge when ready

## Maintenance

### Updating hadolint Rules
Edit `.pre-commit-config.yaml`:
```yaml
- id: hadolint
  args: [--ignore, DL3008, --ignore, DL3009, --ignore, NEW_RULE]
```

### Updating Dependabot Schedule
Edit `.github/dependabot.yml`:
```yaml
- package-ecosystem: "docker"
  schedule:
    interval: "monthly"  # Change from weekly
```

### Updating Renovate Configuration
Edit `renovate.json`:
```json
{
  "schedule": ["before 5am on Monday"],  // Modify schedule
  "automerge": true,  // Enable auto-merge (not recommended)
  "packageRules": [
    // Add custom rules
  ]
}
```

### Testing Renovate Configuration
```bash
# Install Renovate CLI (optional)
npm install -g renovate

# Validate configuration
renovate-config-validator

# Dry run (if you have access)
LOG_LEVEL=debug renovate --dry-run
```

## Security Considerations

### Automated Updates
- ✅ Timely security patches
- ✅ Reduced manual maintenance
- ⚠️ Risk of breaking changes
- ⚠️ Requires active PR review

### Mitigation Strategies
1. **Manual review required** (no auto-merge)
2. **CI validation** on all PRs
3. **Staged rollout** (weekly for Docker, daily for others)
4. **Version pinning** prevents surprise updates
5. **hadolint** catches security issues in Dockerfile

## Monitoring

### Check Dependency Update Status
```bash
# View open Dependabot PRs
gh pr list --label dependencies

# View all open PRs
gh pr list

# Check Renovate PRs
gh pr list --author renovate[bot]
```

### Review Logs
- **Dependabot**: GitHub UI > Insights > Dependency graph > Dependabot
- **Renovate**: Check PR descriptions for detailed logs
- **Pre-commit**: Local output when hooks run

## Troubleshooting

### hadolint Fails on Valid Dockerfile
1. Check which rule is failing
2. Add to ignore list if appropriate
3. Or fix the issue if it's a real problem

### Dependabot PR Conflicts
1. Rebase PR on latest main
2. Or close and wait for next run

### Renovate Not Creating PRs
1. Check renovate.json is valid JSON
2. Verify regex patterns match actual files
3. Check Renovate bot has repo access

## Resources

- **hadolint**: https://github.com/hadolint/hadolint
- **Dependabot**: https://docs.github.com/en/code-security/dependabot
- **Renovate**: https://docs.renovatebot.com/
- **mise**: https://mise.jdx.dev/

---

**Last Updated**: 2025-11-27
**Maintained By**: jbcom-control-center
**Status**: Production-ready
