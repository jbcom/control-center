# Terraform Repository Manager - Quick Start

## Overview

The Terraform Repository Manager is a custom AI agent that uses the Terraform MCP server to actively manage all 18 jbcom GitHub repositories.

## What It Does

✅ **Active Management**: Uses Terraform MCP server to manage repository configuration  
✅ **Drift Detection**: Automatically detects when repos diverge from policy  
✅ **State Tracking**: Maintains state in HCP Terraform Cloud  
✅ **Policy Enforcement**: Ensures all repos follow consistent standards  
✅ **Change Preview**: Shows exactly what will change before applying  

## Quick Start

### 1. Invoke the Agent

**Via GitHub Copilot Workspace:**
```
@terraform-repository-manager Initialize Terraform and import all repositories
```

**Via agentic-control CLI:**
```bash
cd /path/to/jbcom-control-center
agentic fleet spawn . --agent terraform-repository-manager \
  --task "Initialize Terraform workspace and import all 18 repositories"
```

### 2. Common Tasks

**Change Repository Settings:**
```
@terraform-repository-manager Enable wiki feature on agentic-control repository
```

**Add New Repository:**
```
@terraform-repository-manager Add new repository 'new-project' to managed list (Python)
```

**Fix Drift:**
```
@terraform-repository-manager Check for drift and reapply configuration
```

**Update Policy:**
```
@terraform-repository-manager Change all repositories to require 1 approval instead of 0
```

## How It Works

1. **You ask the agent** to make a change
2. **Agent updates Terraform** files in `/terraform/`
3. **Agent creates a plan run** via MCP server to preview changes
4. **Agent reviews the plan** to ensure it's correct
5. **Agent applies the plan** to update repositories
6. **Agent reports back** with what changed

## What the Agent Manages

### Repository Settings
- Merge strategies
- Branch protection
- Security scanning
- GitHub Pages
- Feature flags

### State Management
- Workspace: `jbcom/jbcom-control-center` in HCP
- Execution: Local (via GitHub Actions or CLI)
- Provider: GitHub (~> 6.0)
- State: Encrypted, versioned, locked

### All 18 Repositories
**Python**: agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors

**Node.js**: agentic-control, otter-river-rush, otterfall, pixels-pygame-palace, rivermarsh, strata

**Go**: port-api, vault-secret-sync

**Terraform**: terraform-github-markdown, terraform-repository-automation

## Initial Setup (One-Time)

The agent needs to:

1. **Set workspace variables** in HCP Terraform Cloud:
   ```
   GITHUB_TOKEN = <CI_GITHUB_TOKEN value>
   ```

2. **Initialize Terraform** in the workspace:
   - Download GitHub provider
   - Configure HCP backend
   - Verify authentication

3. **Import existing repositories**:
   - Import all 18 repositories to Terraform state
   - Import branch protection rules
   - Verify no unintended changes

4. **Create baseline**:
   - Run initial plan to see current state
   - Apply to align any drifted configs
   - Establish clean baseline

## Monitoring

The agent monitors via:

- **Daily drift detection**: Runs at 2 AM UTC via GitHub Actions
- **PR validation**: Plans on every PR to terraform/
- **Auto-apply**: Applies on merge to main
- **Manual checks**: Via `terraform plan` in workspace

## Benefits Over Old Approach

| Old (Passive Sync) | New (Active Terraform) |
|--------------------|------------------------|
| Bash scripts in workflow | Declarative Terraform code |
| No state tracking | HCP state management |
| No drift detection | Automatic daily detection |
| Scattered in YAML | Centralized in /terraform/ |
| Manual alignment | Agent applies fixes |
| No preview | Plan before apply |
| No history | Full git + state history |

## Troubleshooting

**Agent not responding?**
- Check it has access to Terraform MCP server
- Verify TF_API_TOKEN secret is set
- Check HCP workspace isn't locked

**Changes not applying?**
- Review plan output in agent response
- Check GitHub token permissions
- Look for state lock issues in HCP

**Drift keeps recurring?**
- Identify what's changing repos outside Terraform
- Update Terraform to match reality if intentional
- Fix automation that's causing drift

## Next Steps

1. **Initialize the agent** - Run initial setup
2. **Review baseline** - Check current vs desired state
3. **Apply first run** - Align all repositories
4. **Monitor drift** - Watch for external changes
5. **Update policies** - Make changes via agent

## References

- Agent Instructions: `.github/agents/terraform-repository-manager.md`
- Terraform Config: `terraform/`
- Documentation: `docs/TERRAFORM-REPOSITORY-MANAGEMENT.md`
- HCP Workspace: https://app.terraform.io/app/jbcom/workspaces/jbcom-control-center
