# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Philosophy

**We are stewards and servants of the open source community FIRST.**

This repository exists because of the OSS community. Every decision should:
1. **Serve the community** - Make tools that help everyone, not just us
2. **Lead by example** - If we expect standards from others, we follow them ourselves
3. **Be transparent** - Our tooling is public, our process is public

---

## What This Repo Does

**jbcom Control Center** is a pure Go CLI tool that provides:
1. **AI-powered code review** using Ollama GLM 4.6
2. **CI failure analysis** with automated fix suggestions
3. **Issue/PR triage** with smart agent routing
4. **Enterprise orchestration** across organizations

### The Binary

```bash
# Install
go install github.com/jbcom/control-center/cmd/control-center@latest

# Or Docker
docker pull jbcom/control-center:latest

# Commands
control-center reviewer --repo owner/name --pr 123
control-center fixer --repo owner/name --run-id 456
control-center curator --repo owner/name
control-center delegator --repo owner/name --issue 789 --command "/jules fix bug"
control-center gardener --target all
```

---

## 🚀 Using Control Center (OSS)

### Option 1: Namespaced GitHub Actions (Recommended)

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
    run_id: ${{ github.event.workflow_run.id }}

# Issue Delegation (/jules, /cursor commands)
- uses: jbcom/control-center/actions/delegator@v1
  with:
    repo: ${{ github.repository }}
    issue: ${{ github.event.issue.number }}
    command: ${{ github.event.comment.body }}

# Nightly Issue Triage
- uses: jbcom/control-center/actions/curator@v1
  with:
    repo: ${{ github.repository }}

# Enterprise Orchestration
- uses: jbcom/control-center/actions/gardener@v1
  with:
    target: all
```

### Option 2: Direct CLI

```bash
# In your workflow
- run: |
    go install github.com/jbcom/control-center/cmd/control-center@latest
    control-center reviewer --repo ${{ github.repository }} --pr ${{ github.event.pull_request.number }}
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
```

### Option 3: Docker

```bash
docker run --rm \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e OLLAMA_API_KEY="$OLLAMA_API_KEY" \
  jbcom/control-center:latest \
  reviewer --repo owner/name --pr 123
```

---

## Required Secrets

| Secret | Required For | How to Get |
|--------|--------------|------------|
| `GITHUB_TOKEN` | All commands | Automatic in Actions |
| `OLLAMA_API_KEY` | reviewer, fixer, curator | [ollama.com](https://ollama.com) |
| `GOOGLE_JULES_API_KEY` | delegator (/jules) | Google Cloud Console |
| `CURSOR_API_KEY` | delegator (/cursor) | Cursor dashboard |

---

## Repository Structure

```
control-center/
├── cmd/control-center/     # CLI entrypoint (Cobra)
│   └── cmd/                # Commands
│       ├── root.go         # Global flags, Viper config
│       ├── reviewer.go     # AI code review
│       ├── fixer.go        # CI failure analysis
│       ├── curator.go      # Issue/PR triage
│       ├── delegator.go    # /jules, /cursor routing
│       └── gardener.go     # Enterprise orchestration
├── pkg/
│   ├── clients/            # Native API clients (zero external deps)
│   │   ├── ollama/         # Ollama GLM 4.6 Cloud
│   │   ├── jules/          # Google Jules
│   │   ├── cursor/         # Cursor Cloud Agent
│   │   └── github/         # GitHub API via gh CLI
│   └── orchestrator/       # Gardener logic
├── actions/                # Namespaced GitHub Actions
│   ├── reviewer/action.yml
│   ├── fixer/action.yml
│   ├── curator/action.yml
│   ├── delegator/action.yml
│   └── gardener/action.yml
├── docs/site/              # Hugo + doc2go documentation
├── repository-files/       # Files synced to managed repos
│   └── always-sync/        # Always overwrite
├── Dockerfile              # Multi-stage Alpine build
├── action.yml              # Root action (composite)
├── .goreleaser.yml         # Cross-platform releases
└── go.mod                  # Pure Go, no jbcom deps
```

---

## Development

### Build

```bash
make build           # Build to bin/
make install         # Install to GOPATH/bin
make docker-build    # Build Docker image
```

### Test

```bash
make test            # Run tests with coverage
make lint            # Run golangci-lint
make lint-fix        # Auto-fix lint issues
```

### Release

Releases are automated via GoReleaser on tag push:

```bash
git tag v1.0.0
git push origin v1.0.0
# GoReleaser builds binaries, Docker pushes to GHCR
```

---

## AI Agent Triggers

In any issue or PR comment:

| Command | Agent | Description |
|---------|-------|-------------|
| `/jules <task>` | Google Jules | Multi-file refactoring, auto-creates PR |
| `/cursor <task>` | Cursor Cloud | Long-running tasks with IDE context |

---

## Session Protocol

### Start of Session

```bash
cat memory-bank/activeContext.md
cat memory-bank/progress.md
```

### End of Session

```bash
cat >> memory-bank/activeContext.md << 'EOF'

## Session: $(date +%Y-%m-%d)

### Completed
- [x] Task description

### For Next Agent
- [ ] Follow-up task
EOF

git add memory-bank/
git commit -m "docs: update memory bank for handoff"
```

---

## Design Principles

1. **Pure Go** - No dependencies on other jbcom packages
2. **Single Binary** - One tool, multiple commands
3. **Native Clients** - Direct HTTP, no SDK dependencies
4. **OSS First** - Everything public, everything documented
5. **Lead by Example** - We use what we build
