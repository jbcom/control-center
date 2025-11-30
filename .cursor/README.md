# Cursor Background Agent Environment

This directory contains the Docker-based development environment configuration for Cursor's background agent operation.

## Files

### `Dockerfile`
The main environment definition with all tools and languages needed for autonomous agent operation.

**Key features:**
- **mise-based tool management** for unified language runtime management
- Python 3.13 + Node.js 24 + Rust stable + Go 1.23.4
- Full Python dev stack (pytest, mypy, ruff, etc.)
- Agent frameworks (ConPort, CrewAI)
- Modern CLI tools (ripgrep, fd, bat, etc.)
- All language versions defined in `.mise.toml`
- Versioned, reproducible builds

**Build:** See "Building the Environment" below.

### `environment.json`
Cursor-specific configuration that tells Cursor to use the Dockerfile in this repo.

### `ENVIRONMENT_ANALYSIS.md`
Comprehensive analysis of tool requirements, security considerations, and workflow mappings.

**Read this to understand:**
- Why each tool was chosen
- Security improvements made
- How tools map to workflows
- Maintenance strategy

### `EVALUATION_SUMMARY.md`
Executive summary of improvements made to the Dockerfile.

**Quick overview of:**
- All PR feedback addressed
- Complete tool matrix
- Testing recommendations
- Image size estimates

### `TOOLS_REFERENCE.md`
Quick reference guide for all available tools in the environment.

**Use this when:**
- You need to know what command to run
- You want to find the modern alternative to a classic tool
- You need examples of common workflows

## Building the Environment

### Prerequisites
- Docker installed and running
- At least 5GB free disk space
- Internet connection (for downloading tools)

### Build Command
```bash
cd /workspace
docker build -f .cursor/Dockerfile -t jbcom-control-center:dev .
```

### Build Time
First build: ~15-30 minutes (downloads and compiles tools)
Subsequent builds: ~5-10 minutes (uses layer cache)

### Verify Build
```bash
docker run --rm jbcom-control-center:dev python --version
docker run --rm jbcom-control-center:dev rg --version
docker run --rm jbcom-control-center:dev process-compose version
```

## Using with Cursor

### Automatic Setup
When you open this workspace in Cursor with the `.cursor/environment.json` file present, Cursor will:
1. Detect the Dockerfile configuration
2. Build the image automatically (if not already built)
3. Start the container
4. Mount the workspace at `/workspace`
5. Copy files into the container (NOT done in Dockerfile)

### Manual Setup (if needed)
If Cursor doesn't auto-detect:
1. Open Cursor settings
2. Go to "Remote" section
3. Select "Use Dockerfile in repository"
4. Restart Cursor

## Tool Categories

### Python Development
- **Package managers**: uv, pip, poetry
- **Testing**: pytest (with plugins)
- **Type checking**: mypy, pyright
- **Linting**: ruff
- **Versioning**: python-semantic-release (SemVer)

### Node.js Development
- **Package manager**: pnpm 9.15.0
- **Browser automation**: Playwright 1.49.0

### Agent Frameworks
- **Memory**: ConPort (context-portal-mcp)
- **Multi-agent**: CrewAI + crewai-tools
- **Instructions**: Ruler

### Shell Utilities
- **Search**: ripgrep (rg), fd-find
- **Data**: jq, yq, sqlite3
- **Display**: bat, exa, glow
- **Git**: git, git-lfs, gh, delta, lazygit
- **Process**: process-compose, htop

### Additional Runtimes
- **Rust**: stable (via rustup)
- **Go**: 1.23.4

## Version Pinning Strategy

### Language Runtimes (via mise + .mise.toml)
- Python: 3.13
- Node.js: 24
- Rust: stable
- Go: 1.23.4
- just: latest

### Strictly Pinned (for reproducibility)
- pnpm: 9.15.0 (must match package.json)
- Playwright: 1.49.0
- process-compose: v1.27.0

### Loosely Pinned (major version)
- Python packages: `>=X.Y.0` (pip resolves)
- Cargo tools: `--locked` (uses Cargo.lock)

### No Pin (always latest)
- System packages: Latest from apt repos
- mise base image: jdxcode/mise:latest

## Security Considerations

### What We Did Right
✅ **mise-based tool management**: Reproducible, version-controlled language runtimes
✅ **No manual downloads**: Languages installed via mise from official sources
✅ **HTTPS only**: All downloads use HTTPS
✅ **Reproducible**: Pinned versions in `.mise.toml` for language runtimes
✅ **Verified**: Final verification step checks all tools work
✅ **Minimal attack surface**: Only install what's needed

### What to Watch
⚠️ **Base image trust**: We trust `jdxcode/mise:latest` (official mise Docker image)
⚠️ **mise downloads**: mise installs tools from official sources (Python, Node.js, Rust, Go)
⚠️ **System packages**: Installed from Debian apt repositories

### Regular Updates
- **Monthly**: Check for `.mise.toml` version updates and base image updates
- **Quarterly**: Review and update tool versions
- **On CVE**: Update affected tools immediately

## Troubleshooting

### Build Fails on Rust Tools
If `cargo install` fails (common on low-memory systems):
- Reduce parallel jobs: `cargo install --jobs 1 ...`
- Comment out optional tools (exa, bottom, ast-grep)
- Or use pre-built binaries instead

### Build Fails on Python Packages
If pip install fails:
- Check internet connection
- Try with `--no-cache-dir` (already default)
- Check package availability: `pip index versions package-name`

### Image Too Large
Current image: ~2.5GB
- Remove Rust tools: Save ~400MB
- Remove Go tools: Save ~200MB
- Remove Playwright: Save ~500MB
- Keep only what you need!

### Cursor Not Using Dockerfile
1. Check `.cursor/environment.json` exists
2. Verify Docker is running: `docker ps`
3. Restart Cursor
4. Check Cursor logs for errors

## Maintenance

### Update Base Image
The environment now uses mise for language runtime management:
```toml
# Edit .mise.toml to update language versions
[tools]
python = "3.13"
node = "24"
rust = "stable"
go = "1.23.4"
just = "latest"
```

For the base Docker image:
```dockerfile
FROM jdxcode/mise:latest
# mise provides unified tool management
# See https://mise.jdx.dev/ for documentation
```

### Update Pinned Versions
Edit `.mise.toml` for language versions:
```toml
[tools]
python = "3.13"      # Update this
node = "24"          # Update this
go = "1.23.4"        # Update this
rust = "stable"      # Or pin to specific version
```

Edit Dockerfile environment variables for other tools:
```dockerfile
ENV PC_VERSION="v1.27.0"         # Update this
ENV PLAYWRIGHT_VERSION="1.49.0"  # Update this
```

### Update Python Packages
```dockerfile
RUN pip install --no-cache-dir \
    pytest>=8.0.0 \  # Update minimum version
    # ...
```

### Rebuild After Changes
```bash
docker build --no-cache -f .cursor/Dockerfile -t jbcom-control-center:dev .
```

## Automated Dependency Management

This repository uses multiple tools to keep dependencies up to date:

### Dependabot
Configured in `.github/dependabot.yml` to automatically:
- Update GitHub Actions (daily)
- Update Python packages (daily)
- Update Docker base images (weekly)

### Renovate
Configured in `renovate.json` to automatically:
- Update Docker base image (`jdxcode/mise:latest`)
- Update Go tool versions in Dockerfile
- Update mise tool versions in `.mise.toml`
- Update language runtime versions

### Pre-commit Hooks
Configured in `.pre-commit-config.yaml` to validate:
- **hadolint**: Dockerfile linting and best practices
- **yamllint**: YAML syntax and style
- **ruff**: Python linting and formatting
- **mypy**: Python type checking
- **actionlint**: GitHub Actions workflow validation
- **markdownlint**: Markdown formatting

Run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

## Integration with Agent Rules

This environment is designed to work with the agent rules in `.cursor/rules/`:

### `00-loader.mdc`
- ✅ CrewAI workflows supported
- ✅ uv package manager available
- ✅ Documentation-driven development (all tools present)

### `10-background-agent-conport.mdc`
- ✅ ConPort (context-portal-mcp) installed
- ✅ sqlite3 for ConPort database
- ✅ process-compose for orchestration
- ✅ ripgrep for fast search (REQUIRED by rules)

### Root `.cursorrules`
- ✅ Python tooling (pytest, mypy, ruff)
- ✅ GitHub CLI (gh)
- ✅ Git operations supported
- ✅ python-semantic-release CLI

## Advanced Usage

### Custom Tools
Add your own tools by editing Dockerfile:
```dockerfile
RUN mise x -- cargo install your-rust-tool
RUN mise x -- go install github.com/user/tool@latest
RUN mise x -- pip install your-python-package
```

Or add tools to `.mise.toml`:
```toml
[tools]
# Add tools available as mise plugins
your-tool = "latest"
```

### Environment Variables
Add custom env vars in `.mise.toml`:
```toml
[env]
YOUR_VAR = "value"
```

Or in Dockerfile:
```dockerfile
ENV YOUR_VAR=value
```

### Multi-Stage Builds
For production, consider multi-stage:
```dockerfile
FROM base AS builder
RUN ... build steps ...

FROM base AS runtime
COPY --from=builder /usr/local/bin/tool /usr/local/bin/
```

### Dockerfile Best Practices
- Group related commands in single RUN
- Clean up after apt installs
- Use `--no-cache-dir` for pip
- Remove build artifacts: `rm -rf $CARGO_HOME/registry`

## Resources

- **mise documentation**: https://mise.jdx.dev/
- **Dockerfile best practices**: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- **Python in Docker**: https://pythonspeed.com/docker/
- **ConPort**: https://github.com/cyanheads/context-portal-mcp
- **CrewAI**: https://github.com/joaomdmoura/crewAI
- **Ruler**: https://github.com/intellectronica/ruler

## Questions?

- **Agent rules**: See `.cursor/rules/` and `.cursorrules`
- **Tool usage**: See `TOOLS_REFERENCE.md`
- **Analysis**: See `ENVIRONMENT_ANALYSIS.md`
- **Summary**: See `EVALUATION_SUMMARY.md`

---

**Last Updated**: 2025-11-27
**Environment Version**: 1.0.0
**Maintained By**: jbcom-control-center
