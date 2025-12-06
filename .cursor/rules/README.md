# Cursor Background Agent Rules

This directory contains the rules that Cursor's background agent loads **automatically**.

## How Cursor Rules Work

**Cursor reads `.mdc` files from this directory directly - NO REGENERATION needed!**

### File Naming and Load Order

Files are loaded in **numeric then alphabetic order**:

1. `00-loader.mdc` - Project structure, workflow, foundational patterns
2. `05-pr-ownership.mdc` - PR collaboration and AI-to-AI interaction
3. `10-background-agent-conport.mdc` - Memory management with ConPort

Lower numbers = higher priority = loaded first.

### File Format

```markdown
---
alwaysApply: true
description: Brief description
globs: ["**/*"]  # or specific patterns like ["*.py", "*.ts"]
priority: 1      # optional, lower = higher priority
---

# Rule Content

Your markdown content here...
```

## Active Rules

### `00-loader.mdc` (Foundation)
**Always applies to all files**

- Documentation-driven development principles
- Project structure (frontend, python, shared)
- Continuous operation mode
- CrewAI agent guidelines
- Override behaviors

**When to edit:** Project structure changes, workflow changes, new frameworks

### `05-pr-ownership.mdc` (PR Workflow)
**Always applies, priority 1**

- First agent owns PR completely
- AI-to-AI collaboration protocol
- Response templates for different agents
- Handling conflicting feedback
- Merge criteria and process

**When to edit:** PR workflow improvements, new AI agent patterns emerge

### `10-background-agent-conport.mdc` (Memory)
**Always applies to all files**

- ConPort initialization sequence
- MCP tool usage patterns
- Decision and progress logging
- Process-compose integration
- Export/import for review

**When to edit:** ConPort features change, memory strategy evolves

### `REFERENCE-pr-ownership-details.md` (Documentation)
**NOT a rule file - reference only**

- Detailed examples and scenarios
- Extended templates
- Troubleshooting guide
- Complete protocol documentation

**Not loaded by Cursor** - only for agents to reference when needed.

## When to Add New Rules

### Add a new `.mdc` file when:
- ✅ New agent behavior pattern emerges
- ✅ Complex workflow needs formalization
- ✅ Integration with new tool/system
- ✅ Repeated mistakes need prevention

### Choose priority number:
- `00-09`: Foundational (structure, principles)
- `10-19`: Core workflows (memory, state)
- `20-29`: Specific features (testing, deployment)
- `30+`: Optional enhancements

### File naming:
```
<priority>-<descriptive-name>.mdc

Examples:
00-loader.mdc
05-pr-ownership.mdc
10-background-agent-conport.mdc
20-testing-strategy.mdc (if we add)
25-deployment-protocol.mdc (if we add)
```

## Testing Rule Changes

### Immediate Effect
Edit `.mdc` file → Cursor loads it automatically on next action

### Verification
1. Make a small change to test rule
2. Observe Cursor behavior in next interaction
3. Check if rule is being followed
4. Iterate if needed

### Common Issues

**Rule not being followed:**
- Check syntax (YAML frontmatter valid?)
- Check globs (does pattern match your files?)
- Check priority (is another rule overriding?)
- Check placement (is content in right section?)

**Conflicting rules:**
- Lower number wins (00 beats 10)
- More specific glob wins (*.py beats **/* for Python files)
- Later in file takes precedence (within same file)

## Best Practices

### DO:
- ✅ Use clear, specific language
- ✅ Provide examples and templates
- ✅ Explain WHY, not just WHAT
- ✅ Reference specific files/lines when relevant
- ✅ Keep rules focused (one concept per file)

### DON'T:
- ❌ Duplicate content across multiple files
- ❌ Write vague, ambiguous rules
- ❌ Assume context agent doesn't have
- ❌ Mix multiple unrelated concerns in one file
- ❌ Forget to update frontmatter metadata

## Examples

### Good Rule Structure
```markdown
---
alwaysApply: true
description: Security scanning before merge
globs: ["*.py", "*.ts", "*.js"]
---

# Security Scanning Protocol

Before merging any PR, run security scans.

## Tools

Use these in order:
1. `ruff check` for Python
2. `npm audit` for Node.js  
3. `git secrets --scan` for secrets

## Process

\`\`\`bash
# Run all checks
ruff check src/
npm audit
git secrets --scan
\`\`\`

If any fail: Fix before merge, no exceptions.
```

### Bad Rule Structure
```markdown
# Do security stuff

Run tools and fix problems.

# Also do testing

Test things before merge.
```
Why bad:
- No frontmatter
- Vague instructions
- Mixed concerns
- No examples
- No specific tools

## Maintenance

### Regular Review
- **Monthly**: Review rules for clarity
- **After agent mistakes**: Update rules to prevent
- **When tools change**: Update tool references
- **When workflow evolves**: Update process rules

### Version Control
All rule changes go through PR process:
1. Edit `.mdc` file
2. Test in Cursor
3. Create PR
4. Have another agent review (dog-fooding!)
5. Merge when validated

## Documentation

When adding rules, update:
- This README (if structural change)
- `.cursor/README.md` (if user-facing)

## Questions?

- **How rules work**: This file
- **What rules exist**: Read the `.mdc` files
- **Why specific rule**: Check rule's description and content
- **How to change**: Edit `.mdc` file directly, test, PR

---

**Last Updated**: 2025-11-27
**Cursor Version**: Latest (background agent support)
**Rule Count**: 3 active + 1 reference doc
