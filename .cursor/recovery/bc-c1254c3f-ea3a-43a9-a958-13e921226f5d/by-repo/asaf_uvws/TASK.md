# Repository Task: asaf/uvws

**Agent**: bc-c1254c3f-ea3a-43a9-a958-13e921226f5d
**Relevant Messages**: 1
**Generated**: 2025-11-27T23:13:41Z

## Context
This task was extracted from agent bc-c1254c3f-ea3a-43a9-a958-13e921226f5d's conversation.
The agent mentioned this repository 1 times.

## Files Mentioned
- -o.yml
- ../../scripts/psr/custom_parser/monorepo_parser.py
- ./.github/workflows/release-package.yml
- ./packages/core/CHANGELOG.md
- ./packages/core/pyproject.toml
- ./packages/core/src/uvws_core/__init__.py
- ./packages/svc1/pyproject.toml
- ./pyproject.toml
- ./scripts/psr/custom_parser/monorepo_parser.py
- ./scripts/update_package_deps.py
- ./src/uvws/__init__.py
- //github.com/asaf/uvws/blob/main/.github/workflows/release-package.yml
- //github.com/asaf/uvws/blob/main/.github/workflows/release.yml
- //raw.githubusercontent.com/asaf/uvws/refs/heads/main/scripts/psr/custom_parser/monorepo_parser.py
- //raw.githubusercontent.com/asaf/uvws/refs/heads/main/scripts/update_package_deps.py
- CHANGELOG.md
- __init__.py
- packages/core/src/uvws_core/__init__.py
- packages/svc1/pyproject.toml
- packages/svc1/src/uvws_svc1/__init__.py
- pyproject.toml
- src/uvws/__init__.py
- src/uvws_core/__init__.py
- src/uvws_svc1/__init__.py

## PRs Mentioned


## Your Mission
1. Clone or access asaf/uvws
2. Review the files and PRs mentioned above
3. Determine what work was completed vs incomplete
4. Generate a recovery report

## Verification Steps
```bash
# Check repo state
gh repo view asaf/uvws --json name,description

# Check mentioned PRs


# Check files exist
ls -la -o.yml 2>/dev/null || echo 'Missing: -o.yml'
ls -la ../../scripts/psr/custom_parser/monorepo_parser.py 2>/dev/null || echo 'Missing: ../../scripts/psr/custom_parser/monorepo_parser.py'
ls -la ./.github/workflows/release-package.yml 2>/dev/null || echo 'Missing: ./.github/workflows/release-package.yml'
ls -la ./packages/core/CHANGELOG.md 2>/dev/null || echo 'Missing: ./packages/core/CHANGELOG.md'
ls -la ./packages/core/pyproject.toml 2>/dev/null || echo 'Missing: ./packages/core/pyproject.toml'
```

## Output
Create: `/workspace/.cursor/recovery/bc-c1254c3f-ea3a-43a9-a958-13e921226f5d/by-repo/asaf_uvws/RECOVERY_REPORT.md`
