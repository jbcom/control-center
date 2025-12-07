# Active Context

## Current Status: Agents Spawned on All PRs/Issues ✅

All issues cross-referenced, in project, and have @cursor agents assigned.

### Agent-to-Agent Communication Pattern

Instead of using agentic-control (which we're developing), we use:
```
@cursor comments on PRs/Issues → Spawns background agents
Follow-up @cursor comments → Communicates with spawned agents
```

This avoids chicken-and-egg of using the system while building it.

### Epic Tracking

**[#340](https://github.com/jbcom/jbcom-control-center/issues/340)** - Clarify Surface Scope and Ownership

### Issue Dependency Chain

```
PR #16 (Cursor/Anthropic) ─── IN REVIEW
    │
    ▼
#17 (AI sub-package) ────── OPEN
    │
    ├──────────────────┐
    ▼                  ▼
#18 (Meshy)          #342 (agentic-crew)
                       │
                       ▼
                     #8 (agentic-control refactor)
```

### All Issues (by Repo)

| Repo | Issue | Title | Status |
|------|-------|-------|--------|
| vendor-connectors | #15 | Cursor/Anthropic connectors | PR #16 |
| vendor-connectors | #17 | AI sub-package (LangChain) | Open |
| vendor-connectors | #18 | Meshy connector | Open |
| jbcom-control-center | #340 | EPIC | Open |
| jbcom-control-center | #342 | agentic-crew repo | Open |
| agentic-control | #8 | Vendor-agnostic refactor | Open |

### Architecture Summary

```
Python Ecosystem                    Node.js Ecosystem
────────────────                    ─────────────────
vendor-connectors                   agentic-control
├── ai/ (LangChain)                 ├── protocols/
│   ├── providers/                  ├── orchestration/
│   └── tools/ (auto-gen)           └── providers/
├── cursor/
├── meshy/                          
└── [aws, github, slack...]         
                                    
agentic-crew                        
├── crews/                          
└── tools/ ← uses ai.tools          
```

### Consumer Projects

- **otterfall**: Has `.crewai/` with 8 crews, needs Meshy tool

### Spawned Agents (via @cursor)

| Location | Task | Status |
|----------|------|--------|
| [vendor-connectors PR #16](https://github.com/jbcom/vendor-connectors/pull/16#issuecomment-3621584666) | Complete review cycle | Active |
| [agentic-control PR #7](https://github.com/jbcom/agentic-control/pull/7#issuecomment-3621584907) | Architecture alignment | Active |
| [vendor-connectors #17](https://github.com/jbcom/vendor-connectors/issues/17#issuecomment-3621585018) | Prepare AI sub-package | Waiting (blocked) |
| [vendor-connectors #18](https://github.com/jbcom/vendor-connectors/issues/18#issuecomment-3621585238) | Prepare Meshy connector | Waiting (blocked) |
| [jbcom-control-center #342](https://github.com/jbcom/jbcom-control-center/issues/342#issuecomment-3621585123) | Prepare agentic-crew | Waiting (blocked) |

### To Communicate with Agents

```bash
# Follow up on PR #16
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr comment 16 --repo jbcom/vendor-connectors --body "@cursor <instructions>"

# Follow up on any issue
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh issue comment <num> --repo <repo> --body "@cursor <instructions>"
```

## For Next Agent

1. **Wait for PR #16 reviews** to complete
2. Once merged, start AI sub-package (#17)
3. Then Meshy connector (#18)
4. Then agentic-crew repo (#342)
5. Finally agentic-control refactor (#8)

All items tracked in [Project #2](https://github.com/users/jbcom/projects/2).
