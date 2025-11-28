# Active Context

## Current Focus
- GitHub Actions workflows for agent-driven development
- Moving agent orchestration OUTSIDE single background agent
- Issue triage and project management automation

## Active Work

### GitHub Actions Agent Workflows (PR #189 - OPEN)
- `agent-pr-review.yml` - Review on PR events
- `agent-post-merge.yml` - Follow-up on main merges
- `agent-issue-triage.yml` - Auto-label, /agent commands, cross-repo linking
- `agent-project-management.yml` - Project sync, stale management, reports
- `spawn-cursor-agent` reusable action

Features:
- Auto-classify and label issues (bug, enhancement, security, ci-cd, package-specific)
- Auto-add issues to GitHub project board
- `/agent` commands in issue comments:
  - `/agent review` - Request detailed analysis
  - `/agent fix` - Request fix PR
  - `/agent investigate` - Deep investigation
  - `/agent close` - Verify can close
  - `/agent help` - Show commands
- Cross-repo issue linking across ecosystem
- Weekly stale issue management
- Ecosystem status report generation
- Maintenance agent spawning

### Prior PRs (MERGED)
- ✅ PR #185: aider CLI with Python 3.12 workaround
- ✅ PR #186: Automated agent triage pipeline
- ✅ PR #188: Agentic rule updates (tooling documentation)

### Agent Recovery (COMPLETED)
- Session `bc-c1254c3f-ea3a-43a9-a958-13e921226f5d`: 287 messages recovered
- Artifacts extracted: 22 PRs, 11 repos, 1 branch, 83 files
- Tasks delegated via GitHub issues (#207, #8, #42)

## Next Actions
1. Wait for PR #189 review/merge
2. Monitor workflows after merge
3. Test `/agent` commands on a new issue

## Open PRs
| Repo | PR | Status | Description |
|------|-----|--------|-------------|
| jbcom/jbcom-control-center | #189 | Open | GitHub Actions agent workflows |
| FlipsideCrypto/terraform-modules | #203 | Ready to merge | vendor-connectors integration |

## Open Issues (Agent Tasks)
| Repo | Issue | Status | Description |
|------|-------|--------|-------------|
| jbcom/jbcom-control-center | #183 | Todo | Enterprise SOPS secrets sync |
| jbcom/vendor-connectors | #8 | Todo | Fix CI/PyPI publish |
| jbcom/lifecyclelogging | #42 | Todo | Fix CodeQL/CI workflow |
| FlipsideCrypto/terraform-modules | #207 | Todo | Merge PR #203 |

## Holding PR
- PR #182: `agent/rebalance-github-projects-issues-20251127-224414`
- Purpose: Keep background agent session alive during multi-merge workflow
