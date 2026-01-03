---
title: "Control Center"
description: "Enterprise AI orchestration for the jbcom ecosystem"
---

# Control Center

**The unified CLI for enterprise AI orchestration.**

Control Center is the **only public Go release** from the jbcom ecosystem, providing native integrations with AI agents for managing repositories, workflows, and automation across the enterprise.

## Features

- **🌱 Gardener** - Enterprise-level cascade orchestration
- **📋 Curator** - Nightly triage of issues and PRs with AI routing
- **🔍 Reviewer** - Ollama-powered code review
- **🔧 Fixer** - Automated CI failure analysis and suggestions
- **🤖 Native AI Clients** - Ollama, Google Jules, Cursor Cloud

## Quick Start

### Installation

```bash
# Go Install (recommended)
go install github.com/jbcom/control-center/cmd/control-center@latest

# Docker
docker pull jbcom/control-center:latest

# Verify
control-center version
```

### Basic Usage

```bash
# Review a PR with AI
control-center reviewer --repo jbcom/my-project --pr 123

# Analyze CI failures
control-center fixer --repo jbcom/my-project --pr 123

# Triage issues across a repository
control-center curator --repo jbcom/my-project

# Run enterprise orchestration
control-center gardener --target all
```

## Architecture

```
control-center/
├── cmd/control-center/     # CLI entrypoint (Cobra)
│   └── cmd/                # Commands
│       ├── root.go         # Base configuration
│       ├── gardener.go     # Enterprise orchestration
│       ├── curator.go      # Issue/PR triage
│       ├── reviewer.go     # AI code review
│       └── fixer.go        # CI failure resolution
├── pkg/
│   ├── clients/            # Native API clients
│   │   ├── ollama/         # Ollama GLM 4.6
│   │   ├── jules/          # Google Jules
│   │   ├── cursor/         # Cursor Cloud Agent
│   │   └── github/         # GitHub API + gh CLI
│   └── orchestrator/       # Orchestration logic
├── Dockerfile              # Multi-stage build
├── action.yml              # GitHub Action
└── .goreleaser.yml         # Cross-platform releases
```

## Configuration

Control Center uses Viper for configuration. Set options via:

### Environment Variables

```bash
export GITHUB_TOKEN="your-token"
export OLLAMA_API_KEY="your-key"
export GOOGLE_JULES_API_KEY="your-key"
export CURSOR_API_KEY="your-key"
```

### Config File

Create `~/.control-center.yaml`:

```yaml
log:
  level: info
  format: text

gardener:
  target: all
  decompose: false

curator:
  repo: jbcom/control-center
```

## GitHub Action

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

## Part of the jbcom Ecosystem

Control Center orchestrates automation across the jbcom enterprise:

| Organization | Domain | Purpose |
|-------------|--------|---------|
| jbcom | jonbogaty.com | Enterprise control plane |
| agentic-dev-library | agentic.dev | AI agent orchestration |
| strata-game-library | strata.game | 3D graphics library |
| extended-data-library | extendeddata.dev | Enterprise data utilities |

## License

MIT License - see [LICENSE](https://github.com/jbcom/control-center/blob/main/LICENSE) for details.
