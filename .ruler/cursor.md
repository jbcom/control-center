# Cursor-Specific Agent Configuration

Configuration for Cursor AI agents in jbcom-control-center.

## 🔑 Authentication

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
```

The default `GH_TOKEN` does NOT have jbcom access.

## 🚨 Long-Running PR Workflow (Hold-Open Pattern)

When managing **multiple merges to main** and **multiple CI runs**, use the hold-open pattern:

### The Problem
When a background agent creates a PR and merges it, the session closes because the branch is deleted.

### The Solution: Holding PR + Interim PRs

**1. Create Holding PR (keeps session alive):**
```bash
git checkout -b agent/holding-pr-for-<task>-$(date +%Y%m%d-%H%M%S)
echo "# Agent Session" >> .cursor/agents/session-notes.md
git commit -m "Agent holding PR for <task>"
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --draft \
  --title "[HOLDING] Agent session for <task>" \
  --body "Keeps session alive. DO NOT MERGE until work complete."
```

**2. Create Interim PRs (for actual fixes):**
```bash
git checkout main && git pull
git checkout -b fix/<specific-issue>
# Make the fix
git commit -m "fix(scope): specific issue"
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create
# After CI passes
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch
```

**3. When Done:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr close <HOLDING_PR_NUM>
```

### Rules for Hold-Open PRs
- Use `--draft` to avoid triggering AI reviewers
- Title with `[HOLDING]` prefix
- NEVER merge the holding PR until all work complete
- Create NEW interim branches from updated main for each fix

## 🛠️ cursor-fleet Tooling

The fleet tooling is in `packages/cursor-fleet/`. Build and use:

```bash
# Build
cd /workspace/packages/cursor-fleet && npm run build

# List agents
node dist/cli.js list

# Get agent status
node dist/cli.js status <agent-id>

# Replay/recover conversation
node dist/cli.js replay <agent-id> -o /workspace/.cursor/recovery/<agent-id> -v

# Spawn new agent
node dist/cli.js spawn --repo jbcom/vendor-connectors --task "Fix CI"

# Send followup
node dist/cli.js followup <agent-id> "Please check PR feedback"
```

### Replay Features
- Fetches full conversation via Cursor API
- Splits into batches (10 messages per file)
- Creates INDEX.md for navigation
- Extracts completed/outstanding tasks
- Archives to specified directory

## Background Agent Modes

### Code Review Mode
When reviewing PRs:
- Focus on logic and correctness
- Check type safety
- Verify test coverage
- Look for security issues

### Maintenance Mode
For routine tasks:
- Update dependencies
- Fix linting issues
- Improve documentation
- Keep it simple

### Ecosystem Coordination Mode
When working across packages:
- Work in dependency order (EDT → LL → DIC → VC)
- Test each package independently
- Create PRs for each change
- Ensure CI passes before merge

## Error Handling

### CI Failures
1. Read full error output
2. Identify root cause
3. Fix the issue
4. Push fix
5. Verify CI passes

### Type Check Errors
1. Read the specific error
2. Fix with proper type hints
3. Don't use `type: ignore` unless necessary

### Test Failures
1. Read test output carefully
2. Identify which test failed
3. Fix the code or the test
4. Run full test suite

## Code Style

### Python Style
- Modern type hints: `list[]`, `dict[]`, not `List[]`, `Dict[]`
- Prefer pathlib over os.path
- Use context managers for resources
- Keep functions focused and small
- Docstrings for public APIs

### Commit Messages
Use conventional commits for releases to work:
```bash
feat(vc): add new connector       # Minor bump
fix(dic): resolve bug             # Patch bump
docs: update README               # No release
```

## Communication Style

### With User
- Be concise
- Highlight important info
- Use formatting for clarity
- Show progress on long tasks

### In Code Comments
- Explain why, not what
- Link to issues/PRs for context
- Keep them brief

---

**Cursor Version:** Compatible with latest Cursor AI
**Last Updated:** 2025-11-30
