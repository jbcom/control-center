# Active Context

## Current Focus
Cursor background agent reliability, MCP proxy health, and codex instruction coverage without clashing with workspace bootstrap logic.

## Active Work

### Background Agent MCP Bridge Alignment
- Enabled codex agent coverage in Ruler and regenerated instruction artifacts for all agents.
- Shifted runtime bootstrap to avoid pre-creating workspace directories during image build while still linking MCP bridge wrappers after mount time.
- Centralized the repository memory bank under `memory-bank/` with a `recovery/` area that all agents can rely on, replacing scattered `.cursor` paths.
- Adjusted the bootstrap flow to leave log and memory-bank directory creation to background agents while still wiring the symlink when the global memory bank already exists.

### Memory Recovery
- Pulled the final 15 messages from failed agent `bc-c1254c3f-ea3a-43a9-a958-13e921226f5d` into the global `memory-bank/recovery/` folder to reconstruct the last 24 hours of activity.

---

## GitHub Tracking
- Focused on jbcom-control-center background agent stability (no new external PRs opened in this session).

---

## Next Actions
1. Run `/usr/local/bin/bootstrap-cursor-runtime.sh` after mounting the workspace to link MCP bridge wrappers and ensure global memory bank symlinks are in place.
2. Start `process-compose` and confirm `cursor-agent-manager` plus MCP proxies stay healthy with logs writing under `./logs` (created at runtime by agents as needed).
3. Resume enterprise secrets sync work captured in recovered agent logs once background services are stable.
