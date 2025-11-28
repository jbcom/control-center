# Active Context

## Current Focus
- Consolidating agentic documentation for Copilot access
- Fixing recovery tooling documentation gaps

## Recent Work (2025-11-28)
- Moved all agentic documentation to `.github/copilot/`
- Created `RECOVERY_GUIDE.md` with step-by-step recovery instructions
- Updated `instructions.md` with comprehensive agent instructions
- Copied recovery scripts to `.github/scripts/recovery/`
- Created `memory-bank/` directory structure

## Active Cycle
- **Cycle 001**: Control Plane Activation
- **PR**: #200 (MERGED)
- **Status**: In Progress

## Next Actions
1. User exports `bc-7d1997bf-56b0-4e1f-9f6d-2ba4382d3ac4` conversation from Cursor web UI
2. Run `python scripts/replay_agent_session.py` on exported conversation
3. Create handoff document from findings
4. Continue Cycle 001 Phase 1 tasks

## Key Documentation Locations
- `.github/copilot/instructions.md` - Main agent instructions
- `.github/copilot/RECOVERY_GUIDE.md` - Recovery procedures
- `.github/copilot/AGENTS_GUIDE.md` - Custom agent setup
- `wiki/` - Full wiki documentation
