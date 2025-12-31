---
title: "Getting Started"
weight: 1
---

# Getting Started

This guide walks you through installing and configuring Control Center.

## Prerequisites

- Go 1.21+ (for source installation)
- Docker (optional, for containerized usage)
- GitHub token with `repo` scope
- API keys for AI services (Ollama, Jules, Cursor)

## Installation

### Option 1: Go Install (Recommended)

```bash
go install github.com/jbcom/control-center/cmd/control-center@latest
```

### Option 2: Docker

```bash
docker pull ghcr.io/jbcom/control-center:latest

# Run with environment variables
docker run --rm \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e OLLAMA_API_KEY="$OLLAMA_API_KEY" \
  ghcr.io/jbcom/control-center:latest reviewer --repo jbcom/my-project --pr 123
```

### Option 3: Build from Source

```bash
git clone https://github.com/jbcom/control-center.git
cd control-center
make build
./bin/control-center version
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub token with `repo` scope |

### Optional Environment Variables

| Variable | Description |
|----------|-------------|
| `OLLAMA_API_KEY` | Ollama Cloud API key |
| `GOOGLE_JULES_API_KEY` | Google Jules API key |
| `CURSOR_API_KEY` | Cursor Cloud Agent API key |

### Config File

Create `~/.control-center.yaml`:

```yaml
log:
  level: info    # debug, info, warn, error
  format: text   # text, json

# Default settings for commands
gardener:
  target: all
  decompose: false
  backlog: true

curator:
  repo: ""  # Set per-invocation
```

## Verify Installation

```bash
control-center version
# control-center dev (commit: abc123, built: 2024-01-01T00:00:00Z)

control-center --help
# Shows all available commands
```

## Next Steps

- [Commands Reference](/commands/) - Learn about each command
- [API Reference](/api/) - Explore the Go packages
- [GitHub Action](/#github-action) - Use in CI/CD
