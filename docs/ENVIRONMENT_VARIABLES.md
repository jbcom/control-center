# Environment Variable Priority Documentation

## Overview

All packages in this monorepo now support **COPILOT_MCP_* prefixed environment variables** with proper fallback to standard names. This enables seamless testing in both Copilot agent and standard development environments.

## Priority Order

All environment variable lookups follow this consistent pattern:

```typescript
const apiKey = options.apiKey ?? process.env.COPILOT_MCP_CURSOR_API_KEY ?? process.env.CURSOR_API_KEY
```

**Priority:**
1. **Explicit parameter** - Passed to constructor/function
2. **COPILOT_MCP_* prefix** - For testing in Copilot agent environment
3. **Standard name** - For regular development/production

## Supported Environment Variables

### Cursor API

| COPILOT_MCP Prefix | Standard Name | Usage |
|-------------------|---------------|-------|
| `COPILOT_MCP_CURSOR_API_KEY` | `CURSOR_API_KEY` | Cursor Background Agent API access |

**Used in:**
- `packages/agentic-control/src/cursor-api.ts`
- `packages/agentic-control/src/mcp-client.ts`
- `packages/ai-triage/src/mcp-clients.ts`

### GitHub

| COPILOT_MCP Prefix | Standard Names | Usage |
|-------------------|----------------|-------|
| `COPILOT_MCP_GITHUB_TOKEN` | `GITHUB_TOKEN`, `CI_GITHUB_TOKEN` | GitHub API, PR operations, MCP server |

**Used in:**
- `packages/agentic-control/src/fleet.ts`
- `packages/agentic-control/src/handoff.ts`
- `packages/agentic-control/src/ai-analyzer.ts`
- `packages/ai-triage/src/mcp-clients.ts`

### Anthropic

| COPILOT_MCP Prefix | Standard Name | Usage |
|-------------------|---------------|-------|
| `COPILOT_MCP_ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | Claude AI analysis, code review, triage |

**Used in:**
- `packages/agentic-control/src/ai-analyzer.ts`

### Context7 (Optional)

| COPILOT_MCP Prefix | Standard Name | Usage |
|-------------------|---------------|-------|
| `COPILOT_MCP_CONTEXT7_API_KEY` | `CONTEXT7_API_KEY` | Documentation lookup (optional) |

**Used in:**
- `packages/ai-triage/src/mcp-clients.ts`

## Usage Examples

### Development Environment

```bash
# Standard environment variables
export CURSOR_API_KEY="your-cursor-key"
export GITHUB_TOKEN="your-github-token"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Run tools
agentic-control list
ai-triage mcp status
```

### Copilot Agent Environment

```bash
# COPILOT_MCP_* variables are automatically injected
# Listed in: COPILOT_AGENT_INJECTED_SECRET_NAMES

# Run the same tools - they automatically use COPILOT_MCP_* versions
agentic-control list
ai-triage mcp status
```

### Testing Priority

```typescript
// You can test the priority order:
import { CursorAPI } from "@jbcom/agentic-control";

// 1. Explicit parameter (highest priority)
const api1 = new CursorAPI({ apiKey: "explicit-key" });

// 2. COPILOT_MCP_CURSOR_API_KEY (if set)
process.env.COPILOT_MCP_CURSOR_API_KEY = "copilot-key";
const api2 = new CursorAPI();  // Uses COPILOT_MCP_CURSOR_API_KEY

// 3. CURSOR_API_KEY (fallback)
delete process.env.COPILOT_MCP_CURSOR_API_KEY;
process.env.CURSOR_API_KEY = "standard-key";
const api3 = new CursorAPI();  // Uses CURSOR_API_KEY
```

## Implementation Pattern

### Constructor Pattern

```typescript
export class MyClass {
  private apiKey: string;

  constructor(options: { apiKey?: string } = {}) {
    // Priority: options > COPILOT_MCP_* > standard
    this.apiKey = options.apiKey
      ?? process.env.COPILOT_MCP_API_KEY
      ?? process.env.STANDARD_API_KEY
      ?? "";

    if (!this.apiKey) {
      throw new Error("API_KEY is required");
    }
  }
}
```

### Inline Pattern

```typescript
async function doSomething(config: Config) {
  const token = config.token
    ?? process.env.COPILOT_MCP_GITHUB_TOKEN
    ?? process.env.GITHUB_TOKEN
    ?? process.env.CI_GITHUB_TOKEN;
}
```

## Verification

### Check Configuration

```bash
# List available COPILOT_MCP variables
env | grep COPILOT_MCP_

# Check which secrets are configured for injection
echo $COPILOT_AGENT_INJECTED_SECRET_NAMES
```

### Test MCP Connectivity

```bash
# Check MCP server status (shows which env vars are set)
cd packages/ai-triage
npm run build
node dist/cli.js mcp status
```

Expected output:
```
🔍 Checking MCP servers...

✅ Cursor Agent MCP
   Environment: COPILOT_MCP_CURSOR_API_KEY or CURSOR_API_KEY (set)
✅ GitHub MCP
   Environment: COPILOT_MCP_GITHUB_TOKEN or GITHUB_TOKEN (set)
⚠️ Context7 MCP
   Environment: CONTEXT7_API_KEY (optional) (not set)
```

## Benefits

### For Copilot Agents
- ✅ **No manual configuration needed** - COPILOT_MCP_* variables auto-injected
- ✅ **Same commands work** - No special flags or options required
- ✅ **Isolated from production** - Separate API keys for testing
- ✅ **Consistent behavior** - Same priority order everywhere

### For Developers
- ✅ **Backward compatible** - Standard env var names still work
- ✅ **Flexible** - Can override with explicit parameters
- ✅ **Clear priority** - Predictable behavior

### For CI/CD
- ✅ **Easy to configure** - Use whichever naming convention fits
- ✅ **Secure** - Secrets managed by GitHub/platform
- ✅ **Testable** - Can inject COPILOT_MCP_* for testing

## Troubleshooting

### "API_KEY is required" Error

**Problem:** Code can't find API key

**Solution:** Check priority order
```bash
# 1. Is explicit parameter passed?
# 2. Is COPILOT_MCP_* version set?
env | grep COPILOT_MCP_CURSOR_API_KEY
# 3. Is standard version set?
env | grep CURSOR_API_KEY
```

### Wrong API Key Used

**Problem:** Using wrong account/key

**Solution:** Check priority - explicit parameter overrides environment
```typescript
// Force use of specific key
const api = new CursorAPI({ apiKey: "specific-key" });

// Or temporarily unset COPILOT_MCP_* version
delete process.env.COPILOT_MCP_CURSOR_API_KEY;
```

### Secrets Not Available

**Problem:** COPILOT_MCP_* variables not set

**Cause:** Secrets are configured but not injected in this environment

**Check:**
```bash
# Are they configured?
echo $COPILOT_AGENT_INJECTED_SECRET_NAMES

# Are they actually set?
env | grep COPILOT_MCP_
```

**Solution:** Secrets may only be available in specific contexts (e.g., when agent is invoked with MCP enabled). Fall back to standard env vars for now.

## Migration Guide

### Updating Existing Code

If you have code that directly reads environment variables:

**Before:**
```typescript
const apiKey = process.env.CURSOR_API_KEY;
```

**After:**
```typescript
const apiKey = process.env.COPILOT_MCP_CURSOR_API_KEY ?? process.env.CURSOR_API_KEY;
```

### Adding New Environment Variables

When adding support for a new service:

1. **Define both names** in type definitions
2. **Use priority pattern** in constructor
3. **Document** in this file
4. **Update** CLI help text if applicable

Example:
```typescript
// 1. Type definition
export interface NewServiceConfig {
  apiKey?: string;
}

// 2. Priority pattern
constructor(config: NewServiceConfig = {}) {
  this.apiKey = config.apiKey
    ?? process.env.COPILOT_MCP_NEWSERVICE_API_KEY
    ?? process.env.NEWSERVICE_API_KEY
    ?? "";
}

// 3. Document in this file under "Supported Environment Variables"

// 4. Update CLI help
console.log("Set COPILOT_MCP_NEWSERVICE_API_KEY or NEWSERVICE_API_KEY");
```

## References

- **Copilot Agent Injection:** `COPILOT_AGENT_INJECTED_SECRET_NAMES` environment variable
- **agentic-control package:** `packages/agentic-control/README.md`
- **ai-triage package:** `packages/ai-triage/package.json`
- **Investigation:** `packages/agentic-control/docs/FOLLOWUP_INVESTIGATION.md`

---

**Last Updated:** 2024-11-30
**Maintainer:** @copilot, @jbcom
