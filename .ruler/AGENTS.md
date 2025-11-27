# AI Agent Guidelines for Python Library Template (jbcom ecosystem)

**This is the DEFINITIVE Python library template** for the jbcom ecosystem. All configuration, workflows, and agent instructions here represent the consolidated best practices from multiple production deployments.

## 🎯 CRITICAL: PR Ownership Rule (READ WHEN WORKING WITH PRs!)

**If you are working on a Pull Request, STOP and read `pr-ownership.md` FIRST.**

Key points:
- **First agent on PR = PR Owner** - You own ALL feedback, issues, and collaboration
- **Engage with AI agents directly** - Respond to @gemini-code-assist, @copilot, etc.
- **Free the user** - Handle everything that doesn't need human judgment
- **Collaborate, don't escalate** - Resolve AI-to-AI conflicts yourself

See `.ruler/pr-ownership.md` for complete protocol.

## 🔑 CRITICAL: Authentication (READ FIRST!)

**ALWAYS use `GITHUB_JBCOM_TOKEN` for ALL jbcom repo operations:**
```bash
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create --title "..." --body "..."
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr merge 123 --squash --delete-branch
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh run list --repo jbcom/extended-data-types
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh workflow run "Release" --repo jbcom/jbcom-control-center
```

### Token Reference:
- **GITHUB_JBCOM_TOKEN** - Use for ALL jbcom repo operations (PRs, merges, workflow triggers)
- **CI_GITHUB_TOKEN** - Used by GitHub Actions workflows (in repo secrets)
- **PYPI_TOKEN** - Used by release workflow for PyPI publishing (in repo secrets)

### ⚠️ NEVER FORGET:
The default `GH_TOKEN` does NOT have access to jbcom repos. You MUST prefix with `GH_TOKEN="$GITHUB_JBCOM_TOKEN"` for EVERY `gh` command targeting jbcom repos.

## 🎯 PURPOSE: Agentic Template Repository

This template is designed for:
1. **Human developers** starting new Python libraries
2. **AI coding assistants** (Cursor, Codex, Copilot, Gemini) helping maintain the ecosystem
3. **Background agents** performing automated maintenance tasks

### Template Usage

When creating a new library from this template:
1. Update `pyproject.toml` with your project name and details
2. Replace `${REPO_NAME}` in documentation with your actual repo name
3. Copy `.github/scripts/set_version.py` as-is (it auto-detects your package)
4. Copy `.github/workflows/ci.yml` and update PyPI project name
5. Run `ruler apply` to regenerate agent-specific instructions

## 🚨 CRITICAL: CI/CD Workflow Design Philosophy

### Our Simple Automated Release Workflow

**This repository uses CALENDAR VERSIONING with automatic PyPI releases**. Every push to main that passes tests gets released automatically.

This design has been battle-tested across:
- `extended-data-types` (foundational library, released 2025.11.164)
- `lifecyclelogging` (logging library)
- `directed-inputs-class` (input processing)

### Key Design Decisions (DO NOT SUGGEST CHANGING THESE)

#### 1. **Calendar Versioning (CalVer) - No Manual Version Management**

✅ **How It Works:**
- Version format: `YYYY.MM.BUILD_NUMBER`
- Example: `2025.11.42`
- **Month is NOT zero-padded** (project choice for brevity)
- Version is auto-generated using GitHub run number
- Script: `.github/scripts/set_version.py`

❌ **INCORRECT Agent Suggestion:**
> "You should manually manage versions in __init__.py"
> "Add semantic-release for version management"
> "Use git tags for versioning"
> "Zero-pad the month for consistency"

✅ **CORRECT Understanding:**
- Version is AUTOMATICALLY updated on every main branch push
- No git tags needed or used
- No semantic analysis of commits needed
- No manual version bumps required
- Month padding is a project preference (we chose no padding)

#### 2. **Every Push to Main = PyPI Release**

✅ **How It Works:**
```
Push to main branch
  ↓
All tests pass
  ↓
Auto-generate version (YYYY.MM.BUILD)
  ↓
Build signed package
  ↓
Publish to PyPI
  ↓
DONE
```

❌ **INCORRECT Agent Suggestion:**
> "Only release when version changes"
> "Check if release is needed before publishing"
> "Use conditional logic to skip releases"

✅ **CORRECT Understanding:**
- Every main branch push = new release
- No conditionals, no skipping
- Simple, predictable, automatic
- If code was merged to main, it should be released

#### 3. **No Git Tags, No GitHub Releases**

✅ **What We Do:**
- Publish directly to PyPI
- Version in package metadata only
- PyPI is the source of truth for releases

❌ **What We Don't Do:**
- ❌ Create git tags
- ❌ Create GitHub releases
- ❌ Manage changelog files automatically
- ❌ Commit version changes back to repo

#### 4. **Why This Approach?**

**Problems with semantic-release and tag-based versioning:**
- Complex setup and configuration
- Depends on commit message conventions
- Requires git tags and history analysis
- Can fail or skip releases unexpectedly
- Adds unnecessary complexity
- Multiple points of failure

**Benefits of CalVer + Auto-increment:**
- ✅ Dead simple - minimal configuration
- ✅ Always works - no analysis, no skipping
- ✅ Predictable - every push = new version
- ✅ No git pollution - no tags, no bot commits
- ✅ Build number always increments
- ✅ Fails loudly with clear error messages

## 📝 Making Code Changes

### When Reviewing PRs

**DO:**
- ✅ Review code quality and correctness
- ✅ Check test coverage
- ✅ Verify type hints
- ✅ Suggest API improvements
- ✅ Check for security issues
- ✅ Verify dependencies are up to date

**DO NOT:**
- ❌ Suggest adding semantic-release
- ❌ Recommend manual version management
- ❌ Suggest git tag-based versioning
- ❌ Recommend complex release workflows
- ❌ Flag the simple auto-versioning as "incorrect"
- ❌ Suggest zero-padding months (unless project explicitly wants it)

### Understanding Version Management

```
GitHub Action Starts
  ↓
Run Number: 42 (GitHub auto-increments)
  ↓
Script generates: 2025.11.42
  ↓
Updates __init__.py: __version__ = "2025.11.42"
  ↓
Updates docs/conf.py: version = "2025.11.42" (if exists)
  ↓
Package built with that version
  ↓
Published to PyPI
```

**Version is:**
- ✅ Generated automatically
- ✅ Based on date + GitHub run number
- ✅ Always incrementing
- ✅ Written to __init__.py during build
- ✅ Also written to docs/conf.py if it exists
- ❌ NOT committed back to git
- ❌ NOT based on git tags

### The set_version.py Script

Key features of the production-tested script:
- **Auto-detects** the package `__init__.py` in `src/`
- **Validates** that exactly one __version__ declaration exists
- **Uses regex** to match version assignment (handles quotes, spacing, etc.)
- **Fails loudly** with clear error if update doesn't work
- **Updates docs/conf.py** if it exists (optional)
- **Preserves indentation** and file formatting
- **Ruff-compliant** with proper noqa annotations

### Commit Message Format

**You can use any commit format you want.** We don't analyze commits for versioning.

Recommendations:
- Write clear, descriptive commits
- Explain what and why
- No specific format required
- Conventional commits are fine but not enforced

## 🤖 For AI Agents: Approval & Override Instructions

### Background Agent Behavior

When you are operating as a **background agent** (autonomous, no user interaction):

**CRITICAL RULES:**
1. **DO NOT** create or merge PRs without explicit user approval
2. **DO NOT** push directly to main branch
3. **DO** create PRs and mark them as ready for review
4. **DO** run all CI checks and fix linting/test failures
5. **DO** respond to PR feedback and iterate
6. **WAIT** for human approval before merging

**EXCEPTION - When User Says:**
> "merge it", "go ahead and merge", "merge to main", "just push it"

Then you MAY:
- Merge PRs after CI passes
- Push directly to main if explicitly instructed
- Skip the usual "wait for approval" step

**HOW TO MERGE:**
```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

### Interactive Agent Behavior

When you are in **interactive mode** (user is actively engaged):

**DEFAULT BEHAVIOR:**
- Ask for confirmation before major actions
- Present options and let user decide
- Show diffs and explain changes

**WHEN USER GETS FRUSTRATED:**
User signals like "just do it", "stop asking", "I don't care", "fucking do it":
- Switch to autonomous mode
- Make decisions based on best practices in this document
- Execute without asking for every little thing
- Still verify after major milestones

### PR Review Response

When PR feedback arrives (from Copilot, Gemini, human reviewers):

1. **READ the feedback carefully**
2. **CHECK** if feedback contradicts this document
3. **IF** feedback suggests semantic-release, git tags, or manual versioning:
   - Politely explain our CalVer approach
   - Reference this document
   - Do NOT implement the suggestion
4. **IF** feedback is about code quality, bugs, or improvements:
   - Implement the feedback
   - Push fixes
   - Verify CI passes

### Template Maintenance Tasks

As an agent maintaining this template:

**ALLOWED:**
- Update dependencies
- Fix security vulnerabilities
- Improve documentation clarity
- Add helpful examples
- Fix bugs in scripts or workflows

**NOT ALLOWED WITHOUT USER APPROVAL:**
- Change the versioning approach
- Modify CI workflow structure
- Remove or bypass safety checks
- Change the release process

## 🔧 Development Workflow

### Local Development

```bash
# Install dependencies
pip install -e ".[tests,typing,docs]"  # or use poetry/uv

# Run tests
pytest

# Run type checking
mypy src/  # or pyright

# Run linting
pre-commit run --all-files
```

### Creating PRs

1. Create a feature branch
2. Make your changes
3. Run tests locally
4. Create PR against `main`
5. CI will run automatically
6. Address any feedback
7. Merge to main when approved

### Releases (Fully Automated)

When PR is merged to main:
1. CI runs all checks
2. Auto-generates version: `YYYY.MM.BUILD`
3. Builds signed package with attestations
4. Publishes to PyPI
5. **DONE - that's it**

No manual steps, no tags, no conditionals, no complexity.

## 🎯 Common Agent Misconceptions

### Misconception #1: "Missing version management"
**Agent says:** "You need to manually update __version__ before releases"
**Reality:** Version is auto-generated on every main branch push. Manual management not needed and will be overwritten.

### Misconception #2: "Should use semantic versioning"
**Agent says:** "Consider using semantic-release or conventional commits"
**Reality:** We intentionally use CalVer for simplicity. Every push gets a new version. This has been deployed successfully across multiple production libraries.

### Misconception #3: "Need git tags"
**Agent says:** "Add git tags for release tracking"
**Reality:** PyPI version history is our source of truth. No git tags needed. We tried this, it caused more problems than it solved.

### Misconception #4: "CalVer is wrong for libraries"
**Agent says:** "Libraries should use SemVer"
**Reality:** CalVer works fine for our ecosystem. Users pin versions anyway. Simplicity and reliability > convention. Our dependencies work with CalVer.

### Misconception #5: "Missing release conditions"
**Agent says:** "You should only release when changes are made"
**Reality:** Every main push is intentional. If it was merged, it should be released. Empty releases are fine and caught by PyPI anyway.

### Misconception #6: "Month should be zero-padded"
**Agent says:** "Use 2025.01.42 instead of 2025.1.42"
**Reality:** This is a project-specific choice. We chose no padding for brevity. CalVer allows both. Don't suggest changing it.

### Misconception #7: "Need to commit version back to git"
**Agent says:** "Version changes should be committed to the repository"
**Reality:** NO. Versions are ephemeral build artifacts. Committing them creates noise and potential conflicts. The script updates them during CI only.

## 📚 Design Rationale

This workflow was created to solve REAL problems we encountered:

**Problems We Solved:**
- ✅ No more failed releases due to missing tags
- ✅ No more version conflicts between branches
- ✅ No more "why didn't it release?" debugging sessions
- ✅ No more complex semantic-release configuration issues
- ✅ No more dependency on git history analysis
- ✅ No more bot commits cluttering git history
- ✅ No more release workflow that sometimes works, sometimes doesn't

**Benefits We Gained:**
- ✅ Predictable: every main push = release
- ✅ Simple: ~100 lines of Python for versioning
- ✅ Reliable: no conditional logic to fail
- ✅ Fast: no git history analysis overhead
- ✅ Clean: no bot commits or tags in git
- ✅ Debuggable: clear error messages when things fail
- ✅ Testable: can run script locally with ease

## 🧪 Testing the Workflow

### Local Testing

Test the versioning script locally:
```bash
export GITHUB_RUN_NUMBER=999
python .github/scripts/set_version.py

# Verify it updated the version
grep __version__ src/your_package/__init__.py
```

### CI Testing

Test in a PR:
1. Create a PR
2. Watch CI run
3. Verify all checks pass
4. Check that versioning step succeeds

### Release Testing

To test an actual release:
1. Merge a PR to main
2. Watch the CI run
3. Verify version was generated (check logs)
4. Verify package was built with correct version
5. Verify publish to PyPI succeeded
6. Install from PyPI and verify: `pip install your-package==2025.XX.YYY`

## 🤝 Getting Help

### For AI Agents

If you're an AI agent uncertain about a suggestion:
1. **Check this document first** - it's comprehensive
2. If it involves versioning or releases, **DO NOT suggest changes**
3. Focus on code quality, tests, and documentation
4. Trust that the release workflow is intentionally simple
5. When in doubt, ask the user instead of assuming

### For Human Developers

- This template has been tested in production
- Don't overthink it - it's designed to be simple
- If something seems weird, check this document first
- The versioning really is meant to be automatic
- Trust the process - it works

---

**Last Updated:** 2025-11-25
**Versioning:** CalVer (YYYY.MM.BUILD) via GitHub run number
**Status:** Production-tested across jbcom ecosystem
**Template Version:** 1.0.0
