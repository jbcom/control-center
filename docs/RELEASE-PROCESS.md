# Release Process

This document describes the unified release process for control-center, covering Go binary releases, GitHub Actions marketplace publishing, Docker images, and enterprise cascade synchronization.

## Overview

Control Center uses a unified, automated release process that:

1. **Builds Go Binaries** (OSS) - Cross-platform binaries via GoReleaser
2. **Publishes Docker Images** - Multi-arch images to Docker Hub via automatic builds
3. **Tags GitHub Actions** - Marketplace-ready actions with floating version tags
4. **Triggers Ecosystem Sync** - Propagates updates to all managed organizations

**Distribution Model**: 
- **CLI Users**: Download Go binaries from GitHub Releases or use `go install`
- **GitHub Actions**: Use Docker-based actions that pull from Docker Hub
- **Docker Users**: Pull images directly from Docker Hub

**Key Change**: Control Center no longer builds or uploads Docker images in GitHub Actions. Instead, Docker Hub automatically builds images when tags are pushed, and GitHub Actions reference these pre-built images.

## Architecture

```
git tag vX.Y.Z (manual or via release-please)
         │
         ├─────────────┬─────────────┬────────────────┬──────────────────┐
         │             │             │                │                  │
         ▼             ▼             ▼                ▼                  ▼
   GoReleaser      Docker        Action Tags    Ecosystem Sync     Go Proxy
   (binaries)   (Docker Hub)    (marketplace)    (cascade)        (automatic)
         │         automatic          │                │
         ▼           build            ▼                ▼
    GitHub           │            v1, v1.1         All managed
    Release          ▼              tags            organizations
              Docker Hub image
              (60s wait time)
```

## Release Workflow

### Automated Process (via release-please)

**Release Please** automatically creates release PRs based on conventional commits:

1. Commits to `main` following [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   feat: add new feature      # Bumps minor version
   fix: resolve bug          # Bumps patch version
   feat!: breaking change    # Bumps major version
   ```

2. Release Please creates/updates a PR with:
   - Updated `CHANGELOG.md`
   - Version bump in `.release-please-manifest.json`
   - Version updates in all `action.yml` files (via `x-release-please-version` marker)

3. When you merge the release PR, Release Please:
   - Creates a GitHub Release
   - Tags the commit with `vX.Y.Z`
   - Triggers the release workflow

### Manual Process

If you need to create a release manually:

```bash
# 1. Ensure all changes are committed and pushed
git checkout main
git pull origin main

# 2. Create and push a version tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

This triggers the release workflow automatically.

## What Gets Released

### 1. Go Binary (via GoReleaser)

**Output**: Cross-platform binaries in GitHub Release

Platforms:
- `linux/amd64`
- `linux/arm64`
- `darwin/amd64` (macOS Intel)
- `darwin/arm64` (macOS Apple Silicon)
- `windows/amd64`

**Installation**:
```bash
# Via Go install (automatically uses Go proxy)
go install github.com/jbcom/control-center/cmd/control-center@latest
go install github.com/jbcom/control-center/cmd/control-center@v1.2.0

# Via binary download from GitHub Releases
curl -LO https://github.com/jbcom/control-center/releases/download/v1.2.0/control-center_1.2.0_linux_amd64.tar.gz
tar -xzf control-center_1.2.0_linux_amd64.tar.gz
sudo mv control-center /usr/local/bin/
```

**Note**: The Go binary is the traditional distribution method for CLI tools. For GitHub Actions workflows, use the Docker-based actions instead (see section 3).

### 2. Docker Image (Docker Hub)

**Registry**: `jbcom/control-center` on Docker Hub

**Automatic Builds**: Docker Hub is configured to automatically build images when:
- Tags matching `/^v([0-9.]+)$/` are pushed → Tagged as version number (e.g., `1.2.0`)
- Commits are pushed to `main` branch → Tagged as `latest`

**Tags**:
- `vX.Y.Z` or `X.Y.Z` - Specific version (e.g., `v1.2.0` or `1.2.0`)
- `latest` - Latest stable release from `main` branch

**Platforms** (via Docker Hub automatic builds):
- `linux/amd64`
- `linux/arm64`

**Security**: Docker Scout is integrated to scan images for vulnerabilities after each build.

**Usage**:
```bash
# Run specific version
docker run jbcom/control-center:1.2.0 version

# Run latest
docker run jbcom/control-center:latest reviewer --repo owner/repo --pr 123
```

**Required Configuration**:
- Docker Hub automatic builds configured for repository
- GitHub secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
- Docker Scout enabled in Docker Hub repository settings

### 3. GitHub Actions (Marketplace)

**Location**: GitHub Actions Marketplace

**Action Paths**:
- `jbcom/control-center@v1` - Latest v1.x.x (floating)
- `jbcom/control-center@v1.2` - Latest v1.2.x (floating)
- `jbcom/control-center@v1.2.0` - Exact version
- `jbcom/control-center/actions/reviewer@v1` - Specific command action

**Docker Image Reference**: All actions use `docker://jbcom/control-center:latest` from Docker Hub. The actions themselves are versioned via git tags, but they always pull the latest Docker image. This ensures workflows get the most up-to-date binary without having to rebuild or upload artifacts.

**Version Tags**:
- `v1` - Floating major version tag (updated on each v1.x.x release)
- `v1.2` - Floating minor version tag (updated on each v1.2.x release)
- `v1.2.0` - Exact version tag (immutable)

**Usage**:
```yaml
# Using main action with command input (recommended for flexibility)
- uses: jbcom/control-center@v1
  with:
    command: reviewer
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}

# Using specific command action (simpler interface)
- uses: jbcom/control-center/actions/reviewer@v1
  with:
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}
```

### 4. Ecosystem Sync

After successful release, the workflow triggers `ecosystem-sync.yml` to propagate the new version across all managed organizations:

**Organizations**:
- `arcade-cabinet`
- `agentic-dev-library`
- `extended-data-library`
- `strata-game-library`

**What Gets Updated**:
- Control center Go binary in workflows
- Docker image references in workflows
- Action version references in repository workflows
- Cursor rules and AI agent configurations

**See**: [`docs/SYNC-ARCHITECTURE.md`](./SYNC-ARCHITECTURE.md) for cascade details.

## Version Management

### Semantic Versioning

Control Center follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.Y.0): New functionality, backwards compatible
- **PATCH** version (0.0.Z): Bug fixes, backwards compatible

### Version Tracking

Version information is embedded in:

1. **Git Tag**: `vX.Y.Z` (source of truth)
2. **Go Binary**: `control-center version` command
3. **Docker Image**: Labels and VERSION env var
4. **Action Files**: Docker image tag (managed by release-please)
5. **CHANGELOG.md**: Release notes

### Release Please Configuration

Managed by these files:
- `.release-please-manifest.json` - Current version
- `release-please-config.json` - Changelog sections, extra files to update

## Troubleshooting

### Release Workflow Failed

**Check**:
1. GoReleaser configuration (`.goreleaser.yaml`)
2. Dockerfile builds successfully
3. GitHub token has `contents: write` and `packages: write` permissions

**Common Issues**:
- Go build failures → Check `go.mod` dependencies
- Docker build failures → Test locally with `docker build .`
- Tag already exists → Delete and re-push: `git tag -d v1.2.0 && git push origin :refs/tags/v1.2.0`

### Docker Image Not Published

**Check**:
1. Docker Hub automatic build succeeded
2. Docker Hub credentials (secrets.DOCKERHUB_USERNAME, secrets.DOCKERHUB_TOKEN) are valid
3. Docker Hub repository has automatic builds enabled
4. Wait up to 60 seconds for Docker Hub to complete the build after tag push

**Debug**:
```bash
# Test Docker build locally
docker buildx build --platform linux/amd64,linux/arm64 -t test:local .

# Check Docker Hub build status
# Visit: https://hub.docker.com/r/jbcom/control-center/builds
```

**Docker Hub Automatic Build Configuration**:
- Source Type: Tag
- Source: `/^v([0-9.]+)$/`
- Docker Tag: Version number (without 'v' prefix)
- Source Type: Branch
- Source: `main`
- Docker Tag: `latest`

### Actions Not Updating

**Check**:
1. Floating tags (`v1`, `v1.2`) were force-pushed
2. Action marketplace sees new version (may take 5-10 minutes)
3. Downstream workflows are using floating tags (not exact versions)

**Verify**:
```bash
# Check tags in repo
git ls-remote --tags origin

# Verify Docker image tags
docker pull jbcom/control-center:latest
docker inspect jbcom/control-center:latest | jq '.[0].Config.Labels'
```

### Ecosystem Sync Not Triggered

**Check**:
1. `CI_GITHUB_TOKEN` secret is configured
2. Token has `workflow: write` permission
3. Workflow trigger succeeded in Actions UI

**Manual Trigger**:
```bash
gh workflow run ecosystem-sync.yml --repo jbcom/control-center --ref main
```

## Best Practices

### Before Releasing

1. **Review open PRs** - Merge or defer to next release
2. **Run tests locally** - `make test lint`
3. **Check CHANGELOG** - Review release-please PR for accuracy
4. **Verify dependencies** - Update Go modules if needed (`go get -u ./...`)

### After Releasing

1. **Monitor workflow** - Watch GitHub Actions for completion
2. **Verify artifacts** - Check GitHub Release, GHCR, marketplace
3. **Test installation** - Try `go install` with new version
4. **Check ecosystem sync** - Verify managed orgs received updates
5. **Update documentation** - If new features or breaking changes

### Hotfix Process

For urgent fixes to released versions:

1. Create hotfix branch from release tag:
   ```bash
   git checkout -b hotfix/v1.2.1 v1.2.0
   ```

2. Apply fix and commit:
   ```bash
   git commit -m "fix: critical security issue"
   ```

3. Tag and push:
   ```bash
   git tag v1.2.1
   git push origin v1.2.1
   ```

4. Merge back to main:
   ```bash
   git checkout main
   git merge hotfix/v1.2.1
   git push origin main
   ```

## Security Considerations

### Token Permissions

The release workflow requires:
- `contents: write` - Create releases and tags
- `packages: write` - Reserved for future use (not currently used)
- `actions: write` - Update action tags

Docker Hub credentials are required as secrets:
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token (not password)

**Never** expose tokens in:
- Logs or workflow outputs
- Docker image layers
- Binary artifacts
- Public repositories (use secrets)

### Supply Chain Security

- **Reproducible builds** - GoReleaser provides checksums
- **Multi-stage Dockerfile** - Minimal runtime image (Alpine)
- **No secrets in images** - All secrets via env vars at runtime
- **Signed commits** - Enable GPG signing for releases
- **SBOM generation** - Consider adding SBOM to releases

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Release Please](https://github.com/googleapis/release-please)
- [GoReleaser](https://goreleaser.com/)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Sync Architecture](./SYNC-ARCHITECTURE.md)
- [Ecosystem Documentation](./ECOSYSTEM.md)
