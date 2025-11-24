# Python Library Template 🚀

**Production-ready Python library template with automatic CalVer versioning and PyPI publishing.**

## ✨ Features

- 🔢 **Calendar Versioning (CalVer)**: `YYYY.MM.BUILD` format, auto-incremented
- 📦 **Automatic PyPI Releases**: Every main branch push = new PyPI release
- 🔐 **Signed Package Attestations**: Built-in security with provenance tracking
- 🧪 **Comprehensive CI/CD**: Tests, type checking, linting, coverage
- 🤖 **AI Agent Ready**: Includes instructions for Cursor, Copilot, and other AI assistants
- ⚡ **Modern Tooling**: Hatchling, Ruff, Pytest, Pyright/Mypy, Pre-commit
- 📚 **Battle-Tested**: Deployed across the jbcom ecosystem

## 🎯 Quick Start

### 1. Use This Template

Click "Use this template" on GitHub or:

```bash
gh repo create my-new-library --template jbcom/python-library-template --public
cd my-new-library
```

### 2. Customize Your Project

```bash
# Update package name in pyproject.toml
sed -i 's/python-library-template/my-new-library/g' pyproject.toml

# Rename the package directory
mv src/example_package src/my_new_library

# Update imports and references
sed -i 's/example_package/my_new_library/g' pyproject.toml

# Update agent documentation
sed -i 's/\${REPO_NAME}/my-new-library/g' AGENTS.md .github/copilot-instructions.md

# Update workflow environment URL
sed -i 's/python-library-template/my-new-library/g' .github/workflows/ci.yml
```

### 3. Configure PyPI Publishing

Set up [trusted publishing](https://docs.pypi.org/trusted-publishers/) on PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Add pending publisher:
   - Owner: `your-org`
   - Repo: `my-new-library`
   - Workflow: `ci.yml`
   - Environment: `pypi`

### 4. Push and Release

```bash
git add .
git commit -m "Initialize from template"
git push origin main
```

**That's it!** CI will run, and your first version will be published to PyPI automatically.

## 📖 How It Works

### Versioning: CalVer with Auto-Increment

```
GitHub Run Number: 42
Current Date: 2025-11-24

Generated Version: 2025.11.42
```

Every push to main:
1. Generates version from date + GitHub run number
2. Updates `__version__` in your package's `__init__.py`
3. Also updates `docs/conf.py` if present
4. Builds package with that version
5. Publishes to PyPI

**No manual version management. No git tags. Just works.**

### Workflow

```
Push to main
  ↓
Tests pass ✓
  ↓
Type check ✓
  ↓
Lint passes ✓
  ↓
Auto-version (2025.11.42)
  ↓
Build signed package ✓
  ↓
Publish to PyPI ✓
```

## 🤖 AI Agent Integration

This template includes comprehensive instructions for AI coding assistants.

### For AI Agents Reading This

Please read these files first:
1. **`AGENTS.md`** - Comprehensive guidelines (read this first!)
2. **`.cursorrules`** - Cursor AI specific instructions  
3. **`.github/copilot-instructions.md`** - Quick reference for Copilot

### Key Points

✅ **DO**:
- Trust the automatic versioning
- Focus on code quality and tests
- Follow existing patterns
- Suggest improvements to docs and examples

❌ **DON'T**:
- Suggest manual version management
- Recommend semantic-release
- Propose git tag-based versioning
- Suggest zero-padding months (project choice)

## 📚 Documentation

- **[TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)**: Comprehensive usage guide
- **[AGENTS.md](AGENTS.md)**: AI agent guidelines
- **[.cursorrules](.cursorrules)**: Cursor AI instructions
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Copilot quick reference

## 🏗️ Project Structure

```
python-library-template/
├── .github/
│   ├── scripts/
│   │   └── set_version.py          # Auto-versioning script
│   ├── workflows/
│   │   └── ci.yml                  # Unified CI/CD workflow
│   └── copilot-instructions.md     # Copilot quick reference
├── src/
│   └── example_package/
│       ├── __init__.py             # Your package (rename this!)
│       └── py.typed                # Type hints marker
├── tests/
│   └── test_default.py             # Test examples
├── docs/                           # Optional documentation
├── .cursorrules                    # Cursor AI instructions
├── AGENTS.md                       # AI agent comprehensive guide
├── TEMPLATE_USAGE.md               # Usage documentation
├── pyproject.toml                  # Project configuration
└── README.md                       # This file
```

## 🔧 Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
# or
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy src/
# or
pyright
```

### Linting

```bash
ruff check .
ruff format .
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## 🎓 Learn More

### Reference Implementations

See these production libraries for examples:

- **[extended-data-types](https://github.com/jbcom/extended-data-types)** - Foundational data types (v2025.11.164)
- **[lifecyclelogging](https://github.com/jbcom/lifecyclelogging)** - Structured logging
- **[directed-inputs-class](https://github.com/jbcom/directed-inputs-class)** - Input processing

### Why CalVer?

- ✅ **Simple**: No commit message conventions required
- ✅ **Predictable**: Every push = new version
- ✅ **Reliable**: No analysis that can fail
- ✅ **Clear**: Version tells you when it was built
- ✅ **Flexible**: Month padding is your choice (we chose no padding)

### Why Auto-Release Everything?

- If it's merged to main, it should be released
- Developers control releases via PR merge
- No "forgot to release" issues
- No complex release workflows
- PyPI handles duplicate versions gracefully

## 🤝 Contributing

Improvements to this template are welcome!

1. Test your changes in a real library first
2. Create a PR with clear description
3. Reference the production library where you tested it
4. Update documentation

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/jbcom/python-library-template/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jbcom/python-library-template/discussions)
- **Documentation**: See [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md)

---

**Template Version**: 1.0.0  
**Status**: Production-Ready  
**Tested**: jbcom ecosystem (3+ libraries)  
**Last Updated**: 2025-11-24

Made with ❤️ for humans and AI agents alike.
