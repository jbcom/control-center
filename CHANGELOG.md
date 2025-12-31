# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Features

- **Go CLI**: Pure Go binary with zero jbcom dependencies
  - `reviewer` - AI code review using Ollama GLM 4.6
  - `fixer` - CI failure analysis and fix suggestions
  - `curator` - Nightly issue/PR triage with smart routing
  - `delegator` - `/jules` and `/cursor` command routing
  - `gardener` - Enterprise cascade orchestration
  - `version` - Build information

- **Native API Clients**:
  - Ollama Cloud (GLM 4.6)
  - Google Jules
  - Cursor Cloud Agent
  - GitHub (via gh CLI)

- **Namespaced GitHub Actions**:
  - `jbcom/control-center/actions/reviewer@v1`
  - `jbcom/control-center/actions/fixer@v1`
  - `jbcom/control-center/actions/curator@v1`
  - `jbcom/control-center/actions/delegator@v1`
  - `jbcom/control-center/actions/gardener@v1`

- **Distribution**:
  - Go module (`go install github.com/jbcom/control-center/cmd/control-center@latest`)
  - Docker image (`ghcr.io/jbcom/control-center`)
  - GitHub releases (binaries for Linux, macOS, Windows)

### 📚 Documentation

- Hugo + doc2go documentation site
- Comprehensive CLAUDE.md and AGENTS.md
- API reference via godoc

### 🏗️ Build

- Multi-stage Alpine Dockerfile with gh CLI
- GoReleaser for cross-platform builds
- Makefile for development workflow
- Pre-commit hooks for code quality

[Unreleased]: https://github.com/jbcom/control-center/compare/v0.0.0...HEAD
