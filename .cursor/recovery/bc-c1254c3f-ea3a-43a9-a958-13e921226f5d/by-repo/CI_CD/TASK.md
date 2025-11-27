# Repository Task: CI/CD

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 5
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 5 times.

## Files Mentioned
- .cursor/agents/jbcom-ecosystem-manager.md
- .github/copilot-instructions.md
- .github/workflows/ci.yml
- AGENTS.md
- README.md
- activeContext.md
- agenticRules.md
- aws_client.py
- ci.yml
- github_client.py
- packages/ECOSYSTEM.toml
- progress.md
- pyproject.toml
- reusable-enforce-standards.yml
- reusable-release.yml
- set_version.py
- terraform_data_source.py
- terraform_null_resource.py
- utils.py

## PRs Mentioned
- #156
- #157
- #158
- #159
- #160
- #161
- #162
- #163
- #164
- #200
- #201
- #202

## Your Mission
1. Clone or access CI/CD
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view CI/CD --json name,description

# Check mentioned PRs
gh pr view 156 --repo CI/CD --json state,title
gh pr view 157 --repo CI/CD --json state,title
gh pr view 158 --repo CI/CD --json state,title
gh pr view 159 --repo CI/CD --json state,title
gh pr view 160 --repo CI/CD --json state,title
gh pr view 161 --repo CI/CD --json state,title
gh pr view 162 --repo CI/CD --json state,title
gh pr view 163 --repo CI/CD --json state,title
gh pr view 164 --repo CI/CD --json state,title
gh pr view 200 --repo CI/CD --json state,title
gh pr view 201 --repo CI/CD --json state,title
gh pr view 202 --repo CI/CD --json state,title

# Check files exist
ls -la .cursor/agents/jbcom-ecosystem-manager.md 2>/dev/null || echo 'Missing: .cursor/agents/jbcom-ecosystem-manager.md'
ls -la .github/copilot-instructions.md 2>/dev/null || echo 'Missing: .github/copilot-instructions.md'
ls -la .github/workflows/ci.yml 2>/dev/null || echo 'Missing: .github/workflows/ci.yml'
ls -la AGENTS.md 2>/dev/null || echo 'Missing: AGENTS.md'
ls -la README.md 2>/dev/null || echo 'Missing: README.md'
```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/CI_CD/RECOVERY_REPORT.md`
