# Global Memory Bank

This directory is the single source of truth for agent memory across jbcom-control-center. All agents (interactive and background) should read from and write to these files to maintain a coherent chronology.

Background agents are responsible for creating the directory structure if it is missing during handoff; the Docker image and runtime bootstrap no longer pre-create any of these paths.

- `activeContext.md` — current focus and next actions
- `progress.md` — chronological log of completed and pending work
- `recovery/` — transcripts and diagnostics recovered from failed or background agents

If a process mounts a workspace without these files, create them here instead of under `.cursor/` so every agent shares the same state.
