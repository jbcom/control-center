# Global Memory Bank

This directory is the single source of truth for agent memory across jbcom-control-center. All agents (interactive and background) should read from and write to these files to maintain a coherent chronology.

Background agents are responsible for creating the directory structure if it is missing during handoff; the Docker image and runtime bootstrap no longer pre-create any of these paths.

- `activeContext.md` — current focus and next actions
- `progress.md` — chronological log of completed and pending work
- `agenticRules.md` — stable behavioral expectations for every agent
- `recovery/` — transcripts and diagnostics recovered from failed or background agents

## Merged memory-bank locations

The historical `.cursor/memory-bank` content is merged here to avoid symlinks and split states. Compatibility copies are kept under `.cursor/memory-bank/` by running `python scripts/replay_agent_session.py`, which mirrors updates after each replay.

## Automated session replay

Use `scripts/replay_agent_session.py` to ingest recovered Cursor background-agent transcripts and populate the memory bank:

```bash
python scripts/replay_agent_session.py \
  --conversation .cursor/recovery/<agent-id>/conversation.json \
  --tasks-dir .cursor/recovery/<agent-id>/tasks
```

The script will:
- Archive a condensed transcript to `memory-bank/recovery/<agent-id>-replay.md`
- Append a replay entry to `progress.md`
- Refresh `activeContext.md` with the current focus and next actions
- Generate a delegation prompt for MCP-aware CLIs (Codex, Claude code aider, etc.)
- Mirror the updated files into `.cursor/memory-bank/` for backward compatibility

If you want AI-authored summaries, pass `--ai-command "codex summarize --stdin"` (or another CLI that reads from stdin and writes the summary to stdout).
