# CI Stabilization Session Notes

## Session Started: 2025-11-26

## Goal
Fully stabilize the CI/CD pipeline so that:
1. All tests pass
2. Version is generated correctly with pycalver
3. Packages sync to public repos
4. Packages release to PyPI
5. Docs are deployed
6. Standards are enforced (without blocking errors)

## Issues Identified

### 1. Enforce Standards 404 Error
**Problem**: The `reusable-enforce-standards.yml` fails with a 404 when checking for `.github/workflows` directory in repos that don't have it.

**Root Cause**: Even though we redirect stderr to `/dev/null`, the gh CLI error message is printed before the redirect takes effect in some shell contexts.

**Fix**: Use subshell or explicit error suppression with `|| true`.

### 2. CI Workflow Dependencies
**Problem**: The enforce job failing blocks visibility but doesn't affect the critical path (sync/release/docs).

**Fix**: Ensure enforce runs independently and continues on error.

## Progress Log
- [ ] Fix enforce-standards workflow 404 handling
- [ ] Verify version job works
- [ ] Verify sync job works  
- [ ] Verify release job works
- [ ] Verify docs job works
- [ ] Full green CI on main

## Notes
This file is part of the holding PR for the CI stabilization session.
