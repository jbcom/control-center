# jbcom Control Center Wiki

Central documentation hub for the jbcom Python library ecosystem.

## Quick Navigation

### 📋 Memory Bank
- [[Memory-Bank-Active-Context|Active Context]] - Current work focus
- [[Memory-Bank-Progress|Progress]] - Session history & completed tasks
- [[Memory-Bank-Agentic-Rules|Agentic Rules]] - Core agent behavior rules

### 📜 Agentic Rules  
- [[Agentic-Rules-Core-Guidelines|Core Guidelines]] - **MUST READ FIRST** - CalVer, releases, PR workflow
- [[Agentic-Rules-Python-Standards|Python Standards]] - Type hints, docstrings, code style
- [[Agentic-Rules-PR-Ownership|PR Ownership]] - AI-to-AI collaboration protocol
- [[Agentic-Rules-Ecosystem|Ecosystem]] - Cross-repo coordination & packages
- [[Agentic-Rules-Self-Sufficiency|Self-Sufficiency]] - Tool discovery & environment
- [[Agentic-Rules-Environment-Setup|Environment Setup]] - Docker, dependencies, tools

### 🤖 Agent Instructions
- [[Agent-Instructions-Cursor|Cursor]] - Background agent modes, workflows
- [[Agent-Instructions-Copilot|GitHub Copilot]] - Quick patterns, code style
- [[Agent-Instructions-Claude|Claude Code]] - Commands, wiki access

### 📚 Documentation
- [[Documentation-Architecture|Architecture]] - System structure
- [[Documentation-Agentic-Orchestration|Agentic Orchestration]] - Cycle-based coordination
- [[Documentation-Agent-Handoff|Agent Handoff]] - Session transfer protocol
- [[Documentation-Cursor-Management|Cursor Management]] - Background agent ops
- [[Documentation-Diff-Recovery|Diff Recovery]] - Session recovery procedures
- [[Documentation-MCP-Setup|MCP Setup]] - Model Context Protocol
- [[Documentation-MCP-Proxy-Setup|MCP Proxy Setup]] - HTTP bridge
- [[Documentation-MCP-Proxy-Strategy|MCP Proxy Strategy]] - Architecture decisions
- [[Documentation-Multi-AI-Review|Multi-AI Review]] - Coordinated PR reviews
- [[Documentation-Wiki-Architecture|Wiki Architecture]] - This wiki's design

### 🔄 Recovery
- [[Recovery-2025-11-27|Nov 27 Recovery]] - Recent recovery session
- [[Recovery-Delegation|Delegation]] - Task delegation records
- [[Recovery-Replay|Replay]] - Session replay logs

---

## Ecosystem Packages

| Package | PyPI | GitHub | Status |
|---------|------|--------|--------|
| extended-data-types | [PyPI](https://pypi.org/project/extended-data-types/) | [Repo](https://github.com/jbcom/extended-data-types) | Foundation |
| lifecyclelogging | [PyPI](https://pypi.org/project/lifecyclelogging/) | [Repo](https://github.com/jbcom/lifecyclelogging) | Logging |
| vendor-connectors | [PyPI](https://pypi.org/project/vendor-connectors/) | [Repo](https://github.com/jbcom/vendor-connectors) | Connectors |
| directed-inputs-class | [PyPI](https://pypi.org/project/directed-inputs-class/) | [Repo](https://github.com/jbcom/directed-inputs-class) | Inputs |

## Quick Access

```bash
# Read wiki page
wiki-cli read "Memory-Bank-Active-Context"

# Update progress
wiki-cli append "Memory-Bank-Progress" "## Session update"

# List all pages
wiki-cli list
```
