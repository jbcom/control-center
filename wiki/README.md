# jbcom Control Center Wiki

Welcome to the central documentation hub for the jbcom Python library ecosystem.

## 🔄 Active Cycle

**[Cycle 001: Control Plane Activation](Active-Cycle)** - IN PROGRESS

See [PR #200](https://github.com/jbcom/jbcom-control-center/pull/200) for details.

## Quick Start

| What | Where |
|------|-------|
| **All Agent Guidelines** | [Core Guidelines](Core-Guidelines) |
| **Ecosystem Overview** | [Ecosystem](Ecosystem) |
| **Current Status** | [Active Cycle](Active-Cycle) |
| **Claude Instructions** | [Claude](Claude) |
| **Cursor Instructions** | [Cursor](Cursor) |

## Managed Packages

| Package | PyPI | Status |
|---------|------|--------|
| [extended-data-types](https://github.com/jbcom/extended-data-types) | [PyPI](https://pypi.org/project/extended-data-types/) | ✅ |
| [lifecyclelogging](https://github.com/jbcom/lifecyclelogging) | [PyPI](https://pypi.org/project/lifecyclelogging/) | ✅ |
| [directed-inputs-class](https://github.com/jbcom/directed-inputs-class) | [PyPI](https://pypi.org/project/directed-inputs-class/) | ✅ |
| [vendor-connectors](https://github.com/jbcom/vendor-connectors) | [PyPI](https://pypi.org/project/vendor-connectors/) | ✅ |

## For Agents

1. **Start here**: [Core Guidelines](Core-Guidelines)
2. **Check active work**: [Active Cycle](Active-Cycle)
3. **Understand architecture**: [Agentic Orchestration](Agentic-Orchestration)
4. **Know your tools**: [Self-Sufficiency](Self-Sufficiency)

## Repository Structure

```
jbcom-control-center/
├── packages/           # All Python packages (monorepo)
├── wiki/               # This documentation (synced to wiki)
├── .github/
│   ├── workflows/      # CI/CD and Claude workflows
│   └── cycles/         # Agentic cycle documentation
└── templates/          # Templates for managed repos
```

---

*This wiki is the single source of truth for agent and project documentation.*
