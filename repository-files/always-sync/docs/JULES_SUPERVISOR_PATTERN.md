# Jules Supervisor Pattern

This document outlines the pattern for Cursor Cloud Agents to supervise Jules sessions and handle the full pull request lifecycle.

## Environment Variables Available

Future Cursor Cloud Agents will have access to the following environment variables:

| Variable              | Purpose                   |
|-----------------------|---------------------------|
| `JULES_API_KEY`       | Google Jules API access   |
| `CURSOR_GITHUB_TOKEN` | GitHub API access for merges |

## Orchestration Pattern

The supervision of Jules sessions by a Cursor Cloud Agent follows this pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                  CURSOR CLOUD AGENT                         │
│                    (Supervisor)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. List active Jules sessions                              │
│     GET /v1alpha/sessions                                   │
│                                                             │
│  2. Check session status                                    │
│     GET /v1alpha/sessions/{id}                              │
│                                                             │
│  3. When COMPLETED with PR:                                 │
│     - Check PR CI status                                    │
│     - Review AI feedback                                    │
│     - Handle any failing checks                             │
│     - Merge when ready                                      │
│                                                             │
│  4. For complex work, spawn additional:                     │
│     - Jules sessions (async refactoring)                    │
│     - Cursor Cloud Agents (long-running tasks)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Script Created

The orchestration logic is encapsulated in the following script:

**Location:** `/workspace/scripts/cursor-jules-orchestrator.mjs`

```javascript
// Usage by future Cursor agents:
// node scripts/cursor-jules-orchestrator.mjs
```

*Note: This script will be integrated into the `agentic-control` repository as a proper module.*

## Cursor Cloud Agent Spawning

Future agents can spawn additional agents to delegate or parallelize tasks:

```bash
# Example: Spawn an agent to monitor a specific repository
curl -X POST 'https://api.cursor.com/agents/launch' \
  -u "$CURSOR_API_KEY:" \
  -d '{
    "repository": "jbcom/nodejs-strata",
    "task": "Monitor Jules PRs, handle reviews, merge when ready",
    "branch": "main"
  }'
```

## Workflow

The end-to-end workflow is as follows:

1.  **Jules Creates PR**: A Jules session completes and a pull request is created. The session state transitions to `COMPLETED`.
2.  **Cursor Agent Detects**: The supervisor agent detects the completed session and the associated PR.
3.  **CI Status Check**: The agent checks the CI status of the PR.
4.  **Handle Failures**: If CI fails, the agent can either attempt to fix the issues directly or spawn a new Jules session to address them.
5.  **Address Feedback**: If there is AI-generated feedback on the PR, the agent will process and address the comments.
6.  **Merge When Ready**: Once all checks pass and feedback is addressed, the agent merges the pull request.
7.  **Handle Complexity**: For complex scenarios, the agent can spawn sub-agents (either Jules sessions or other Cursor Cloud Agents) to handle specific sub-tasks.
