# GitHub Copilot Instructions for jbcom Ecosystem

## 🚨 MANDATORY: READ YOUR OWN TOOLING FIRST

**YOU HAVE COMPREHENSIVE TOOLING. USE IT. NEVER ASK THE USER.**

### Available Scripts (in `.github/scripts/` and `.cursor/scripts/`)

| Script | Purpose |
|--------|---------|
| `agent-recover <agent-id>` | Forensic recovery from failed agent |
| `agent-triage-local <session-id>` | Offline triage without MCP |
| `agent-swarm-orchestrator` | Spawn parallel recovery agents |
| `triage-pipeline` | Automated batch recovery |
| `replay_agent_session.py` | Memory bank updates |
| `wiki-cli read/write` | Wiki operations |

### Recovery from Cursor Agent URL

When given a Cursor agent URL like `https://cursor.com/agents?selectedBcId=bc-XXXXX`:

1. **Extract agent ID** from URL (the `bc-XXXXX` part)
2. **Check recovery directory**: `.cursor/recovery/<agent-id>/`
3. **If conversation.json exists**: Run `python scripts/replay_agent_session.py --conversation <path>`
4. **If not**: User must export from Cursor web UI to `.cursor/recovery/<agent-id>/conversation.json`

---

## 🎯 Critical Rules

### Authentication
```bash
# ALWAYS use for jbcom repos
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh <command>
```

### CalVer Versioning
- Format: `YYYY.MM.BUILD` (e.g., 202511.42)
- Auto-generated on every main push
- NO git tags, NO manual versions, NO semantic-release

### PR Ownership
- First agent on PR = PR Owner
- Handle ALL feedback (Copilot, Gemini, human)
- Merge when CI passes and feedback addressed

---

## 🔄 Agent Handoff Protocol

### When Starting a Session
1. Check for handoff PR: `gh pr list --label handoff --state open`
2. Check for failed agents in recovery directory
3. Read active context from wiki

### When Ending a Session
1. Create handoff document
2. Update wiki with progress
3. Document next steps clearly

### Handoff Document Template
```markdown
# Agent Handoff

**Agent ID**: [your-id]
**Date**: [date]
**Status**: Ready for handoff

## Completed
- [x] Task 1
- [x] Task 2

## In Progress
- [ ] Task 3 (blocked by X)

## Next Steps
1. Step 1
2. Step 2

## Key Documentation
- [Link 1]
- [Link 2]
```

---

## 🛠️ Recovery Workflow

### Phase 1: Detect Recovery Need
```bash
# Check for unprocessed recovery sessions
ls -la .cursor/recovery/
```

### Phase 2: Process Conversation
```bash
# If conversation.json exists
python scripts/replay_agent_session.py \
  --conversation .cursor/recovery/<agent-id>/conversation.json \
  --session-label "<descriptive-name>"
```

### Phase 3: Extract Artifacts
The replay script automatically extracts:
- PRs mentioned
- Branches mentioned
- Files mentioned
- Key events timeline

### Phase 4: Generate Handoff
Based on extracted artifacts, create actionable next steps.

---

## 📦 Ecosystem Overview

### Managed Packages
| Package | Role | PyPI |
|---------|------|------|
| extended-data-types | Foundation | ✅ 202511.2 |
| lifecyclelogging | Logging | ✅ 202511.2 |
| directed-inputs-class | Input validation | ✅ 202511.2 |
| vendor-connectors | Cloud integrations | ✅ 202511.2 |

### Dependency Order
```
extended-data-types (FOUNDATION)
├── lifecyclelogging
├── directed-inputs-class
└── vendor-connectors
```

---

## 🤖 Custom Copilot Agents

### @ecosystem-manager
```
/ecosystem-status    - Full health report
/repo-status <name>  - Detailed repo status
/check-ci            - CI status across all repos
```

### @ci-deployer
```
/deploy-ci <repo>    - Deploy CI to repo
/check-workflows     - Audit all workflows
/standardize <repo>  - Bring to standard
```

### @dependency-coordinator
```
/check-deps          - Check for updates
/cascade-update      - Update across dependents
/dep-graph           - Show dependencies
```

### @release-coordinator
```
/release-status      - Current versions
/plan-release <repo> - Plan with dependencies
/release <repo>      - Trigger release
```

### @vendor-connectors-consolidator
```
/scan-integrations   - Find integration code
/consolidate <name>  - Consolidate connector
```

### @game-dev
```
/game-status         - All game repos status
/list-games          - List by language
```

---

## ❌ Never Suggest

- semantic-release for Python
- Git tags for versioning
- Manual version management
- GitHub releases automation
- Complex conditional release logic

---

## ✅ Always Do

- Use CalVer (YYYY.MM.BUILD)
- Use uv for Python package management
- Use unified ci.yml workflow
- Update wiki after completing work
- Create handoff documents

---

## 🔗 Key Documentation Links

- [Wiki Home](https://github.com/jbcom/jbcom-control-center/wiki)
- [Core Guidelines](https://github.com/jbcom/jbcom-control-center/wiki/Core-Guidelines)
- [Agent Handoff](https://github.com/jbcom/jbcom-control-center/wiki/Agent-Handoff)
- [Recovery Replay](https://github.com/jbcom/jbcom-control-center/wiki/Recovery-Replay)
- [Diff Recovery](https://github.com/jbcom/jbcom-control-center/wiki/Diff-Recovery)

---

## 📁 Key File Locations

### Agent Configuration
- `.github/copilot/agents/*.agent.yaml` - Copilot agent definitions
- `.cursor/agents/*.md` - Cursor agent definitions
- `.cursor/rules/*.mdc` - Cursor rules

### Recovery & Handoff
- `.cursor/recovery/<agent-id>/` - Recovery artifacts per agent
- `.cursor/scripts/` - Recovery and triage scripts
- `scripts/replay_agent_session.py` - Conversation replay tool

### CI/CD
- `.github/workflows/ci.yml` - Unified CI workflow
- `.github/scripts/set_version.py` - CalVer version script

---

## 🆘 If Stuck

1. Check wiki for documentation
2. Check `.cursor/` for tooling
3. Check existing recovery sessions for patterns
4. Document what was tried
5. Create clear handoff for next agent

---

**Last Updated**: 2025-11-28
**Status**: Production
