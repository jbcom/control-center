# Active Context - jbcom Control Center

## Current Status: AGENTIC-CREW PREPARATION

Prepared comprehensive draft for `jbcom/agentic-crew` repository. **Blocked by** jbcom/vendor-connectors#17.

### What Was Done

1. **Studied reference implementations**
   - `jbcom/otterfall/.crewai` - YAML-based crew definitions with knowledge
   - `jbcom/agentic-control/python` - Python @CrewBase classes + Flows

2. **Drafted repository structure** (`docs/AGENTIC-CREW-DRAFT.md`)
   - Full package layout with crews/, tools/, server/, cli/
   - Dual-mode operation design (standalone, registered, hybrid)
   - Tool integration with vendor-connectors.ai.tools
   - HTTP server for agentic-control fleet registration

3. **Designed core abstractions**
   - `AgenticCrew` client with operation modes
   - `TriageCrew`, `ReviewCrew`, `OpsCrew` definitions
   - FastAPI server for task delegation

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Three modes (standalone/registered/hybrid) | Flexibility for local dev vs fleet orchestration |
| FastAPI server | Receives tasks from agentic-control |
| vendor-connectors.ai.tools | Single tool source, LangChain-compatible |
| @CrewBase pattern | Consistent with agentic-control/python |

### Blocked By

- **jbcom/vendor-connectors#17** - AI sub-package needed for tools

## For Next Agent

1. **When vendor-connectors#17 merges**: Create the repository using the draft
2. **Reference draft**: `/workspace/docs/AGENTIC-CREW-DRAFT.md`
3. **PR to update**: jbcom/jbcom-control-center#361

## Key Files

- `/workspace/docs/AGENTIC-CREW-DRAFT.md` - Complete repository design
- Draft includes: pyproject.toml, crew implementations, server code

---
*Updated: 2025-12-07*
