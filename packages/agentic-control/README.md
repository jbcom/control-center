# agentic-control

> Unified AI agent fleet management, triage, and orchestration toolkit for control centers

[![npm version](https://badge.fury.io/js/agentic-control.svg)](https://www.npmjs.com/package/agentic-control)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🎯 Intelligent Token Switching** - Automatically selects the correct GitHub token based on organization
- **🚀 Fleet Management** - Spawn, monitor, and coordinate Cursor Background Agents
- **🔍 AI-Powered Triage** - Analyze conversations, review code, extract tasks
- **🤝 Station-to-Station Handoff** - Seamless agent continuity across sessions
- **🔐 Multi-Org Support** - Manage agents across multiple GitHub organizations

## Installation

```bash
npm install -g agentic-control
# or
pnpm add -g agentic-control
```

## Quick Start

### 1. Configure Tokens

Set environment variables for your GitHub organizations:

```bash
export GITHUB_JBCOM_TOKEN="ghp_xxx"      # Personal org
export GITHUB_FSC_TOKEN="ghp_xxx"        # Enterprise org
export ANTHROPIC_API_KEY="sk-xxx"        # For AI features
export CURSOR_API_KEY="xxx"              # For fleet management
```

### 2. Check Token Status

```bash
agentic tokens status
```

### 3. List Your Fleet

```bash
agentic fleet list --running
```

### 4. Spawn an Agent

```bash
agentic fleet spawn https://github.com/org/repo "Fix the CI workflow" --model claude-sonnet-4-20250514
```

### 5. Analyze a Session

```bash
agentic triage analyze bc-xxx-xxx -o report.md --create-issues
```

## Commands

### Token Management

```bash
# Check all token status
agentic tokens status

# Validate required tokens
agentic tokens validate

# Show token for a specific repo
agentic tokens for-repo FlipsideCrypto/terraform-modules
```

### Fleet Management

```bash
# List all agents
agentic fleet list

# List only running agents
agentic fleet list --running

# Get fleet summary
agentic fleet summary

# Spawn a new agent (with explicit model!)
agentic fleet spawn <repo> <task> --model claude-sonnet-4-20250514

# Send followup message
agentic fleet followup <agent-id> "Status update?"

# Run coordination loop
agentic fleet coordinate --pr 123 --repo org/repo
```

### AI Triage

```bash
# Quick triage of text
agentic triage quick "Error in deployment pipeline"

# Review code changes
agentic triage review --base main --head HEAD

# Analyze agent conversation
agentic triage analyze <agent-id> -o report.md

# Create issues from analysis
agentic triage analyze <agent-id> --create-issues
```

### Handoff Protocol

```bash
# Initiate handoff to successor
agentic handoff initiate <predecessor-id> --pr 123 --branch my-branch

# Confirm health as successor
agentic handoff confirm <predecessor-id>

# Take over from predecessor
agentic handoff takeover <predecessor-id> 123 my-new-branch
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_JBCOM_TOKEN` | Token for jbcom org | For jbcom repos |
| `GITHUB_FSC_TOKEN` | Token for FlipsideCrypto org | For FSC repos |
| `GITHUB_TOKEN` | Default fallback token | Fallback |
| `ANTHROPIC_API_KEY` | Anthropic API key | For AI features |
| `CURSOR_API_KEY` | Cursor API key | For fleet ops |

### Custom Organizations

Add custom organizations via environment:

```bash
export AGENTIC_ORG_MYORG_TOKEN=MY_CUSTOM_TOKEN_VAR
```

### PR Review Token

By default, all PR review operations use `GITHUB_JBCOM_TOKEN` for consistent identity.
Override with:

```bash
export AGENTIC_PR_REVIEW_TOKEN=GITHUB_MY_TOKEN
```

## Programmatic Usage

```typescript
import { Fleet, AIAnalyzer, getTokenForRepo } from "agentic-control";

// Fleet management
const fleet = new Fleet();
const agents = await fleet.list();
await fleet.spawn({
  repository: "https://github.com/org/repo",
  task: "Fix the bug",
  model: "claude-sonnet-4-20250514",
});

// Token-aware operations
const token = getTokenForRepo("FlipsideCrypto/terraform-modules");
// Returns GITHUB_FSC_TOKEN value

// AI Analysis
const analyzer = new AIAnalyzer();
const result = await analyzer.quickTriage("Error in deployment");
```

## Token Switching Logic

The package automatically selects tokens based on organization:

```
Repository                           → Token Used
──────────────────────────────────────────────────
FlipsideCrypto/terraform-modules     → GITHUB_FSC_TOKEN
FlipsideCrypto/fsc-control-center    → GITHUB_FSC_TOKEN
jbcom/jbcom-control-center           → GITHUB_JBCOM_TOKEN
jbcom/extended-data-types            → GITHUB_JBCOM_TOKEN
unknown/repo                         → GITHUB_TOKEN (default)

PR Review Operations (always)        → GITHUB_JBCOM_TOKEN
```

## Architecture

```
agentic-control/
├── src/
│   ├── core/           # Types, tokens, config
│   │   ├── types.ts    # Shared type definitions
│   │   ├── tokens.ts   # Intelligent token switching
│   │   └── config.ts   # Configuration management
│   ├── fleet/          # Cursor agent fleet management
│   │   ├── fleet.ts    # High-level Fleet API
│   │   └── cursor-api.ts
│   ├── triage/         # AI-powered analysis
│   │   └── analyzer.ts # Claude-based analysis
│   ├── github/         # Token-aware GitHub ops
│   │   └── client.ts   # Multi-org GitHub client
│   ├── handoff/        # Agent continuity
│   │   └── manager.ts  # Handoff protocols
│   ├── cli.ts          # Command-line interface
│   └── index.ts        # Main exports
└── tests/
```

## Development

```bash
# Install dependencies
pnpm install

# Build
pnpm run build

# Test
pnpm test

# Watch mode
pnpm run dev
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `agentic triage review` before pushing
5. Create a pull request

## License

MIT © [Jon Bogaty](https://github.com/jbcom)

---

**Part of the [jbcom-control-center](https://github.com/jbcom/jbcom-control-center) ecosystem**
