# Agent Self-Sufficiency Rules

**CRITICAL: Read this when you encounter "command not found" or missing tools**

## Core Principle: Tools Should Exist, Use Them

If you encounter a missing tool or command, it usually means ONE of three things:

1. **Tool is in Dockerfile but environment not rebuilt** → Document for user
2. **Tool should be in Dockerfile but isn't** → ADD IT
3. **Tool is non-standard and shouldn't be assumed** → Use alternatives

## Decision Tree: Missing Tool

```
Tool not found
    ↓
Is tool listed in .cursor/TOOLS_REFERENCE.md?
    ├─ YES → Environment needs rebuild
    │         → Document in PR/commit: "Requires Docker rebuild"
    │         → Continue with workarounds if possible
    │
    └─ NO → Should this tool be available?
              ├─ YES → ADD to Dockerfile immediately
              │         → Common tools (see list below)
              │         → Document why it's needed
              │
              └─ NO → Use standard alternatives
                        → python/node/rust/go standard library
                        → Tools already in environment
```

## Common Tools That MUST Be Available

### Always Available (Core System)
```bash
# These should ALWAYS work
python --version
node --version  
git --version
bash --version
sh --version
```

### Should Be Available (In Dockerfile)
```bash
# Package managers
pip, uv, pnpm, cargo, go

# Code search
rg (ripgrep), fd, ast-grep

# Data processing  
jq, yq, sqlite3

# Git operations
git, git-lfs, gh, delta, lazygit

# Process management
process-compose, htop, ps, top

# Text processing
bat, exa, vim, nano

# Development
pytest, mypy, ruff, pre-commit

# Agent tools
ruler (for applying agent config changes)
```

### Never Assume Available
```bash
# Don't assume these exist
docker (we're INSIDE docker)
kubectl, helm (cluster tools)
aws, gcloud, az (cloud CLIs - use vendor-connectors)
terraform, pulumi (IaC tools)
```

## When to Add Tools to Dockerfile

### ✅ ADD IMMEDIATELY
- **Standard development tools** everyone needs
- **Security tools** for vulnerability scanning
- **Performance tools** for profiling/debugging
- **Agent management tools** (ruler, etc.)
- **Tools required by project rules** (ripgrep is REQUIRED per .cursorrules)

### ⚠️ ADD WITH JUSTIFICATION
- **Language-specific tools** (add to appropriate section)
- **Build tools** for specific frameworks
- **Testing tools** beyond pytest
- **Database clients** beyond sqlite3

### ❌ DON'T ADD
- **Project-specific tools** (install via package.json/pyproject.toml)
- **One-off utilities** (download in CI or use alternatives)
- **Deprecated tools** (find modern alternatives)
- **Redundant tools** (if we have ripgrep, don't add grep alternatives)

## How to Add Tools to Dockerfile

### Pattern 1: System Package (apt)
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tool-name \
    && rm -rf /var/lib/apt/lists/*
```

**Examples**: jq, vim, htop, ripgrep

### Pattern 2: Python Package (pip)
```dockerfile
RUN pip install --no-cache-dir \
    package-name>=X.Y.Z
```

**Examples**: pytest, mypy, ruff

### Pattern 3: Node.js Package (pnpm)
```dockerfile
RUN pnpm install -g \
    package-name
```

**Examples**: @intellectronica/ruler, typescript

### Pattern 4: Rust Tool (cargo)
```dockerfile
RUN cargo install --locked \
    tool-name \
    && rm -rf $CARGO_HOME/registry
```

**Examples**: ripgrep, fd-find, bat, exa

### Pattern 5: Go Tool (go install)
```dockerfile
RUN go install github.com/user/tool@latest
```

**Examples**: yq, lazygit, glow

### Pattern 6: Binary Download
```dockerfile
ENV TOOL_VERSION="vX.Y.Z"
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/user/tool/releases/download/${TOOL_VERSION}/tool-linux-${ARCH}" \
    -o /usr/local/bin/tool && \
    chmod +x /usr/local/bin/tool && \
    tool --version
```

**Examples**: process-compose

## Update Dockerfile Process

When you add a tool:

1. **Choose the right section** in Dockerfile
2. **Add with comment** explaining why
3. **Verify in verification step** at end of Dockerfile
4. **Update TOOLS_REFERENCE.md** with usage examples
5. **Update ENVIRONMENT_ANALYSIS.md** if significant
6. **Document in PR** that Docker rebuild required

### Example: Adding jq (already done correctly)

```dockerfile
# In SYSTEM DEPENDENCIES section
RUN apt-get update && apt-get install -y --no-install-recommends \
    # ... other tools ...
    # JSON/YAML processing
    jq \
    # ... more tools ...
```

```dockerfile
# In FINAL VERIFICATION section  
RUN echo "=== VERIFICATION ===" && \
    # ... other checks ...
    jq --version && \
    # ... more checks ...
```

### Example: Adding ruler (just added)

```dockerfile
# In NODE.JS GLOBAL TOOLS section
RUN pnpm install -g \
    # Ruler - Agent instruction management
    @intellectronica/ruler \
    && ruler --version
```

## Workarounds When Tool Unavailable

### If jq not available
```bash
# Use python instead
python -c "import json, sys; print(json.load(sys.stdin)['key'])" < file.json

# Or for GitHub API
gh api endpoint --jq '.key'  # gh has built-in jq
```

### If yq not available
```bash
# Use python with ruamel.yaml
python -c "import sys; from ruamel.yaml import YAML; yaml=YAML(); print(yaml.load(sys.stdin)['key'])" < file.yaml
```

### If ripgrep not available
```bash
# Fallback to grep (much slower)
grep -r "pattern" .

# But really, add ripgrep - it's REQUIRED by rules
```

### If ruler not available
```bash
# Manual concatenation (not ideal)
cat .ruler/AGENTS.md .ruler/copilot.md .ruler/cursor.md > .cursorrules

# But really, just add ruler to Dockerfile
```

## Self-Healing: Apply Your Own Changes

When you identify a missing tool:

1. **Add it to Dockerfile** immediately (this PR or next commit)
2. **Update documentation** (TOOLS_REFERENCE.md)
3. **Apply agent config changes** with ruler (see below)
4. **Note in commit message**: "Adds <tool> to environment (discovered missing during <task>)"
5. **Verify addition** in verification step
6. **Test locally if possible** or note that rebuild required

### Applying Agent Configuration Changes

**CRITICAL: Cursor reads from `.cursor/rules/*.mdc` files, NOT `.cursorrules`**

When you update agent rules in `.ruler/*.md`:

```bash
# Apply ruler to regenerate all agent configs
ruler apply

# This updates:
# - .cursorrules (for legacy Cursor)
# - .github/copilot-instructions.md (for Copilot)  
# - AGENTS.md (for Aider)
# - .claud (for Claude)
```

**For Cursor background agent, edit these directly:**
- `.cursor/rules/00-loader.mdc` - Project structure and workflow
- `.cursor/rules/05-pr-ownership.mdc` - PR collaboration protocol
- `.cursor/rules/10-background-agent-conport.mdc` - Memory management

**Cursor loads `.mdc` files automatically - no regeneration needed!**

### Example Commit Message
```
build: add ruler to Docker environment

Discovered during PR workflow when attempting to apply agent config
changes. Ruler is essential for maintaining .cursorrules and other
agent-specific configs.

Added as Node.js global via pnpm in NODE.JS GLOBAL TOOLS section.

Requires Docker rebuild: docker build -f .cursor/Dockerfile .
```

## Documentation Updates

When adding tools, update:

### .cursor/TOOLS_REFERENCE.md
```markdown
## New Tool Section

\`\`\`bash
tool-name command            # Description
tool-name --help             # Show help
\`\`\`

### Common Workflows
- Use case 1
- Use case 2
```

### .cursor/ENVIRONMENT_ANALYSIS.md
If significant addition:
```markdown
## Tool Requirements (Update)

### New Category
**New tool** (added YYYY-MM-DD)
- Purpose: Why it's needed
- Installation: How it's installed
- Workflow: What workflow it supports
```

## Anti-Patterns

### ❌ Silently Fail
```bash
# Bad: Silently skip if tool missing
which tool && tool command || echo "Skipped"

# Good: Fail explicitly
if ! which tool > /dev/null; then
    echo "ERROR: tool not found. Add to .cursor/Dockerfile"
    exit 1
fi
```

### ❌ Install Locally
```bash
# Bad: Install in running container (non-persistent)
apt-get install tool

# Good: Add to Dockerfile (persists across rebuilds)
# Edit .cursor/Dockerfile, document rebuild needed
```

### ❌ Assume User Has Tool
```bash
# Bad: Assume tool on user's machine
docker run --rm -v $(which tool):/usr/local/bin/tool ...

# Good: Tool should be in Docker image
# Add to Dockerfile
```

### ❌ Use Obscure Tools
```bash
# Bad: Use tool nobody has heard of
obscure-json-parser file.json

# Good: Use standard, well-known tools
jq '.' file.json
```

## Verification Checklist

Before committing Dockerfile changes:

- [ ] Tool added to appropriate section (system deps, python, node, rust, go)
- [ ] Comment explains why tool is needed
- [ ] Version pinned if critical for reproducibility
- [ ] Verification step updated (tool --version check)
- [ ] TOOLS_REFERENCE.md updated with usage
- [ ] ENVIRONMENT_ANALYSIS.md updated if significant
- [ ] Commit message notes Docker rebuild required
- [ ] PR description includes rebuild instructions

## Common Scenarios

### Scenario 1: "ruler: command not found"
**Analysis**: ruler is agent management tool, should be available
**Action**: Add to Dockerfile as Node.js global
**Documentation**: Update TOOLS_REFERENCE.md
**Result**: ✅ Done (just added)

### Scenario 2: "jq: command not found"  
**Analysis**: jq is standard JSON tool, listed in Dockerfile but not in current environment
**Action**: Document rebuild needed, continue with python fallback
**Documentation**: Note in commit/PR
**Result**: ⏳ Rebuild required

### Scenario 3: "custom-parser: command not found"
**Analysis**: Project-specific tool, not general-purpose
**Action**: Don't add to Dockerfile, install via package manager in project
**Documentation**: Add to README for that package
**Result**: ✅ Correct approach

### Scenario 4: "docker: command not found"
**Analysis**: We're inside Docker, can't use Docker
**Action**: This is expected, find alternative approach
**Documentation**: Document why Docker-in-Docker not supported
**Result**: ✅ Use different approach

## Summary

1. **Expect tools to exist** - Dockerfile should be comprehensive
2. **Add missing common tools** - Don't work around, fix root cause
3. **Document additions** - Help future agents understand why
4. **Update references** - Keep TOOLS_REFERENCE.md current
5. **Test verification** - Ensure tool checks in Dockerfile work
6. **Self-heal** - You can fix your own environment

**The agent environment should be complete enough that you rarely encounter "command not found" for standard development tasks.**

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-27  
**Related**: `.cursor/Dockerfile`, `.cursor/TOOLS_REFERENCE.md`
