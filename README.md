# jbcom Ecosystem Management Hub

**This repository is the central management hub for all jbcom Python libraries.**

## Purpose

This is **NOT a template**. This is the control center where AI agents:
- Manage CI/CD workflows across all jbcom repositories
- Standardize agentic documentation processes
- Coordinate releases and updates
- Maintain consistency across the ecosystem
- Deploy changes to managed repositories

## Managed Repositories

- **extended-data-types** - Foundation library
- **lifecyclelogging** - Structured logging
- **directed-inputs-class** - Input validation
- **vendor-connectors** - Service integrations

## What This Repository Contains

### 1. **Standard Workflows** (`workflows/`)
The canonical CI/CD workflows that get deployed to managed repositories:
- `standard-ci.yml` - Test, lint, type check, release workflow
- `security-scan.yml` - Dependabot and security scanning
- `template-validation.yml` - For validating this management hub itself

### 2. **Agentic Documentation** (`.ruler/` and `.copilot/`)
Centralized agent instructions that can be deployed to managed repos:
- Core guidelines (CalVer, release process, best practices)
- Repository-specific overrides
- Ecosystem coordination instructions

### 3. **Management Tools** (`tools/`)
Scripts and utilities for managing the ecosystem:
- `deploy-workflows.py` - Deploy workflows to managed repos
- `sync-docs.py` - Synchronize documentation
- `check-health.py` - Ecosystem health monitoring
- `coordinate-release.py` - Release orchestration

### 4. **Agent Configurations** (`.copilot/`)
Specialized agents for ecosystem management:
- **jbcom-ecosystem-manager** - Main coordination agent
- **ci-deployer** - Deploys CI/CD changes
- **doc-synchronizer** - Keeps documentation consistent

## Agent Workflows

### Deploying CI/CD Changes

```bash
# Agent reads standard workflow
# Agent checks which repos need updates
# Agent creates PRs in each repo
# Agent monitors CI results
# Agent reports status
```

### Synchronizing Documentation

```bash
# Agent generates docs from .ruler/ sources
# Agent determines which repos need updates
# Agent applies changes with context
# Agent creates coordinated PRs
```

### Coordinating Releases

```bash
# Agent checks dependency graph
# Agent determines release order
# Agent verifies CI status
# Agent triggers releases in sequence
# Agent monitors PyPI availability
```

## For AI Agents

When working in this repository, you are in **management mode**. Your job is to:

1. **Maintain standards** in `workflows/` and `.ruler/`
2. **Deploy changes** to managed repositories via GitHub API
3. **Monitor health** across the ecosystem
4. **Coordinate releases** in dependency order
5. **Standardize processes** across all repos

### Key Capabilities Needed

- GitHub API access (create PRs, update files, check CI)
- Git operations (clone, branch, commit, push)
- PyPI API access (check versions, releases)
- File manipulation (templates, configuration)

### Management Commands

- `/deploy-workflow <workflow-name> [repos...]` - Deploy workflow to repos
- `/sync-docs [repos...]` - Synchronize documentation
- `/standardize-config <config-type>` - Standardize configuration files
- `/health-check` - Check ecosystem health
- `/coordinate-release <repo>` - Orchestrate release

## Directory Structure

```
/
├── workflows/              # Standard CI/CD workflows (to deploy)
│   ├── standard-ci.yml
│   ├── security-scan.yml
│   └── README.md
│
├── .ruler/                 # Centralized agent documentation (source)
│   ├── AGENTS.md
│   ├── ecosystem.md
│   ├── cursor.md
│   ├── copilot.md
│   └── ruler.toml
│
├── .copilot/               # Copilot-specific management agents
│   ├── agents/
│   │   ├── jbcom-ecosystem-manager.agent.md
│   │   ├── ci-deployer.agent.md
│   │   └── doc-synchronizer.agent.md
│   ├── prompts/
│   │   └── jbcom-inventory.prompt.md
│   └── instructions/
│       └── jbcom-management.instructions.md
│
├── tools/                  # Management automation scripts
│   ├── deploy_workflows.py
│   ├── sync_docs.py
│   ├── check_health.py
│   ├── coordinate_release.py
│   └── README.md
│
├── configs/                # Standard configuration templates
│   ├── pyproject.toml.template
│   ├── tox.ini.template
│   ├── .pre-commit-config.yaml.template
│   └── README.md
│
├── docs/                   # Management hub documentation
│   ├── MANAGEMENT.md
│   ├── DEPLOYMENT.md
│   ├── AGENTS.md
│   └── ECOSYSTEM.md
│
└── ECOSYSTEM_STATE.json    # Current state of all managed repos
```

## Getting Started (For Agents)

1. **Understand your role**: You manage OTHER repositories, not this one
2. **Learn the ecosystem**: Read `ECOSYSTEM.md` for repository relationships
3. **Check current state**: Review `ECOSYSTEM_STATE.json` for repo status
4. **Use management tools**: Scripts in `tools/` help deploy changes
5. **Follow workflows**: See `docs/DEPLOYMENT.md` for deployment processes

## Development Workflow

### Making Changes to Standards

1. Update files in this repo (`workflows/`, `.ruler/`, etc.)
2. Test changes (use validation workflows)
3. Commit and push to this repo
4. Deploy to managed repos using management tools
5. Monitor deployment and CI results

### Adding a New Managed Repository

1. Add repo to `ECOSYSTEM_STATE.json`
2. Deploy standard workflows: `/deploy-workflow standard-ci <repo>`
3. Deploy documentation: `/sync-docs <repo>`
4. Verify CI passes
5. Update ecosystem documentation

## Security

- **Never commit credentials** - Use GitHub secrets in workflows
- **Use PRs for deployment** - Don't push directly to managed repos
- **Verify CI passes** - Before merging deployment PRs
- **Audit changes** - Review what gets deployed

## Current Status

See `ECOSYSTEM_STATE.json` for real-time status of:
- Last successful workflow deployment
- Current CI/CD workflow versions in each repo
- Documentation sync status
- Latest releases
- Open PRs and issues

---

**This is a meta-repository.** Changes here propagate to the ecosystem. Handle with care.
