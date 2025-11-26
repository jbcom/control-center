# Memory Bank

This directory contains the agent's persistent memory across sessions.

## Purpose

AI agents working on this project can maintain context across sessions by reading and updating these files. This enables:

- **Continuity**: Pick up exactly where the last session left off
- **Progress Tracking**: Know what's done and what's remaining
- **Context Preservation**: Understand decisions and rationale
- **Rule Enforcement**: Consistent behavior across sessions

## Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `activeContext.md` | Current work focus, active branches, immediate next steps | Every session |
| `progress.md` | Task log, milestones, issues resolved | After significant work |
| `agenticRules.md` | Behavior rules, workflows, authentication | Rarely (stable reference) |
| `README.md` | This file explaining the system | When structure changes |

## Usage Pattern

### At Session Start
```
1. Read activeContext.md to understand current focus
2. Read progress.md to see what's been done
3. Check GitHub issues for tracking context
4. Continue from "Next Actions" list
```

### During Session
```
1. Update progress.md after completing tasks
2. Create GitHub issues for multi-step work
3. Note decisions in progress.md "Technical Decisions Log"
```

### At Session End
```
1. Update activeContext.md with current state
2. Update progress.md with session log
3. Push changes to branches
4. Update "Next Actions" for next session
```

## Integration with External Repos

When working on external repos (terraform-modules, terraform-aws-secretsmanager), check for their own memory-bank:

```
/workspace/external/<repo>/memory-bank/
```

Keep both the control-center memory-bank and the external repo's memory-bank in sync for cross-repo work.

## GitHub Integration

The memory-bank works alongside GitHub issues:

1. **Issues** track work items with GitHub's native UI
2. **Memory-bank** provides detailed technical context
3. **PRs** link to issues for automated tracking

### Creating Issues from Memory-Bank
When starting new work:
```bash
gh issue create --title "..." --body "See memory-bank/progress.md for context"
```

### Linking Memory-Bank to Issues
In progress.md, reference issues:
```markdown
### GitHub Issues Created
- [x] #200: Integrate vendor-connectors PyPI package
- [ ] #201: Add deepmerge to extended-data-types
```

## Best Practices

### Keep Context Relevant
- Remove stale information
- Archive completed work to progress.md
- Keep activeContext.md focused on current work

### Be Specific
- Include file paths
- Include branch names
- Include issue numbers
- Include exact error messages

### Use Checklists
- Task lists with [ ] and [x] for tracking
- Easy to scan and update
- Clear completion status

### Document Decisions
- Why, not just what
- Alternatives considered
- Rationale for choices

## Template: New Session Checklist

```markdown
## Session Start Checklist
- [ ] Read memory-bank/activeContext.md
- [ ] Read memory-bank/progress.md
- [ ] Check open issues: `gh issue list`
- [ ] Check open PRs: `gh pr list`
- [ ] Review CI status: `gh run list --limit 5`
- [ ] Identify next action from "Next Actions" list
```

## Template: Session End Checklist

```markdown
## Session End Checklist
- [ ] Push uncommitted changes to branches
- [ ] Update progress.md with session log
- [ ] Update activeContext.md "Next Actions"
- [ ] Create issues for unfinished multi-step work
- [ ] Close holding PRs if work complete
```
