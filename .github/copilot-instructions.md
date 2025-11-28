# GitHub Copilot Instructions

> **📚 Full documentation**: `.github/copilot/instructions.md`

## Quick Rules

- **CalVer**: `YYYY.MM.BUILD` - automatic, never manual
- **Auth**: `GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>` for jbcom repos
- **NO semantic-release** - We use CalVer
- **NO git tags** - PyPI is source of truth

## Recovery from Failed Agents

When given a Cursor agent URL (`https://cursor.com/agents?selectedBcId=bc-XXXXX`):

1. Extract agent ID (`bc-XXXXX`)
2. Check `.cursor/recovery/<agent-id>/conversation.json`
3. If exists: `python scripts/replay_agent_session.py --conversation <path>`
4. If not: User must export from Cursor web UI first

## Available Scripts

| Location | Script | Purpose |
|----------|--------|---------|
| `.cursor/scripts/` | `agent-recover` | Forensic recovery |
| `.cursor/scripts/` | `agent-triage-local` | Offline triage |
| `.cursor/scripts/` | `triage-pipeline` | Batch recovery |
| `scripts/` | `replay_agent_session.py` | Memory bank update |

## Code Style

```python
# Modern type hints
def func(data: dict[str, Any]) -> list[str]: ...

# Use pathlib
from pathlib import Path

# Use extended-data-types
from extended_data_types import strtobool
```

## Agent Handoff

When ending a session:
1. Document completed work
2. Document blockers
3. Document next steps
4. Update wiki

See `.github/copilot/instructions.md` for complete documentation.
