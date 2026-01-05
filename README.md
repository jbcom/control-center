# Control Center

Enterprise AI orchestration for the jbcom ecosystem.

[![Go CI](https://github.com/jbcom/control-center/actions/workflows/go.yml/badge.svg)](https://github.com/jbcom/control-center/actions/workflows/go.yml)
[![Go Reference](https://pkg.go.dev/badge/github.com/jbcom/control-center.svg)](https://pkg.go.dev/github.com/jbcom/control-center)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Control Center is a unified CLI tool for managing AI agents, repository synchronization, and enterprise workflows across the jbcom ecosystem. It provides native integrations with:

- **Ollama** (GLM 4.6 Cloud) - Fast code review and analysis
- **Google Jules** - Multi-file refactoring with auto-PR creation
- **Cursor Cloud Agent** - Long-running autonomous tasks

## Installation

### Go Install

```bash
go install github.com/jbcom/control-center/cmd/control-center@latest
```

### Docker

```bash
docker pull jbcom/control-center:latest
```

### Binary

Download from [Releases](https://github.com/jbcom/control-center/releases).

## Commands

### Gardener

Enterprise-level cascade orchestrator. Discovers organizations, auto-heals control centers, processes backlog, and cascades instructions.

```bash
# Run for all organizations
control-center gardener --target all

# Run for specific organization
control-center gardener --target extended-data-library

# Dry run
control-center gardener --target all --dry-run
```

### Curator

Nightly triage of issues and PRs. Analyzes and routes to appropriate AI agents.

```bash
# Curate a specific repository
control-center curator --repo jbcom/control-center

# Dry run
control-center curator --repo jbcom/control-center --dry-run
```

### Reviewer

AI-powered code review using Ollama.

```bash
# Review a specific PR
control-center reviewer --repo jbcom/control-center --pr 123

# With debug output
control-center reviewer --repo jbcom/control-center --pr 123 --log-level debug
```

### Fixer

Automated CI failure resolution.

```bash
# Analyze and suggest fix for a PR
control-center fixer --repo jbcom/control-center --pr 123

# Analyze a specific workflow run
control-center fixer --repo jbcom/control-center --run-id 12345678
```

## GitHub Action

Control Center is distributed as a Docker-based GitHub Action. All actions pull the Docker image from Docker Hub at runtime.

### Basic Usage

Use Control Center in your workflows:

```yaml
- uses: jbcom/control-center@v1
  with:
    command: reviewer
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
```

### Specific Command Actions

Or use specific command actions for simpler interface:

```yaml
# AI Code Review
- uses: jbcom/control-center/actions/reviewer@v1
  with:
    repo: ${{ github.repository }}
    pr: ${{ github.event.pull_request.number }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}

# CI Failure Analysis
- uses: jbcom/control-center/actions/fixer@v1
  with:
    repo: ${{ github.repository }}
    run_id: ${{ github.run_id }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}

# Nightly Triage
- uses: jbcom/control-center/actions/curator@v1
  with:
    repo: ${{ github.repository }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GOOGLE_JULES_API_KEY: ${{ secrets.GOOGLE_JULES_API_KEY }}
    CURSOR_API_KEY: ${{ secrets.CURSOR_API_KEY }}
```

### Direct Docker Usage

You can also run Control Center directly via Docker:

```bash
# Pull the image
docker pull jbcom/control-center:latest

# Run a command
docker run --rm \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e OLLAMA_API_KEY="$OLLAMA_API_KEY" \
  jbcom/control-center:latest \
  reviewer --repo owner/repo --pr 123
```

### Version Pinning

**Recommended**: Use floating major version tags for automatic updates:
```yaml
- uses: jbcom/control-center@v1  # Latest v1.x.x
```

**Stable**: Pin to minor version for controlled updates:
```yaml
- uses: jbcom/control-center@v1.1  # Latest v1.1.x
```

**Locked**: Use exact version for reproducibility:
```yaml
- uses: jbcom/control-center@v1.1.0  # Exact version
```

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `command` | Command: gardener, curator, reviewer, fixer | Yes | - |
| `repo` | Target repository (owner/name) | No | - |
| `pr` | Pull request number | No | - |
| `target` | Target for gardener | No | `all` |
| `dry_run` | Run without making changes | No | `false` |
| `log_level` | Log level: debug, info, warn, error | No | `info` |

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token for API access |
| `CI_GITHUB_TOKEN` | Alternative GitHub token (CI workflows) |
| `OLLAMA_API_KEY` | Ollama Cloud API key |
| `GOOGLE_JULES_API_KEY` | Google Jules API key |
| `CURSOR_API_KEY` | Cursor Cloud Agent API key |

### Config File

Control Center looks for configuration in:
- `--config` flag
- `$HOME/.control-center.yaml`
- `./.control-center.yaml`
- `/etc/control-center/config.yaml`

Example:

```yaml
log:
  level: info
  format: text

gardener:
  target: all
  decompose: false
  backlog: true

curator:
  repo: jbcom/control-center
```

## Architecture

```
control-center/
├── cmd/control-center/     # CLI entrypoint
│   └── cmd/                # Cobra commands
│       ├── root.go
│       ├── gardener.go
│       ├── curator.go
│       ├── reviewer.go
│       ├── fixer.go
│       └── version.go
├── pkg/
│   ├── clients/            # API clients
│   │   ├── ollama/         # Ollama GLM 4.6
│   │   ├── jules/          # Google Jules
│   │   ├── cursor/         # Cursor Cloud Agent
│   │   └── github/         # GitHub API + gh CLI
│   ├── config/             # Configuration
│   └── orchestrator/       # Orchestration logic
├── Dockerfile
├── action.yml              # GitHub Action
├── .goreleaser.yml         # Release config
└── .golangci.yml           # Linter config
```

## Task Routing

The Curator automatically routes tasks to the appropriate AI agent:

| Task Type | Agent | Reason |
|-----------|-------|--------|
| Quick fix (<5 lines) | Ollama | Fast, inline |
| Multi-file refactor | Jules | Async, AUTO_CREATE_PR |
| Complex debugging | Cursor | Full IDE context |
| Documentation | Jules | Full file context |
| Ambiguous/sensitive | Human | Requires judgment |

## Development

### Prerequisites

- Go 1.23+
- Docker (optional)
- gh CLI (for GitHub operations)

### Build

```bash
go build -o control-center ./cmd/control-center
```

### Test

```bash
go test -v ./...
```

### Lint

```bash
golangci-lint run
```

### Release

Releases are automated via GoReleaser on tag push:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [secretssync](https://github.com/extended-data-library/secretssync) - Multi-account secrets management
- [vendor-connectors](https://github.com/jbcom/vendor-connectors) - Python API clients

---

<sub>Built with ❤️ by the jbcom ecosystem</sub>
