# Active Context - jbcom Control Center

## Current Status: SURFACE SCOPE CLARIFICATION EPIC IN PROGRESS

Owning the resolution of muddled scope and boundaries across the agentic ecosystem.

### Root Issue

[PR #7 Comment](https://github.com/jbcom/agentic-control/pull/7#issuecomment-3621528331) flagged that:
- `agentic-control` has vendor-specific code (cursor-api.ts, Claude SDK) mixed with protocols
- `vendor-connectors` is missing Cursor and Anthropic connectors
- No clear separation between vendor implementations and protocols

### Issues & PRs

| Repository | Issue/PR | Purpose | Status |
|------------|----------|---------|--------|
| `jbcom-control-center` | [#340](https://github.com/jbcom/jbcom-control-center/issues/340) | EPIC: Master tracking | 🟡 In Progress |
| `vendor-connectors` | [#15](https://github.com/jbcom/vendor-connectors/issues/15) | Cursor + Anthropic connectors | 🟢 PR Created |
| `vendor-connectors` | [PR #16](https://github.com/jbcom/vendor-connectors/pull/16) | Implementation PR | 🟡 In Review |
| `agentic-control` | [#8](https://github.com/jbcom/agentic-control/issues/8) | Scope clarification refactor | 🔴 Not Started |

### Project Tracking

All issues in [jbcom Ecosystem Integration Project](https://github.com/users/jbcom/projects/2)

### Target Architecture

```
vendor-connectors (Python)
├── cursor/          # Port from agentic-control/src/fleet/cursor-api.ts
├── anthropic/       # Wrap @anthropic-ai/claude-agent-sdk
└── [existing: aws, github, google, slack, vault, zoom]

agentic-control (Node.js) - REFACTORED
├── core/           # Protocols and types (keep)
├── fleet/          # Fleet protocols - vendor-agnostic (refactor)
├── providers/      # NEW: Uses vendor-connectors
└── [triage, handoff, github - keep]

agentic-crew (Python) - NEW REPO
├── crewai/         # Move from agentic-control/python/
└── bridge/         # Protocol bridge to agentic-control
```

### Implementation Phases

1. **Phase 1**: Vendor Connectors (Cursor + Anthropic) - Week 1
2. **Phase 2**: Create agentic-crew repo - Week 1-2
3. **Phase 3**: Refactor agentic-control - Week 2-3
4. **Phase 4**: Documentation & Integration - Week 3-4

## For Next Agent

1. **Continue Phase 1**: Create Cursor connector in vendor-connectors
   - Port `cursor-api.ts` logic to Python
   - Full API coverage (list agents, launch, followup, etc.)
   - Input validation and SSRF protection

2. **Then**: Create Anthropic connector
   - Wrap Claude Agent SDK
   - Sandbox execution mode

3. **Reference**: See issue details in linked GitHub issues

## Key Files

- Epic: https://github.com/jbcom/jbcom-control-center/issues/340
- Original issue: https://github.com/jbcom/agentic-control/pull/7#issuecomment-3621528331
- Source to port: `agentic-control/src/fleet/cursor-api.ts` (~300 lines)

---
*Updated: 2025-12-07*
