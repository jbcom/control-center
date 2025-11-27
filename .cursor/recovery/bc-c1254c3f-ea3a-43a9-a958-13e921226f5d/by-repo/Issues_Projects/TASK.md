# Repository Task: Issues/Projects

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 1
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 1 times.

## Files Mentioned
- agenticRules.md

## PRs Mentioned


## Your Mission
1. Clone or access Issues/Projects
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view Issues/Projects --json name,description

# Check mentioned PRs


# Check files exist
ls -la agenticRules.md 2>/dev/null || echo 'Missing: agenticRules.md'
```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/Issues_Projects/RECOVERY_REPORT.md`
