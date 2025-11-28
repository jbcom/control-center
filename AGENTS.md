# Agent Instructions

> **📚 Full documentation**: https://github.com/jbcom/jbcom-control-center/wiki

## 🚨 FSC Counterparty Awareness

**If you were spawned by FSC Control Center**, you are part of a fleet coordination:

1. **Parse your task context** - FSC will provide agent IDs to notify
2. **Decompose and spawn** - Use fleet-manager.sh to delegate to jbcom repos
3. **Notify FSC agents directly** - Use `addFollowup` when releases complete
4. **Report to FSC control manager** - Summary when done

See [docs/FSC-FLEET-COORDINATION.md](docs/FSC-FLEET-COORDINATION.md) for full protocol.

### Quick Fleet Commands

```bash
# Spawn agent in jbcom repo
/workspace/scripts/fleet-manager.sh spawn https://github.com/jbcom/vendor-connectors "Release 202511.7" main

# Notify FSC agent
/workspace/scripts/fleet-manager.sh followup bc-xxxxx "✅ Package released"

# List all agents
/workspace/scripts/fleet-manager.sh list
```

---

## Quick Start

1. **Read Core Guidelines**: [Agentic-Rules-Core-Guidelines](https://github.com/jbcom/jbcom-control-center/wiki/Agentic-Rules-Core-Guidelines)
2. **Check Active Context**: [Memory-Bank-Active-Context](https://github.com/jbcom/jbcom-control-center/wiki/Memory-Bank-Active-Context)
3. **Follow Python Standards**: [Agentic-Rules-Python-Standards](https://github.com/jbcom/jbcom-control-center/wiki/Agentic-Rules-Python-Standards)
4. **If spawned by FSC**: [FSC Fleet Coordination](docs/FSC-FLEET-COORDINATION.md)

## Critical Rules

- **CalVer versioning** - `YYYY.MM.BUILD`, never manual
- **Read wiki first** - Before making decisions
- **Use GITHUB_JBCOM_TOKEN** - For all jbcom operations
- **If from FSC** - Notify FSC agents when work completes

## Wiki Access

```bash
# Read current context
wiki-cli read "Memory-Bank-Active-Context"

# Update progress
wiki-cli append "Memory-Bank-Progress" "## Session update"
```

## Links

- [Wiki Home](https://github.com/jbcom/jbcom-control-center/wiki)
- [Active Context](https://github.com/jbcom/jbcom-control-center/wiki/Memory-Bank-Active-Context)
- [Progress](https://github.com/jbcom/jbcom-control-center/wiki/Memory-Bank-Progress)
- [Core Guidelines](https://github.com/jbcom/jbcom-control-center/wiki/Agentic-Rules-Core-Guidelines)
