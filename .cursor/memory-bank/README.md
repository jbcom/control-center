# Agent Memory Bank

Persistent memory for AI agents working on this repository.

## Purpose

This directory enables session continuity for AI agents (Cursor, Copilot, Claude, etc.) by providing:
- **Context preservation** across sessions
- **Progress tracking** for multi-step work
- **Decision documentation** for complex changes
- **Rule enforcement** for consistent behavior

## Files

| File | Purpose | Persistence |
|------|---------|-------------|
| `activeContext.md` | Current work focus, active PRs/branches | Update every session |
| `progress.md` | Task tracking, session logs, milestones | Append after completions |
| `agenticRules.md` | Behavior rules, authentication, workflows | Stable reference |

## Usage Pattern

### Session Start
```
1. Read activeContext.md - understand current focus
2. Read progress.md - see what's been done
3. Check GitHub issues/PRs for context
4. Continue from "Next Actions"
```

### During Work
```
1. Update progress.md after significant completions
2. Create GitHub issues for multi-step work
3. Link commits/PRs to issues
```

### Session End
```
1. Update activeContext.md with current state
2. Update "Next Actions" list
3. Commit memory-bank changes
```

## GitHub Integration

Memory-bank works alongside GitHub for tracking:

- **Issues**: Work items, bugs, features
- **Projects**: Roadmaps, milestones  
- **PRs**: Code changes linked to issues

**Active Project**: [jbcom Ecosystem Integration](https://github.com/users/jbcom/projects/2)

## Cross-Branch Persistence

This memory-bank is on `main` branch to ensure availability across all feature branches.
When working on feature branches, memory-bank updates should be:
1. Made on the feature branch
2. Included in the PR
3. Merged to main with the PR

## External Repositories

When working on external repos (terraform-modules, terraform-aws-secretsmanager):
- Check for their own memory-bank: `<repo>/memory-bank/`
- Keep notes synchronized
- Document cross-repo work in both places
