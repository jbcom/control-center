# Control Center Crew Directory

This directory contains CrewAI agent and task configurations for the jbcom-control-center.

## Architecture

```
                    ┌─────────────────────┐
                    │   agentic-control   │
                    │  (TypeScript core)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   agentic-triage    │
                    │    (primitives)     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐          ┌─────▼─────┐         ┌─────▼─────┐
    │ Triage  │          │ Ecosystem │         │ Planning  │
    │ Agents  │          │  Agents   │         │  Agents   │
    └─────────┘          └───────────┘         └───────────┘
```

## Agent Categories

### Triage Agents
- **triage_assessor**: Analyzes incoming issues and PRs
- **pr_reviewer**: Reviews code quality and breaking changes

### Ecosystem Agents
- **dependency_tracker**: Manages cross-repo dependency graph
- **sync_coordinator**: Ensures consistent repository configuration

### Planning Agents
- **sprint_planner**: Organizes weekly sprints
- **roadmap_curator**: Maintains quarterly roadmap

## Usage

These agents are invoked via `agentic-control` CLI or programmatically:

```bash
# Using agentic-control CLI (once Issue #22 is resolved)
npx agentic-control triage assess <issue-number>
npx agentic-control triage review <pr-number>

# Ecosystem operations
npx agentic-control ecosystem sync --dry-run
npx agentic-control ecosystem health

# Sprint planning
npx agentic-control sprint plan
npx agentic-control roadmap update
```

## Configuration Files

| File | Purpose |
|------|---------|
| `config/agents.yaml` | Agent role definitions, goals, and tool bindings |
| `config/tasks.yaml` | Task descriptions and expected outputs |

## Integration with Workflows

The GitHub Actions workflows in `.github/workflows/` invoke these agents:

- **agentic-triage.yml** → Uses triage agents for cross-repo operations
- **triage.yml** → Uses triage agents for this repo specifically
- **ecosystem-sync.yml** → Uses sync_coordinator agent

## Dependencies

This crew requires:
- `agentic-control` - Core control and orchestration
- `agentic-triage` - Tool primitives (consumed by agentic-control)
- `agentic-crew` - CrewAI execution framework (for Python crews)

## Related Issues

- jbcom/agentic-control#22 - Add agentic-triage as dependency
- jbcom/agentic-control#28 - Monitor npm releases
- jbcom/agentic-control#29 - Improve fleet agent spawning
