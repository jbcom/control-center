# Python Library Template - Usage Guide

This template provides a **production-ready** Python library structure with **automatic CalVer versioning** and **PyPI publishing**.

## 🎯 What You Get

- ✅ **Automatic versioning** using CalVer (`YYYY.MM.BUILD`)
- ✅ **Automatic PyPI releases** on every main branch push
- ✅ **Unified CI workflow** with tests, type checking, linting, and publishing
- ✅ **Signed package attestations** for security
- ✅ **Pre-configured tools**: ruff, mypy/pyright, pytest, pre-commit
- ✅ **Comprehensive AI agent instructions** for Cursor, Copilot, etc.
- ✅ **Production-tested** across jbcom ecosystem

## 🚀 Quick Start

### 1. Create New Repository

```bash
# On GitHub: Use this template to create a new repository
# Or clone and set up manually:
git clone https://github.com/jbcom/python-library-template.git my-new-library
cd my-new-library
rm -rf .git
git init
git remote add origin https://github.com/YOUR_ORG/my-new-library.git
```

### 2. Update Project Configuration

Edit `pyproject.toml`:

```toml
[project]
name = "my-new-library"  # Change this
description = "Your library description"  # Change this
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]

# Update dependencies as needed
dependencies = [
    # Your dependencies here
]
```

### 3. Update Package Structure

```bash
# Rename the src directory to match your package
mv src/example_package src/my_new_library

# Update __init__.py
cat > src/my_new_library/__init__.py << 'EOF'
"""My New Library - Description here."""

__version__ = "0.0.0"  # Will be auto-updated by CI

# Your exports here
__all__ = []
EOF
```

### 4. Update AI Agent Documentation

Update repo name in documentation files:

```bash
# Update ruler source files (Note: On macOS, use sed -i '' instead of sed -i)
sed -i 's/\${REPO_NAME}/my-new-library/g' .ruler/AGENTS.md  # Linux
# sed -i '' 's/\${REPO_NAME}/my-new-library/g' .ruler/AGENTS.md  # macOS

# Regenerate agent-specific instructions
ruler apply
```

### 5. Configure PyPI Publishing

Set up **trusted publishing** (no tokens needed):

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new pending publisher:
   - **Owner**: `your-org`
   - **Repository**: `my-new-library`
   - **Workflow**: `ci.yml`
   - **Environment**: `pypi`

Update workflow environment URL in `.github/workflows/ci.yml`:

```yaml
environment:
  name: pypi
  url: https://pypi.org/project/my-new-library/${{ needs.release.outputs.package_version }}
```

### 6. Initial Commit and Push

```bash
git add .
git commit -m "Initial commit from template"
git branch -M main
git push -u origin main
```

## 🎨 Customization

### Versioning Script

The `.github/scripts/set_version.py` script should work out-of-the-box. It:
- Auto-detects your package in `src/`
- Finds `__version__` declaration
- Updates it during CI runs
- Also updates `docs/conf.py` if present

**No changes needed** unless you have a non-standard project structure.

### CI Workflow

The `.github/workflows/ci.yml` is production-ready. You may want to:

**Customize Python versions:**

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12', '3.13']  # Adjust as needed
```

**Customize test commands:**

```yaml
- name: Run tests
  run: |
    pytest tests/  # or your custom test command
```

**Add/remove check jobs:**

The workflow includes:
- `build`: Package building and inspection
- `tests`: Test matrix across Python versions
- `typechecking`: Type validation (pyright/mypy)
- `linting`: Code quality (ruff/pre-commit)
- `coverage`: Test coverage reporting
- `release`: Auto-versioning and building
- `publish`: PyPI publishing

### Linting Configuration

Update `pyproject.toml` for your project's linting needs:

```toml
[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    # Add more as needed
]

[tool.ruff.lint.per-file-ignores]
# Exempt CI scripts from certain rules
".github/scripts/*.py" = ["T201", "D103", "EM101", "PTH123", "EXE001"]
"tests/*.py" = ["D103", "S101"]  # Allow asserts in tests
```

### Documentation

If you have documentation:

1. Keep `docs/conf.py` with a `version = "X.Y.Z"` line
2. The versioning script will auto-update it
3. Add docs build to CI if needed

## 🔄 Development Workflow

### Making Changes

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, add tests
# ...

# Run checks locally
pytest
mypy src/
pre-commit run --all-files

# Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### Creating Pull Requests

1. Push your branch
2. Create PR on GitHub
3. CI runs automatically
4. Address any failures
5. Get review approval
6. Merge to main

### Automatic Releases

Once merged to main:
1. ✅ CI runs all checks
2. ✅ Auto-generates version (e.g., `2025.11.42`)
3. ✅ Builds package with signed attestations
4. ✅ Publishes to PyPI
5. ✅ Done!

**No manual steps required.**

## 🤖 AI Agent Integration

This template includes comprehensive instructions for AI coding assistants:

### Files for AI Agents

- **`AGENTS.md`**: Comprehensive guide (read this first)
- **`.cursorrules`**: Cursor-specific instructions
- **`.github/copilot-instructions.md`**: GitHub Copilot quick reference

### Key Points for Agents

✅ **Trust the automatic versioning** - don't manually manage versions
✅ **Every main push = release** - this is intentional
✅ **No git tags or GitHub releases** - PyPI is the source of truth
✅ **Simple is correct** - don't suggest complex alternatives

❌ **Don't suggest semantic-release** - we intentionally removed it
❌ **Don't suggest manual versioning** - it's automatic
❌ **Don't suggest git tags** - we don't use them

## 🧪 Testing the Template

### Test Locally

```bash
# Test the versioning script
export GITHUB_RUN_NUMBER=999
python .github/scripts/set_version.py

# Verify version was updated
grep __version__ src/my_new_library/__init__.py
```

### Test CI

1. Create a dummy PR
2. Watch CI run
3. Verify all checks pass
4. Check version generation in logs

### Test Release

1. Merge a small change to main
2. Watch CI run through release
3. Check PyPI for new version
4. Install and verify: `pip install my-new-library`

## 📦 Template Maintenance

### Keeping Template Updated

For jbcom ecosystem libraries:

1. Pull latest template improvements
2. Review changes in AGENTS.md
3. Update workflows if needed
4. Test locally before deploying

### Contributing Back to Template

If you improve the template:

1. Test in your library first
2. Create PR to python-library-template
3. Document the improvement
4. Reference the production library where it was tested

## 🔍 Reference Implementations

See these production libraries for examples:

- **[extended-data-types](https://github.com/jbcom/extended-data-types)**: Foundational data types library
  - Released: `2025.11.164`
  - Full test coverage, type hints
  - Production CalVer deployment

- **[lifecyclelogging](https://github.com/jbcom/lifecyclelogging)**: Structured logging library
  - Clean implementation
  - Good example of docs integration

- **[directed-inputs-class](https://github.com/jbcom/directed-inputs-class)**: Input processing library
  - Simple, focused library
  - Minimal dependencies

## 📋 Checklist for New Libraries

Before first release:

- [ ] Updated `pyproject.toml` with project details
- [ ] Renamed package directory under `src/`
- [ ] Updated `__version__` in `__init__.py`
- [ ] Replaced `${REPO_NAME}` in AGENTS.md and copilot-instructions.md
- [ ] Configured PyPI trusted publishing
- [ ] Updated CI workflow environment URL
- [ ] Added project to PyPI (or enabled new project publishing)
- [ ] Wrote initial tests
- [ ] Added README with usage examples
- [ ] Pushed to main and verified first release

## 🚨 Common Issues

### Issue: "src/ directory not found"

**Solution:** The versioning script expects a `src/` directory with your package.

### Issue: "No __init__.py with __version__ found"

**Solution:** Ensure your package's `__init__.py` has a line like:
```python
__version__ = "0.0.0"
```

### Issue: "PyPI publish failed - authentication"

**Solution:** Configure trusted publishing on PyPI (see step 5 in Quick Start)

### Issue: "Lint failures on set_version.py"

**Solution:** Add to `pyproject.toml`:
```toml
[tool.ruff.lint.per-file-ignores]
".github/scripts/*.py" = ["T201", "D103", "EM101", "PTH123", "EXE001"]
```

### Issue: "Version not incrementing"

**Solution:** GitHub run number is used. Each run gets a new number, ensuring increment.

## 📚 Additional Resources

- **CalVer Specification**: https://calver.org/
- **PyPI Trusted Publishing**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Ruff**: https://docs.astral.sh/ruff/

## 💡 Philosophy

This template embodies:

1. **Simplicity First**: Minimal configuration, maximum automation
2. **Reliability Over Features**: It should work every time
3. **Clear Failures**: When something breaks, it should be obvious
4. **No Magic**: Everything is explicit and traceable
5. **Developer Friendly**: Works with AI agents and humans

## 🤝 Support

For issues or questions:
1. Check AGENTS.md (comprehensive)
2. Review reference implementations
3. Search existing issues
4. Create an issue if needed

---

**Template Version**: 1.0.0  
**Last Updated**: 2025-11-24  
**Status**: Production-ready, battle-tested
