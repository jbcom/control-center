# GitHub Copilot Custom Agents - Setup Guide

## Overview

This repository includes 6 specialized GitHub Copilot custom agents for managing the jbcom ecosystem. These agents are defined in `.github/copilot/agents/` and are automatically available when using GitHub Copilot in this repository.

## Available Agents

### 1. CI/CD Deployer (`ci-deployer`)
**File:** `.github/copilot/agents/ci-deployer.agent.yaml`

Deploys and maintains CI/CD workflows across all 20 active repositories in the ecosystem.

**Commands:**
- `/deploy-ci <repo>` - Deploy CI workflow to specific repo
- `/check-workflows` - Audit all repo workflows
- `/update-workflow <repo>` - Update existing workflow
- `/standardize <repo>` - Bring repo to standard CI

**Use when:** You need to deploy or update CI/CD workflows across repositories.

### 2. Dependency Coordinator (`dependency-coordinator`)
**File:** `.github/copilot/agents/dependency-coordinator.agent.yaml`

Manages dependencies across the ecosystem, tracking version updates and ensuring compatibility.

**Commands:**
- `/check-deps [scope]` - Check for dependency updates
- `/update-deps <repo>` - Update dependencies for a repo
- `/cascade-update <package>` - Update package across all dependents
- `/security-updates` - Apply security updates only
- `/dep-graph` - Show dependency graph

**Use when:** You need to update dependencies or manage cross-repo dependency chains.

### 3. Ecosystem Manager (`ecosystem-manager`)
**File:** `.github/copilot/agents/ecosystem-manager.agent.yaml`

Central coordination agent for managing the entire jbcom ecosystem.

**Commands:**
- `/ecosystem-status` - Overall health check
- `/discover-repos` - Find and categorize repos
- `/sync-repo <repo>` - Sync repo to control center
- `/health-check` - Run full ecosystem health check

**Use when:** You need high-level overview or coordination across multiple repositories.

### 4. Game Dev Assistant (`game-dev`)
**File:** `.github/copilot/agents/game-dev.agent.yaml`

Specialized agent for the 12 game development repositories (Python, TypeScript, Godot, Rust).

**Commands:**
- `/game-status [repo]` - Status of game repos
- `/list-games [language]` - List games by language
- `/check-integrations <repo>` - List integrations used
- `/setup-game <repo>` - Get setup instructions
- `/build <repo> [platform]` - Build game

**Use when:** Working on game development projects or game-related infrastructure.

### 5. Release Coordinator (`release-coordinator`)
**File:** `.github/copilot/agents/release-coordinator.agent.yaml`

Coordinates releases across the ecosystem in the correct dependency order.

**Commands:**
- `/release-status` - Current versions across ecosystem
- `/pending-releases` - What needs releasing
- `/plan-release <repo>` - Plan release with dependencies
- `/release <repo>` - Trigger release (merge to main)
- `/verify-release <repo>` - Verify release succeeded
- `/check-pypi <package>` - Check PyPI availability

**Use when:** Managing releases or coordinating multi-repo release cascades.

### 6. Vendor Connectors Consolidator (`vendor-connectors-consolidator`)
**File:** `.github/copilot/agents/vendor-connectors-consolidator.agent.yaml`

Extracts scattered API integration code from game repos and consolidates it into the vendor-connectors library.

**Commands:**
- `/scan-integrations` - Find all integration code
- `/show-consolidation-plan` - Show extraction plan
- `/consolidate <connector>` - Consolidate specific connector
- `/extract <repo> <path>` - Extract code from repo
- `/create-migration-pr <repo>` - Create migration PR

**Use when:** Consolidating integration code or migrating to vendor-connectors.

## How to Use Copilot Agents

### In GitHub Copilot Chat

1. Open GitHub Copilot Chat in your IDE or on GitHub.com
2. Reference an agent by name: `@ci-deployer /check-workflows`
3. The agent will respond with specialized knowledge and capabilities

### Example Conversations

```
You: @ecosystem-manager /ecosystem-status
Copilot: [Analyzes all 20 repos and provides health report]

You: @release-coordinator /plan-release extended-data-types
Copilot: [Shows release plan including dependent repos]

You: @dependency-coordinator /cascade-update extended-data-types
Copilot: [Plans dependency update across all dependent packages]
```

## Agent Configuration Format

Each agent is defined using this YAML structure:

```yaml
name: agent-name
description: >
  Brief description of what the agent does

model: gpt-4

tools:
  - github      # Access to GitHub API
  - filesystem  # Access to read files
  - web-search  # Access to search the web

system_prompt: |
  You are the [Agent Name], responsible for...
  
  [Detailed instructions, context, and guidelines]

commands:
  - name: command-name
    description: What the command does
    pattern: /command-name {param}
```

## Cursor Agent Equivalents

For Cursor IDE users, equivalent agent definitions exist in `.cursor/agents/`:

- `ci-deployer.md` - Same as Copilot's ci-deployer
- `dependency-coordinator.md` - Same as Copilot's dependency-coordinator
- `game-dev.md` - Same as Copilot's game-dev
- `release-coordinator.md` - Same as Copilot's release-coordinator
- `vendor-connectors-consolidator.md` - Same as Copilot's vendor-connectors-consolidator
- `jbcom-ecosystem-manager.md` - Same as Copilot's ecosystem-manager
- `cursor-environment-triage.md` - Cursor-specific environment debugging agent

## Troubleshooting

### Agents Not Appearing

1. **Check file location:** Agents must be in `.github/copilot/agents/`
2. **Check file extension:** Must be `.agent.yaml` or `.agent.yml`
3. **Validate YAML:** Run `python3 -c "import yaml; yaml.safe_load(open('.github/copilot/agents/agent-name.agent.yaml'))"`
4. **Check permissions:** Ensure your GitHub account has access to Copilot for Business

### Agent Not Responding Correctly

1. **Check system_prompt:** Ensure it has clear, specific instructions
2. **Verify tools:** Agent only has access to listed tools
3. **Check model:** Ensure `gpt-4` or appropriate model is specified

### Adding New Agents

1. Create new `.agent.yaml` file in `.github/copilot/agents/`
2. Follow the format of existing agents
3. Validate YAML syntax
4. Test with simple commands first
5. Create corresponding Cursor agent in `.cursor/agents/` for IDE parity

## Integration with MCP Servers

All agents have access to MCP (Model Context Protocol) servers defined in `.ruler/ruler.toml`:

- **github** - GitHub API access
- **filesystem** - Repository file access
- **git** - Git operations
- **memory** - Persistent memory across sessions
- **conport** - Context portal for agent state
- **python-stdlib** - Python standard library docs
- **AWS servers** - AWS infrastructure access
- **cursor_agents** - Cursor background agent management

## Best Practices

1. **Use specific agents for specific tasks** - Don't use ecosystem-manager when dependency-coordinator is more appropriate
2. **Provide context** - Give agents repo names, file paths, and relevant details
3. **Chain commands** - Use one agent's output as input to another
4. **Verify actions** - Always review suggested changes before applying
5. **Report issues** - If an agent behaves incorrectly, document it

## Maintenance

### Updating Agents

1. Edit `.github/copilot/agents/<agent>.agent.yaml`
2. Update corresponding `.cursor/agents/<agent>.md` for parity
3. Test changes
4. Commit both files together

### Syncing Copilot ↔ Cursor

When adding/updating agents:
1. Update Copilot YAML in `.github/copilot/agents/`
2. Update Cursor MD in `.cursor/agents/`
3. Run `ruler apply` to regenerate consolidated instructions
4. Verify both environments work correctly

---

**Last Updated:** 2025-11-27
**Agent Count:** 6 Copilot, 7 Cursor (includes cursor-environment-triage)
**Status:** Production
