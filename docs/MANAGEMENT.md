# jbcom Ecosystem Management Hub

## What This Is

This repository is the **central control hub** for managing the entire jbcom Python library ecosystem. It is NOT a template to copy from - it's a living management system where AI agents standardize, deploy, and coordinate across all jbcom repositories.

## Core Concept

**Single Source of Truth → Deploy Everywhere**

Changes made here propagate to all managed repositories through automated deployment processes. This ensures consistency, reduces drift, and enables ecosystem-wide coordination.

## Managed Repositories

1. **extended-data-types** (foundation)
2. **lifecyclelogging** (production)
3. **directed-inputs-class** (development)
4. **vendor-connectors** (planning)

## What Agents Can Do Here

### 1. Deploy CI/CD Workflows
```
Agent Action:
- Update workflows/standard-ci.yml
- Run: /deploy-workflow standard-ci.yml
- Agent creates PRs in all repos
- Agent monitors CI results
- Agent reports deployment status
```

### 2. Synchronize Documentation
```
Agent Action:
- Update .ruler/AGENTS.md
- Run ruler apply (generates local copies)
- Run: /sync-docs
- Agent deploys to all repos
- Agent verifies consistency
```

### 3. Coordinate Releases
```
Agent Action:
- Run: /coordinate-release directed-inputs-class
- Agent checks dependencies (extended-data-types)
- Agent verifies CI passing
- Agent determines if extended-data-types needs release first
- Agent provides release plan
- Agent can execute releases in order
```

### 4. Standardize Configuration
```
Agent Action:
- Update configs/pyproject.toml.template
- Run: /standardize-config pyproject
- Agent identifies differences across repos
- Agent creates alignment PRs
- Agent explains what changed and why
```

### 5. Monitor Ecosystem Health
```
Agent Action:
- Run: /ecosystem-status
- Agent queries all repos via GitHub API
- Agent checks: CI status, open PRs, issues, releases
- Agent identifies problems
- Agent suggests actions
```

## Directory Structure

```
management-hub/
├── workflows/           # Standard CI/CD (deployed to repos)
│   ├── standard-ci.yml
│   ├── security-scan.yml
│   └── README.md
│
├── .ruler/              # Centralized docs (source of truth)
│   ├── AGENTS.md       # → deployed to all repos
│   ├── ecosystem.md    # → deployed to all repos
│   └── ruler.toml
│
├── .copilot/            # Management-specific agents
│   ├── agents/
│   │   ├── jbcom-ecosystem-manager.agent.md
│   │   ├── ci-deployer.agent.md
│   │   └── doc-synchronizer.agent.md
│   └── instructions/
│       └── jbcom-management.instructions.md
│
├── tools/               # Automation scripts
│   ├── deploy_workflows.py
│   ├── sync_docs.py
│   └── check_health.py
│
├── configs/             # Standard configuration templates
│   ├── pyproject.toml.template
│   ├── tox.ini.template
│   └── .pre-commit-config.yaml.template
│
├── docs/                # Management documentation
│   ├── DEPLOYMENT.md
│   ├── AGENTS.md
│   └── ARCHITECTURE.md
│
└── ECOSYSTEM_STATE.json # Current state of all repos
```

## Deployment Workflows

### Deploying Workflow Changes

1. **Update workflow** in `workflows/standard-ci.yml`
2. **Test locally** with validation
3. **Deploy**: `/deploy-workflow standard-ci.yml`
4. **Agent creates PRs** in all repos
5. **Monitor CI** across ecosystem
6. **Update state** when complete

### Synchronizing Documentation

1. **Update source** in `.ruler/AGENTS.md`
2. **Regenerate** with `ruler apply`
3. **Deploy**: `/sync-docs`
4. **Agent creates PRs** with updated docs
5. **Review differences**
6. **Merge when ready**

### Coordinating Releases

1. **Check status**: `/ecosystem-status`
2. **Plan release**: `/coordinate-release <repo>`
3. **Agent analyzes dependencies**
4. **Agent provides release order**
5. **Execute**: Agent can trigger in sequence
6. **Monitor**: PyPI availability between releases

## Key Files

### ECOSYSTEM_STATE.json
Current state of all managed repositories:
- Workflow versions deployed
- Documentation sync status
- Latest releases
- Pending actions
- Health indicators

### workflows/standard-ci.yml
The canonical CI workflow deployed to all repos. Includes:
- Multi-version Python testing
- Type checking, linting
- Coverage reporting
- Auto-versioning
- PyPI publishing

### .ruler/AGENTS.md
Source of truth for agent documentation:
- CalVer philosophy
- Release process
- Best practices
- Common misconceptions
- Ecosystem guidelines

## For AI Agents

### Your Role Here

You are in **management mode**, not development mode. Your actions here affect the entire ecosystem. You can:

1. **Update standards** (workflows, docs, configs)
2. **Deploy changes** to managed repos
3. **Monitor health** across ecosystem
4. **Coordinate releases** in correct order
5. **Standardize processes** everywhere

### Commands Available

- `/deploy-workflow <name> [repos...]` - Deploy CI/CD changes
- `/sync-docs [repos...]` - Synchronize documentation
- `/coordinate-release <repo>` - Plan/execute release
- `/ecosystem-status` - Full health check
- `/standardize-config <type>` - Align configuration
- `/discover-repos` - Inventory all repos
- `/health-check` - Quick status

### Best Practices

1. **Test here first** before deploying
2. **Use PRs** for all deployments (never push to main in managed repos)
3. **Monitor CI** after deployments
4. **Update ECOSYSTEM_STATE.json** after changes
5. **Link related PRs** across repos
6. **Work in dependency order** (foundation → leaves)
7. **Report status** after operations

## Examples

### Example 1: Updating CI for Security Patch

```
User: A new ruff version has security fixes. Update all repos.

Agent:
1. Updates workflows/standard-ci.yml with new ruff version
2. Tests workflow validation in this repo
3. Runs: /deploy-workflow standard-ci.yml
4. Creates PRs in all 4 repos
5. Monitors CI (all pass)
6. Reports:
   ✅ extended-data-types PR #125
   ✅ lifecyclelogging PR #47
   ✅ directed-inputs-class PR #89
   ✅ vendor-connectors PR #12
7. Updates ECOSYSTEM_STATE.json
```

### Example 2: Coordinating Major Release

```
User: directed-inputs-class is ready for v1.0.0

Agent:
1. Runs: /coordinate-release directed-inputs-class
2. Checks dependencies:
   - Depends on extended-data-types ✅ (latest: 2025.11.164)
3. Checks CI: ✅ All passing
4. Release plan:
   Step 1: Merge PR to main (auto-triggers release)
   Step 2: Wait 5 min for PyPI
   Step 3: Update vendor-connectors dependency (if needed)
5. Ready to release? (awaits confirmation)
```

### Example 3: Ecosystem Health Check

```
User: /ecosystem-status

Agent:
🏥 jbcom Ecosystem Health Report

Overall: ✅ Healthy

Repositories (4):
  ✅ extended-data-types (v2025.11.164)
  ✅ lifecyclelogging (v2025.11.82)
  ⚠️  directed-inputs-class (development)
  ⏸️  vendor-connectors (planning)

CI Status:
  ✅ All passing (4/4)

Security:
  ✅ No alerts

Pending Actions:
  1. Deploy workflow update to directed-inputs-class
  2. Sync docs to vendor-connectors

Last Deployment: 2025-11-20 (standard-ci.yml v1.0.0)
```

## Architecture

This is a **hub-and-spoke model**:

```
         Management Hub (THIS REPO)
              /  |  |  \
             /   |  |   \
            /    |  |    \
           /     |  |     \
    extended  lifecycle  directed  vendor
     -data    -logging   -inputs  -connectors
     -types
```

All standardization, deployment, and coordination happens from the hub.

---

**Changes here affect the entire ecosystem. Proceed with care and verification.**
