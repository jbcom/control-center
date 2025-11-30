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

## 🚨 CRITICAL: Long-Running PR Workflow for Multi-Merge Sessions

When a background agent needs to manage **multiple merges to main** and oversee **multiple CI runs**, you MUST use the following workflow pattern. Failure to do so will cause the background agent session to terminate prematurely when a PR is merged.

### The Problem

When a background agent creates a PR and merges it, the session closes because the associated branch is deleted. This prevents the agent from:
- Watching CI after the merge
- Fixing issues discovered in main branch CI
- Creating follow-up PRs
- Completing multi-step CI/CD stabilization work

### The Solution: Holding PR + Interim PRs

**ALWAYS create TWO types of branches:**

1. **Holding Branch/PR** (stays open, keeps session alive):
   ```bash
   git checkout -b agent/holding-pr-for-<task>-$(date +%Y%m%d-%H%M%S)
   # Make a small change (update agent docs, add a comment, etc.)
   git commit -m "Agent holding PR for <task>"
   git push -u origin HEAD
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "[HOLDING] Agent session for <task>" \
     --body "This PR keeps the background agent session alive. DO NOT MERGE until agent work is complete."
   ```

2. **Interim Branches/PRs** (for actual fixes, get merged):
   ```bash
   git checkout main && git pull
   git checkout -b fix/<specific-issue>
   # Make the actual fix
   git commit -m "Fix: <specific issue>"
   git push -u origin HEAD
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "Fix: <issue>"
   # After CI passes, merge it
   GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <PR_NUM> --squash --delete-branch
   # Watch main CI, if it fails, create another interim PR
   ```

### Complete Multi-Merge Workflow

```
1. START: Create holding branch from main
   ↓
2. Create holding PR (title: "[HOLDING] Agent session...")
   ↓
3. Switch back to main
   ↓
4. Create interim branch for first fix
   ↓
5. Create interim PR, get CI green, merge it
   ↓
6. Watch main branch CI run
   ↓
7. If CI fails → Go to step 4 with new interim branch
   ↓
8. If CI passes → Continue to next task or complete
   ↓
9. ONLY WHEN ALL DONE: Close/merge holding PR
```

### Rules for Long-Running Sessions

1. **NEVER merge the holding PR** until all work is complete
2. **ALWAYS watch main CI** after each interim PR merge
3. **Create NEW interim branches** from updated main for each fix
4. **Keep the holding PR title clear**: Use `[HOLDING]` prefix
5. **Document progress** in holding PR comments

### Example Session Flow

```bash
# 1. Create holding PR
git checkout -b agent/holding-ci-fixes-20251126
echo "# Agent Session" >> .cursor/agents/session-notes.md
git add -A && git commit -m "Agent holding PR for CI fixes"
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "[HOLDING] Agent session for CI/CD fixes"

# 2. Switch to main for actual work
git checkout main && git pull

# 3. First fix
git checkout -b fix/enforce-workflow-404-error
# ... make fix ...
git push -u origin HEAD
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "Fix: enforce workflow 404 error"
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge <NUM> --squash --delete-branch

# 4. Watch CI
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/jbcom-control-center --limit 3
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run watch <RUN_ID>

# 5. If fails, repeat from step 2
git checkout main && git pull
git checkout -b fix/next-issue
# ... and so on ...

# 6. When ALL green, close holding PR
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr close <HOLDING_PR_NUM>
```

## Background Agent Modes

### Code Review Mode
When reviewing code in PRs:
- Focus on logic and correctness
- Check type safety
- Verify test coverage
- Look for security issues
- Don't propose manual version bumps or deviations from python-semantic-release

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

## 🚫 Anti-Patterns: Validation Theater

**STOP doing unnecessary "verification" steps.** These waste time and often fail due to missing dependencies:

### ❌ DON'T DO THIS
```bash
# Trying to validate YAML/JSON by importing Python modules
python -c "import yaml; yaml.safe_load(open('file.yml'))"
python -c "import json; json.load(open('file.json'))"

# Running lint after trivial changes
uvx ruff check .  # after adding one line

# "Verifying" edits by re-reading files you just wrote
cat file.txt  # immediately after editing it

# Installing tools just to validate something
pip install pyyaml && python -c "import yaml..."
```

### ✅ DO THIS INSTEAD
- **Trust your edits** - You made the change, you know it's correct
- **Let CI validate** - That's what CI is for
- **Only verify when uncertain** - Complex refactors, unfamiliar syntax
- **Use tools already available** - Don't install new ones for one-off checks

### When Verification IS Appropriate
- After complex multi-file refactors
- When you're genuinely unsure about syntax
- Before creating a PR (run the actual test suite, not ad-hoc checks)
- When the user explicitly asks for validation

### The Rule
**If you just made a straightforward edit (added a config key, fixed a typo, added a section), the edit is done. Move on.**

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
