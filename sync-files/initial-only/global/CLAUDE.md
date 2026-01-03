# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **See also:** `AGENTS.md` for comprehensive agent instructions.

## 🤖 AI Agent Commands

Delegate work to AI agents by commenting on issues or PRs:

| Command | Agent | What It Does |
|---------|-------|--------------|
| `/jules <task>` | Google Jules | Multi-file refactoring, auto-creates PR |
| `/cursor <task>` | Cursor Cloud | Long-running autonomous tasks |
| `@claude <task>` | Claude Code | Analysis, implementation, creates PR |
| `@sage <question>` | Ollama | Quick answers and explanations |

**Example:** `/jules Add comprehensive input validation to all API endpoints`

> Requires control center workflow integration. See [jbcom/control-center](https://github.com/jbcom/control-center).

---

## Quick Start

```bash
# Check current context before starting
cat memory-bank/activeContext.md 2>/dev/null || echo "No active context"

# Check for project-specific instructions
cat .github/copilot-instructions.md 2>/dev/null
```

## Development Workflow

### Before Making Changes
1. Read the issue/PR description completely
2. Check `memory-bank/` for project context
3. Look at recent commits for coding patterns
4. Run tests to ensure clean starting state

### Making Changes
1. Create a feature branch if not already on one
2. Make minimal, focused changes
3. Write/update tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed

### Committing
```bash
# Use conventional commits
git commit -m "feat(scope): add new feature"
git commit -m "fix(scope): resolve bug"
git commit -m "docs: update README"
git commit -m "test: add missing tests"
git commit -m "chore: update dependencies"
```

## Code Quality Checklist

Before considering work complete:
- [ ] All tests pass
- [ ] Linting passes
- [ ] No new warnings introduced
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format

## Project Structure

```
.
├── src/                 # Source code
├── tests/               # Test files
├── docs/                # Documentation
├── memory-bank/         # AI context files
│   ├── activeContext.md # Current focus
│   └── progress.md      # Session progress
├── .github/
│   ├── copilot-instructions.md  # Copilot context
│   └── workflows/       # CI/CD
├── CLAUDE.md            # This file
└── AGENTS.md            # Agent instructions
```

## Getting Help

1. Check `AGENTS.md` for detailed instructions
2. Check `.github/copilot-instructions.md` for dev commands
3. Check `docs/` for architecture decisions
4. Look at test files for usage examples

## Repository-Specific Notes

<!-- Add repository-specific context below -->

