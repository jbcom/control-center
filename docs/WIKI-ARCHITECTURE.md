# Wiki-Based Documentation Architecture

## Problem

Current state has scattered documentation:
- `memory-bank/` - Agent context/memory
- `docs/` - Technical documentation
- `.ruler/` - Agent instruction sources
- `.cursor/rules/` - Cursor-specific rules
- `.github/copilot-instructions.md` - Copilot instructions
- `AGENTS.md`, `CLAUDE.md`, `.cursorrules` - Generated files

This creates:
- Duplication across files
- Synchronization overhead (ruler apply)
- No cross-repo access
- Repo pollution with markdown

## Solution

**Move ALL documentation to GitHub Wiki**, keeping only minimal pointers in repo.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB WIKI                                   │
│              jbcom/jbcom-control-center.wiki                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Memory-Bank/                                                 ││
│  │ ├── Active-Context.md    (current work focus)               ││
│  │ ├── Progress.md          (session history)                  ││
│  │ └── Recovery/            (agent recovery logs)              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Agentic-Rules/                                               ││
│  │ ├── Core-Guidelines.md   (universal agent behavior)         ││
│  │ ├── Python-Standards.md  (code style, versioning)           ││
│  │ ├── PR-Ownership.md      (PR collaboration)                 ││
│  │ ├── Ecosystem.md         (cross-repo coordination)          ││
│  │ └── Security.md          (secrets, auth)                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Agent-Instructions/                                          ││
│  │ ├── Cursor.md            (Cursor-specific extras)           ││
│  │ ├── Copilot.md           (Copilot-specific extras)          ││
│  │ └── Claude.md            (Claude Code extras)               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Documentation/                                               ││
│  │ ├── Architecture.md                                         ││
│  │ ├── Agentic-Orchestration.md                                ││
│  │ ├── MCP-Setup.md                                            ││
│  │ └── ...                                                     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ gh api / wiki CLI
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REPOSITORIES                                  │
│                                                                  │
│  jbcom-control-center/                                          │
│  ├── AGENTS.md        → "Read wiki: Core-Guidelines"            │
│  ├── CLAUDE.md        → "Read wiki: Agent-Instructions/Claude"  │
│  └── .cursor/rules/   → Points to wiki                          │
│                                                                  │
│  jbcom/extended-data-types/                                     │
│  └── AGENTS.md        → Points to control-center wiki           │
│                                                                  │
│  jbcom/vendor-connectors/                                       │
│  └── AGENTS.md        → Points to control-center wiki           │
└─────────────────────────────────────────────────────────────────┘
```

## Wiki Structure

```
Wiki/
├── Home.md                         # Entry point, navigation
│
├── Memory-Bank/
│   ├── _Sidebar.md                 # Memory bank navigation
│   ├── Active-Context.md           # Current work (updated by agents)
│   ├── Progress.md                 # Session history (append-only)
│   └── Recovery/
│       └── [session-id].md         # Recovery logs
│
├── Agentic-Rules/
│   ├── _Sidebar.md
│   ├── Core-Guidelines.md          # MUST READ FIRST
│   ├── Python-Standards.md         # CalVer, type hints, etc.
│   ├── PR-Ownership.md             # AI-to-AI collaboration
│   ├── Ecosystem.md                # Cross-repo coordination
│   ├── Security.md                 # Secrets, auth patterns
│   └── Self-Sufficiency.md         # Tooling discovery
│
├── Agent-Instructions/
│   ├── Cursor.md                   # Cursor-specific
│   ├── Copilot.md                  # Copilot-specific
│   ├── Claude.md                   # Claude Code specific
│   └── Aider.md                    # Aider-specific
│
├── Documentation/
│   ├── Architecture.md
│   ├── Agentic-Orchestration.md
│   ├── MCP-Setup.md
│   └── ...
│
└── Templates/
    ├── AGENTS.md.template          # For managed repos
    └── CLAUDE.md.template          # For managed repos
```

## Repo Files (Minimal)

### AGENTS.md (in each repo)
```markdown
# Agent Instructions

**Primary documentation**: https://github.com/jbcom/jbcom-control-center/wiki

## Quick Start
1. Read [Core Guidelines](wiki/Agentic-Rules/Core-Guidelines)
2. Check [Active Context](wiki/Memory-Bank/Active-Context)
3. Follow [Python Standards](wiki/Agentic-Rules/Python-Standards)

## This Repo
- Package: {package_name}
- PyPI: {pypi_name}
- Role: {description}

For full documentation, see the wiki.
```

### .cursor/rules/00-wiki.mdc
```markdown
---
alwaysApply: true
---
# Agent Instructions

Read the wiki for full documentation:
https://github.com/jbcom/jbcom-control-center/wiki

Key pages:
- Core Guidelines: /Agentic-Rules/Core-Guidelines
- Active Context: /Memory-Bank/Active-Context
- Python Standards: /Agentic-Rules/Python-Standards
```

## Access Patterns

### Read Wiki (Any Agent)
```bash
# Via gh CLI
gh api repos/jbcom/jbcom-control-center/wiki/pages/Memory-Bank/Active-Context

# Via wiki-cli tool
wiki-cli read "Memory-Bank/Active-Context"
```

### Write Wiki (Authorized Agents)
```bash
# Update active context
wiki-cli write "Memory-Bank/Active-Context" --content "..."

# Append to progress
wiki-cli append "Memory-Bank/Progress" --content "## Session: ..."
```

### Cross-Repo Access
```bash
# From any repo, read control-center wiki
gh api repos/jbcom/jbcom-control-center/wiki/pages/Agentic-Rules/Core-Guidelines
```

## Benefits

| Before (Repo Files) | After (Wiki) |
|---------------------|--------------|
| Scattered across dirs | Single location |
| Ruler concatenation | Direct access |
| Repo-specific only | Cross-repo shared |
| Git commits for updates | Wiki API updates |
| Bloated repo | Clean repo |
| Manual sync | Live updates |

## Migration Plan

1. **Enable wiki** for jbcom-control-center
2. **Create wiki-cli** tooling
3. **Migrate content** from repo to wiki
4. **Update repos** to point to wiki
5. **Delete old files** from repo
6. **Remove ruler** dependency

## Implementation Files

- `.cursor/scripts/wiki-cli` - Wiki read/write CLI
- `.github/workflows/wiki-sync.yml` - Sync workflow
- `.github/actions/wiki-read/` - Read wiki action
- `.github/actions/wiki-write/` - Write wiki action
