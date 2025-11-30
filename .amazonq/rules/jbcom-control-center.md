# jbcom Control Center - Amazon Q Rules

## Project Overview

This is the jbcom-control-center, managing the Python library ecosystem via monorepo architecture.

## Core Principles

### 1. SemVer via python-semantic-release
- **NEVER** manually edit `__version__` or pyproject versions
- Versions use format: `MAJOR.MINOR.PATCH`
- Conventional commits drive version changes
- Each package is versioned independently via Git tags

### 2. Release Philosophy
- Uses python-semantic-release (PSR) for automated versioning
- Conventional commits determine version bumps
- Per-package Git tags track release state
- Merge to `main` with proper commits = automatic PyPI release

### 3. Conventional Commit Format (REQUIRED)

```
<type>(<scope>): <description>

Types: feat (minor), fix/perf (patch), feat! (major)
Scopes: edt, logging, dic, connectors
```

| Scope | Package |
|-------|---------|
| `edt` | extended-data-types |
| `logging` | lifecyclelogging |
| `dic` | directed-inputs-class |
| `connectors` | vendor-connectors |

### 4. Python Best Practices
- Use modern type hints (`list[]`, `dict[]`, not `List[]`, `Dict[]`)
- Prefer `pathlib` over `os.path`
- Use `ruff` for linting (configured in `pyproject.toml`)
- Type hints required for public APIs
- Docstrings for public functions/classes (Google style)
- Tests for new features

### 5. Dependency Management
- Use `uv` for package management
- Check `extended-data-types` before adding dependencies
- Avoid duplication across packages

## Security Requirements

### AWS Infrastructure
- All S3 buckets must have encryption enabled, enforce SSL, and block public access
- All DynamoDB tables must have encryption enabled
- All SNS topics must have encryption enabled and enforce SSL
- All SQS queues must enforce SSL
- IAM policies must follow least privilege principle

### Secrets Management
- NEVER commit credentials or API keys
- Use environment variables for secrets
- Use `make_raw_data_export_safe()` before logging

## Code Quality

### What to Flag as Critical Issues (🔴)
- Security vulnerabilities
- Breaking changes without migration path
- Missing error handling in critical paths
- Hardcoded credentials or secrets
- SQL injection or XSS vulnerabilities
- Missing input validation

### What to Flag as Warnings (🟡)
- Missing type hints
- Missing docstrings for public APIs
- Inefficient algorithms (O(n²) where O(n) possible)
- Missing tests for new features
- Deprecated API usage
- Inconsistent naming conventions
- Non-conventional commit messages

### What to Suggest (🔵)
- Refactoring opportunities
- Better variable names
- Additional test cases
- Documentation improvements
- Performance optimizations

## Architecture Patterns

### Monorepo Structure
```
packages/
├── extended-data-types/  → Foundation (ALL packages depend on this)
├── lifecyclelogging/     → Logging (depends on extended-data-types)
├── directed-inputs-class → Input validation
└── vendor-connectors/    → Cloud connectors (depends on multiple)
```

### Release Order
1. extended-data-types
2. lifecyclelogging
3. directed-inputs-class
4. vendor-connectors

## Common Mistakes to Avoid

❌ **DON'T**:
- Suggest removing python-semantic-release
- Recommend manual version management
- Remove Git tags (they track release state)
- Add duplicate utilities (check extended-data-types first)
- Use non-conventional commit messages
- Use `typing.List`, `typing.Dict` (use built-ins)

✅ **DO**:
- Use `extended_data_types` utilities
- Use conventional commits with proper scopes
- Run tests before committing
- Check for dependency duplication
- Use modern Python features (3.13+)

## Review Checklist

When reviewing code, check:

- [ ] No manual version edits
- [ ] Commit messages follow conventional format
- [ ] Type hints present and correct
- [ ] Tests added for new features
- [ ] No hardcoded secrets
- [ ] Uses extended-data-types utilities where applicable
- [ ] Follows project structure
- [ ] Documentation updated
- [ ] No breaking changes without discussion
- [ ] Error handling present
- [ ] Input validation for external data

## Integration with Other AI Reviewers

### When Claude Code Reviews
- Focus on Python-specific best practices
- Check ecosystem consistency
- Validate conventional commit messages

### When You (Amazon Q) Review
- Focus on AWS infrastructure patterns
- Security best practices
- Cloud architecture
- IAM policies and permissions

### When DiffGuard Reviews
- Focus on breaking changes
- Version compatibility
- Dependency impacts

## Collaboration Protocol

1. Read all other AI reviews before commenting
2. Don't duplicate feedback
3. Build on others' suggestions
4. Flag disagreements with reasoning
5. Provide consensus recommendations
