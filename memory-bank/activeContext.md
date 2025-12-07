# Active Context

## Current Status: Issues/Project Synced ✅

All issues are cross-referenced and added to [jbcom Ecosystem Integration Project](https://github.com/users/jbcom/projects/2).

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

## For Next Agent

1. **Wait for PR #16 reviews** to complete
2. Once merged, start AI sub-package (#17)
3. Then Meshy connector (#18)
4. Then agentic-crew repo (#342)
5. Finally agentic-control refactor (#8)

All items tracked in [Project #2](https://github.com/users/jbcom/projects/2).
