# Agentic Control: Sandbox Execution Proposal

## Vision

Transform `agentic-control` from a fleet management CLI into a **complete local agent orchestration platform** that provides cloud-like isolation and management for AI agents running on local machines.

```
┌─────────────────────────────────────────────────────────────────┐
│                    agentic-control CLI                          │
├─────────────────────────────────────────────────────────────────┤
│  fleet     │  triage    │  sandbox   │  github    │  handoff   │
│  (manage)  │  (recover) │  (execute) │  (integrate)│ (transfer) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Runtime Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent N  │        │
│  │ (Claude) │  │ (Cursor) │  │ (Custom) │  │   ...    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│       │              │              │              │            │
│       ▼              ▼              ▼              ▼            │
│  /workspace     /workspace     /workspace     /workspace        │
│  (mounted)      (mounted)      (mounted)      (mounted)         │
└─────────────────────────────────────────────────────────────────┘
```

## What This Enables

### 1. Local "Cloud Agent" Experience
Run AI agents with complete isolation on your local machine:

```bash
# Spin up an isolated agent for a task
agentic sandbox run \
  --runtime claude \
  --workspace ./my-project \
  --prompt "Refactor the authentication module"

# Run multiple agents in parallel
agentic sandbox fleet \
  --agents 3 \
  --task "Review PR #123 from different perspectives"
```

### 2. Safe Code Execution
All agent-generated code runs in containers:
- No system file modifications
- No unwanted dependency installations
- Complete rollback capability
- Resource limits (CPU, memory, disk)

### 3. Multi-Runtime Support
Support different AI backends in the same fleet:

```yaml
# agentic-sandbox.yml
agents:
  architect:
    runtime: claude
    model: claude-sonnet-4-20250514
    
  reviewer:
    runtime: cursor
    background: true
    
  tester:
    runtime: custom
    image: jbcom/agentic-control:latest
```

### 4. CI/CD Integration
Run sandboxed agents in pipelines:

```yaml
# .github/workflows/ai-review.yml
- name: AI Code Review
  run: |
    agentic sandbox run \
      --runtime claude \
      --agent code-reviewer \
      --workspace ${{ github.workspace }} \
      --output review.md
```

## Proposed Module Structure

```
src/
├── sandbox/
│   ├── index.ts           # Public API
│   ├── container.ts       # Docker container lifecycle
│   ├── runtime/
│   │   ├── base.ts        # Abstract runtime interface
│   │   ├── claude.ts      # Claude Code runtime
│   │   ├── cursor.ts      # Cursor agent runtime
│   │   └── custom.ts      # Custom Dockerfile runtime
│   ├── workspace.ts       # Volume mounting & file sync
│   ├── output.ts          # Output extraction
│   └── config.ts          # Sandbox configuration
```

## CLI Commands

### `agentic sandbox run`
Execute a single agent in isolation:

```bash
agentic sandbox run [options]

Options:
  --runtime <type>     Runtime: claude, cursor, custom (default: claude)
  --workspace <path>   Directory to mount (default: .)
  --output <path>      Output directory (default: .agentic/output)
  --prompt <text>      Task prompt
  --agent <name>       Pre-built agent template
  --timeout <seconds>  Execution timeout (default: 300)
  --memory <mb>        Memory limit (default: 2048)
  --yes                Skip confirmation
```

### `agentic sandbox fleet`
Run multiple agents in parallel:

```bash
agentic sandbox fleet [options]

Options:
  --config <file>      Fleet configuration YAML
  --agents <n>         Number of parallel agents
  --task <text>        Shared task for all agents
  --merge              Merge outputs into single result
```

### `agentic sandbox build`
Build custom runtime image:

```bash
agentic sandbox build [options]

Options:
  --dockerfile <path>  Custom Dockerfile
  --tag <name>         Image tag
  --push               Push to registry
```

## Key Differences from claude-code-templates

| Feature | claude-code-templates | agentic-control sandbox |
|---------|----------------------|------------------------|
| Scope | Single agent execution | Fleet orchestration |
| Runtimes | Claude only | Multi-runtime (Claude, Cursor, custom) |
| Management | One-shot | Persistent fleet management |
| Triage | None | Full triage & recovery |
| Integration | Standalone | Integrates with GitHub, handoff |
| Output | Simple copy | Structured artifacts |
| Monitoring | Basic | Fleet dashboard |

## Implementation Phases

### Phase 1: Core Sandbox (MVP)
- [ ] Docker container lifecycle management
- [ ] Workspace volume mounting
- [ ] Claude runtime support
- [ ] Basic output extraction
- [ ] `agentic sandbox run` command

### Phase 2: Multi-Runtime
- [ ] Cursor background agent runtime
- [ ] Custom Dockerfile support
- [ ] Runtime detection and configuration
- [ ] Environment variable management

### Phase 3: Fleet Orchestration
- [ ] Parallel agent execution
- [ ] Fleet configuration YAML
- [ ] Output merging strategies
- [ ] Resource pooling

### Phase 4: Advanced Features
- [ ] Persistent agents (long-running containers)
- [ ] Agent-to-agent communication
- [ ] Checkpoint/restore
- [ ] Fleet dashboard UI

## Docker Image Updates

The `jbcom/agentic-control` image would serve dual purposes:

1. **As a base image** for custom agents
2. **As a runtime** for the sandbox itself

Updated Dockerfile additions:

```dockerfile
# Add Claude Agent SDK for Claude runtime
RUN npm install -g @anthropic-ai/claude-agent-sdk

# Add sandbox execution script
COPY sandbox/execute.js /app/sandbox/execute.js

# Support both CLI and sandbox modes
ENTRYPOINT ["/app/entrypoint.sh"]
```

## Environment Variables

```bash
# API Keys (for respective runtimes)
ANTHROPIC_API_KEY=sk-ant-...
CURSOR_API_KEY=...

# Sandbox configuration
AGENTIC_SANDBOX_RUNTIME=claude
AGENTIC_SANDBOX_TIMEOUT=300
AGENTIC_SANDBOX_MEMORY=2048
AGENTIC_SANDBOX_OUTPUT=/output
```

## Security Considerations

1. **Non-root execution**: All containers run as `agent` user (UID 1000)
2. **Read-only mounts**: Workspace mounted read-only by default
3. **Network isolation**: Optional `--no-network` flag
4. **Resource limits**: CPU, memory, disk quotas
5. **Capability dropping**: Minimal Linux capabilities
6. **Secrets management**: API keys passed via Docker secrets, not env

## Competitive Advantage

This positions agentic-control as:

- **For developers**: Local AI agent sandbox with zero cloud dependency
- **For teams**: Fleet management for AI-assisted development
- **For CI/CD**: Safe AI code generation in pipelines
- **For enterprises**: Isolated, auditable AI agent execution

Unlike cloud-based solutions:
- ✅ Complete data privacy (runs locally)
- ✅ No per-execution costs (beyond API calls)
- ✅ Full customization of runtime environment
- ✅ Integration with existing Docker infrastructure
