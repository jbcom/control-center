# Copilot Agent Documentation

This directory contains all documentation needed for GitHub Copilot agents to operate in this repository.

## Files

| File | Purpose |
|------|---------|
| `instructions.md` | Main agent instructions (start here) |
| `AGENTS_GUIDE.md` | Custom agent setup and usage |
| `RECOVERY_GUIDE.md` | Agent recovery procedures |
| `agents/*.agent.yaml` | Custom agent definitions |

## Quick Start for Agents

1. Read `instructions.md` first
2. Check `RECOVERY_GUIDE.md` if recovering from a failed session
3. Use custom agents via `@agent-name /command`

## Recovery Scripts

Located in `.github/scripts/recovery/` and `.cursor/scripts/`:
- `agent-recover` - Full forensic recovery
- `agent-triage-local` - Offline analysis
- `triage-pipeline` - Batch processing
- `replay_agent_session.py` (in `scripts/`) - Memory bank update

## Key Principles

1. **CalVer versioning** - `YYYY.MM.BUILD`, auto-generated
2. **Authentication** - Use `GITHUB_JBCOM_TOKEN` for jbcom repos
3. **Handoff protocol** - Document everything for next agent
4. **Recovery first** - Check for failed agent data before starting

## Links

- [Wiki](https://github.com/jbcom/jbcom-control-center/wiki)
- [Active Cycle](https://github.com/jbcom/jbcom-control-center/wiki/Active-Cycle)
- [Core Guidelines](https://github.com/jbcom/jbcom-control-center/wiki/Core-Guidelines)
