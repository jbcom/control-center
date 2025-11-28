# Agent Instructions

> **📚 Full documentation**: https://github.com/jbcom/jbcom-control-center/wiki

## Quick Start

1. **Read Core Guidelines**: [Agentic-Rules-Core-Guidelines](https://github.com/jbcom/jbcom-control-center/wiki/Agentic-Rules-Core-Guidelines)
2. **Check Active Context**: [Memory-Bank-Active-Context](https://github.com/jbcom/jbcom-control-center/wiki/Memory-Bank-Active-Context)
3. **Follow Python Standards**: [Agentic-Rules-Python-Standards](https://github.com/jbcom/jbcom-control-center/wiki/Agentic-Rules-Python-Standards)

## Critical Rules

- **CalVer versioning** - `YYYY.MM.BUILD`, never manual
- **Read wiki first** - Before making decisions
- **Use GITHUB_JBCOM_TOKEN** - For all jbcom operations

## 🤝 Counterparty: FSC Control Center

jbcom has an enterprise counterparty: **FSC Control Center** (FlipsideCrypto/fsc-control-center)

### Recognizing FSC Interactions
- Issues: `🤖 FSC Feature Request:` or `🔄 Handoff from FSC:`
- PRs: Branch `feat/fsc-*` or `fix/fsc-*`
- Body contains: `From: FSC Control Center`

### FSC Uses These Packages
- extended-data-types
- lifecyclelogging
- vendor-connectors

### Full Documentation
- [FSC Coordination Guide](docs/FSC-COUNTERPARTY-COORDINATION.md)
- [FSC Wiki Page](https://github.com/jbcom/jbcom-control-center/wiki/FSC-Control-Center)

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
- [FSC Coordination](https://github.com/jbcom/jbcom-control-center/wiki/FSC-Control-Center)
