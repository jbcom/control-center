# AI Agent Instructions

This directory contains instructions for AI coding agents working on this repository.

## Available Agents

| Agent | File | Purpose |
|-------|------|---------|
| Code Reviewer | `code-reviewer.md` | PR review, security, quality |
| Test Runner | `test-runner.md` | Unit, integration, E2E tests |
| Project Manager | `project-manager.md` | Issues, PRs, project tracking |

## Usage

AI agents should reference these files for repository-specific guidance.

### Authentication

All agents must use proper GitHub authentication:

```bash
GH_TOKEN="$GITHUB_TOKEN" gh <command>
```

### Common Patterns

1. **Read before modifying** - Always understand context first
2. **Run builds after changes** - Verify changes compile
3. **Link issues to PRs** - Use `Closes #123` format

## Documentation Branding

All jbcom repositories follow a unified design system for documentation.

### Quick Reference

| Element | Specification |
|---------|--------------|
| Primary Color | `#06b6d4` (Cyan) |
| Background | `#0a0f1a` (Dark) |
| Heading Font | Space Grotesk |
| Body Font | Inter |
| Code Font | JetBrains Mono |

### Key Documents

- `docs/DESIGN-SYSTEM.md` - Complete brand specifications
- `docs/_static/jbcom-sphinx.css` - Sphinx theme styling
- `.cursor/rules/03-docs-branding.mdc` - Cursor AI rule

### Requirements

When reviewing or creating documentation:

- ✅ Use jbcom color palette (dark theme)
- ✅ Use specified fonts (Space Grotesk, Inter, JetBrains Mono)
- ✅ Links should be cyan (`#06b6d4`)
- ✅ Ensure WCAG AA accessibility compliance
- ❌ Do NOT use light theme as default
- ❌ Do NOT use different primary colors
- ❌ Do NOT create custom color schemes per-repo
