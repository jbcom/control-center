# Repository Task: albmarin/pycalver

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 1
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 1 times.

## Files Mentioned
- ci.yml
- reusable-enforce-standards.yml
- reusable-release.yml
- set_version.py

## PRs Mentioned


## Your Mission
1. Clone or access albmarin/pycalver
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view albmarin/pycalver --json name,description

# Check mentioned PRs


# Check files exist
ls -la ci.yml 2>/dev/null || echo 'Missing: ci.yml'
ls -la reusable-enforce-standards.yml 2>/dev/null || echo 'Missing: reusable-enforce-standards.yml'
ls -la reusable-release.yml 2>/dev/null || echo 'Missing: reusable-release.yml'
ls -la set_version.py 2>/dev/null || echo 'Missing: set_version.py'
```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/albmarin_pycalver/RECOVERY_REPORT.md`
