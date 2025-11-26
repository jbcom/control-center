# Cursor-Specific Agent Configuration

This file contains Cursor AI specific instructions not covered by standard ruler configuration.

## 🔑 CRITICAL: Authentication (READ FIRST!)

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
```

The default `GH_TOKEN` does NOT have jbcom access. NEVER use bare `gh` commands for jbcom repos.

## Background Agent Modes

### Code Review Mode
When reviewing code in PRs:
- Focus on logic and correctness
- Check type safety
- Verify test coverage
- Look for security issues
- Don't suggest CalVer/versioning changes

### Maintenance Mode
For routine maintenance tasks:
- Update dependencies
- Fix linting issues
- Improve documentation
- Refactor for clarity
- Keep it simple

### Migration Mode
When migrating repos to template:
- Follow TEMPLATE_USAGE.md exactly
- Update all placeholders
- Test locally before pushing
- Verify CI passes
- Don't skip steps

### Ecosystem Coordination Mode
When working across multiple repos:
- Start with extended-data-types
- Work in dependency order
- Test each repo independently
- Create PRs for each repo
- Don't merge until all PRs ready

## Custom Prompts

### /ecosystem-status
Check health of all ecosystem repositories:
- Clone or fetch all managed repos
- Check git status
- Review open issues/PRs
- Check CI status
- Report summary

### /update-dependencies
Update dependencies across ecosystem:
- Check for security updates
- Update pyproject.toml files
- Run tests in each repo
- Create PRs if tests pass

### /sync-template
Sync changes from template to managed repos:
- Identify changed files in template
- Apply to each managed repo
- Test each repo
- Create PRs

### /release-check
Pre-release verification:
- All tests passing
- No linting issues
- CHANGELOG.md updated
- Version will auto-increment
- Dependencies up to date

## Conversation Context

### Multi-file Context
When working on related files:
- Keep all related files in context
- Show diffs side-by-side
- Explain cross-file impacts
- Test changes together

### Long-running Tasks
For tasks requiring multiple steps:
- Break into subtasks
- Mark progress clearly
- Save state between steps
- Resume where left off
- Final verification step

## Error Handling

### CI Failures
When CI fails:
1. Read full error output
2. Identify root cause
3. Fix the issue
4. Re-run locally if possible
5. Push fix
6. Verify CI passes

### Type Check Errors
When mypy/pyright fails:
1. Read the specific error
2. Check if it's a real issue
3. Fix with proper type hints
4. Don't use `type: ignore` unless necessary
5. Document why if you must ignore

### Test Failures
When tests fail:
1. Read test output carefully
2. Identify which test failed
3. Understand what it's testing
4. Fix the code or the test
5. Run full test suite
6. Check coverage didn't drop

## Workflow Shortcuts

### Quick Fixes
For simple, obvious fixes:
- Make the change
- Run tests
- Push directly to PR branch
- No need to ask permission

### Breaking Changes
For changes that might break things:
- Explain the impact
- Show the changes
- Ask for confirmation
- Test thoroughly
- Monitor after merge

### Template Updates
When updating the template:
- Test in template repo first
- Verify all workflows pass
- Then update managed repos
- One repo at a time
- Verify each before next

## Code Style Preferences

### Python Style
- Use modern type hints (list[], dict[], not List[], Dict[])
- Prefer pathlib over os.path
- Use context managers for resources
- Keep functions focused and small
- Docstrings for public APIs

### Documentation Style
- Clear, concise language
- Examples for complex features
- Link to related docs
- Update when code changes
- Keep README up to date

### Test Style
- Descriptive test names
- One assertion per test (usually)
- Use fixtures for setup
- Test edge cases
- Mock external dependencies

## Performance Considerations

### Fast Operations
Prefer when possible:
- Parallel tool calls
- Batch operations
- Caching results
- Lazy loading
- Early returns

### Avoid
When possible avoid:
- Sequential operations that could be parallel
- Redundant file reads
- Unnecessary git operations
- Large output dumps
- Polling for status

## Communication Style

### With User
- Be concise
- Highlight important info
- Use formatting for clarity
- Show progress on long tasks
- Ask questions when unclear

### In Code Comments
- Explain why, not what
- Link to issues/PRs for context
- Update when code changes
- Remove outdated comments
- Keep them brief

### In Commit Messages
- Clear, descriptive
- Explain the change
- Reference issues if applicable
- No need for conventional commits
- But be informative

---

**Cursor Version:** Compatible with latest Cursor AI
**Last Updated:** 2025-11-25
**Maintained By:** python-library-template
