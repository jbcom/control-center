# Triage Hub

The **agentic-triage** workflow keeps jbcom issues and pull requests synchronized across OSS repositories. This guide explains how CI locates downstream documentation (Python/TypeScript/Go/Rust), how MCP-prefixed environment variables are resolved, and how automation pushes triage results into the Roadmap and Integration projects.

## Workflow entry points
- **Issue intake**: `.github/workflows/triage.yml` runs `agentic-triage assess` on newly opened issues to attach labels/metadata for routing.
- **PR review**: the same workflow runs `agentic-triage review` on non-draft pull requests.
- **Automation commands**: manual dispatch supports `sprint`, `roadmap`, `cascade`, and `security` for the repositories in the workflow matrix (`jbdevprimary/strata`, `agentic-control`, `agentic-crew`, `agentic-triage`, `vendor-connectors`). Scheduled runs reuse the matrix to refresh triage data before project routing.

## Documentation discovery across languages
1. **Initialize submodules**: run `git submodule update --init --recursive` so `ecosystems/oss/` contains the downstream packages defined in `.gitmodules`.
2. **Language-specific doc roots** (available after checkout):
   - **TypeScript**: `ecosystems/oss/agentic-control/` (CLI and automation) and `ecosystems/oss/agentic-triage/` expose `README` and `/docs` content consumed by the workflow.
   - **Python**: `ecosystems/oss/agentic-crew/` (crew orchestration) and `ecosystems/oss/vendor-connectors/` (provider plugins) provide `README` and `/docs` folders used for prompt and guidance lookup.
   - **Go / Rust**: new submodules under `ecosystems/oss/<repo>/` follow the same pattern; once the repo is checked out, `agentic-triage` traverses `README` and `/docs` directories so language-agnostic lookups keep working without extra cloning.
3. **Lookup strategy**: during CI runs, `agentic-triage` reads those checked-out paths locally, so language documentation is available to the action without hitting the network.

## MCP-aware environment variables
- All downstream packages honor the precedence defined in `docs/ENVIRONMENT_VARIABLES.md`: CLI flags and explicit options win, then `COPILOT_MCP_*` variables (e.g., `COPILOT_MCP_CURSOR_API_KEY`, `COPILOT_MCP_GITHUB_TOKEN`, `COPILOT_MCP_ANTHROPIC_API_KEY`), then the standard names (`CURSOR_API_KEY`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, etc.). This allows Copilot sandboxes and standard runners to share the same workflows.
- Use the environment variable guide’s `env | grep COPILOT_MCP_` and `agentic-triage mcp status` checks before manual dispatch to confirm MCP servers and GitHub access resolve correctly.

## Routing to Roadmap and Integration projects
- **Roadmap ingestion**: `agentic-triage assess` enriches new issues with labels that downstream automation uses to create or update Roadmap project items; `agentic-triage roadmap` can be manually dispatched for targeted backlog generation.
- **Integration flow**: PR reviews (`agentic-triage review`) and cascade runs (`agentic-triage cascade`) collect dependency and test signals that Integration board automation expects. The sprint matrix keeps OSS repos aligned so tickets can move between Roadmap and Integration as the issue lifecycle progresses.
