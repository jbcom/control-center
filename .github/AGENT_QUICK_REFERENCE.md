# Agent Quick Reference Card

## Copilot Agents (GitHub Copilot Chat)

### @ecosystem-manager
```
/ecosystem-status          - Overall health check
/repo-status <name>        - Detailed repo info
/check-ci                  - CI status across all repos
```

### @ci-deployer
```
/deploy-ci <repo>          - Deploy CI to repo
/check-workflows           - Audit all workflows
/update-workflow <repo>    - Update existing workflow
/standardize <repo>        - Bring to standard CI
```

### @dependency-coordinator
```
/check-deps [scope]        - Check for updates
/update-deps <repo>        - Update dependencies
/cascade-update <package>  - Update across dependents
/dep-graph                 - Show dependency graph
```

### @release-coordinator
```
/release-status            - Current versions
/pending-releases          - What needs releasing
/plan-release <repo>       - Plan with dependencies
/release <repo>            - Trigger release
/verify-release <repo>     - Verify success
```

### @game-dev
```
/game-status [repo]        - Game repos status
/list-games [language]     - List by language
/check-integrations <repo> - List integrations
/setup-game <repo>         - Setup instructions
```

### @vendor-connectors-consolidator
```
/scan-integrations         - Find integration code
/consolidate <connector>   - Consolidate connector
/extract <repo> <path>     - Extract code
```

---

## Cursor Agents (Cursor IDE)

Same capabilities, invoked by describing the task:

- **Ecosystem management:** "Show me the ecosystem status"
- **CI/CD:** "Deploy CI workflow to the repo"
- **Dependencies:** "Check for dependency updates"
- **Releases:** "Plan a release for extended-data-types"
- **Games:** "List all TypeScript game repos"
- **Consolidation:** "Scan for Meshy integrations"
- **Environment:** "Debug the Dockerfile build issues"

---

## MCP Servers Available (All Agents)

**Core:** filesystem, git, github, memory  
**Agents:** conport, cursor_agents, aider  
**AWS:** aws-iac, aws-serverless, aws-api, aws-cdk, aws-cfn, aws-support, aws-pricing, billing-cost-management, aws-documentation  
**Docs:** python-stdlib

---

## Quick Commands

```bash
# Update all agent configs
ruler apply

# Validate Copilot agents
python3 -c "import yaml; yaml.safe_load(open('.github/copilot/agents/ecosystem-manager.agent.yaml'))"

# Check MCP config
cat .cursor/mcp.json | jq '.mcpServers | keys'

# Build Cursor environment
docker build -t jbcom-cursor-env -f .cursor/Dockerfile .
```

---

**Docs:**
- `.github/copilot/AGENTS_GUIDE.md`
- `.cursor/MCP_CONFIGURATION_GUIDE.md`
- `.cursor/DOCKERFILE_ANALYSIS.md`
- `AGENT_FIXES_SUMMARY.md`
