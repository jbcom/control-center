# Agentic Ecosystem Architecture

This document outlines the architecture, scope, and ownership boundaries of the `agentic` ecosystem, a collection of repositories designed for multi-agent orchestration.

## Target Architecture

The ecosystem is designed to separate vendor-specific concerns from the core orchestration logic.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              vendor-connectors (Python)                  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │ Cursor  │ │Anthropic│ │  AWS    │ │ GitHub  │ ...   │   │
│  │  │Connector│ │Connector│ │Connector│ │Connector│       │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │   │
│  │       │           │           │           │             │   │
│  └───────┼───────────┼───────────┼───────────┼─────────────┘   │
│          │           │           │           │                  │
│          └───────────┴───────────┴───────────┘                  │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           agentic-control (Node.js) - PROTOCOL LAYER     │   │
│  │                                                          │   │
│  │  • Fleet management protocols (vendor-agnostic)          │   │
│  │  • Agent registration protocol                           │   │
│  │  • Agent-to-agent communication protocol                 │   │
│  │  • Triage and handoff protocols                          │   │
│  │  • Provider interface (plugs in vendor-connectors)       │   │
│  └───────────────────────────────┬─────────────────────────┘   │
│                                  │                              │
│                                  ▼                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            agentic-crew (Python) - CrewAI LAYER          │   │
│  │                                                          │   │
│  │  • CrewAI-specific flows and workflows                   │   │
│  │  • Manager agent patterns                                │   │
│  │  • Bridge to agentic-control protocol                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Ownership & Responsibilities

### `vendor-connectors`
**Purpose**: Vendor-specific API clients and SDK wrappers. This repository contains the building blocks for interacting with third-party services.
**Owner**: `jbcom-control-center` (Python package management)
**Language**: Python
**PyPI Package**: `vendor-connectors`
**URL**: [github.com/jbcom/python-vendor-connectors](https://github.com/jbcom/python-vendor-connectors)

| Connector | Status | Notes |
|-----------|--------|-------|
| Cursor | ❌ **NEEDED** | Port from `agentic-control/src/fleet/cursor-api.ts` |
| Anthropic | ❌ **NEEDED** | Wrap Claude Agent SDK |
| AWS | ✅ Exists | |
| GitHub | ✅ Exists | |
| Google | ✅ Exists | |
| Slack | ✅ Exists | |
| Vault | ✅ Exists | |
| Zoom | ✅ Exists | |

### `agentic-control`
**Purpose**: A vendor-agnostic protocol layer for agent orchestration. This repository defines the "rules of the road" for how agents communicate and hand off tasks.
**Owner**: `jbcom-control-center` (Node.js package management)
**Language**: TypeScript
**NPM Package**: `agentic-control`
**URL**: [github.com/jbcom/nodejs-agentic-control](https://github.com/jbcom/nodejs-agentic-control)

| Module | Status | Notes |
|--------|--------|-------|
| `core/` | ✅ Keep | Core types and interfaces |
| `fleet/` | 🔄 Refactor | Remove vendor-specific code, keep protocols |
| `triage/` | ✅ Keep | Agent triage logic |
| `handoff/` | ✅ Keep | Agent handoff logic |
| `github/` | ✅ Keep | GitHub integration (uses gh CLI) |
| `providers/` | ❌ **NEW** | Provider interface that uses vendor-connectors |

### `agentic-crew` (NEW)
**Purpose**: A CrewAI-specific orchestration layer. This repository provides concrete implementations of agent crews using the CrewAI framework.
**Owner**: `jbcom-control-center` (Python package management)
**Language**: Python
**PyPI Package**: `agentic-crew`
**URL**: [github.com/jbcom/python-agentic-crew](https://github.com/jbcom/python-agentic-crew)

| Module | Status | Notes |
|--------|--------|-------|
| CrewAI flows | ❌ **NEW** | Move from agentic-control/python/ |
| Manager patterns | ❌ **NEW** | |
| Protocol bridge | ❌ **NEW** | Bridge to agentic-control |
