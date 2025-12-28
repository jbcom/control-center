# 📅 Roadmap Milestones: Balanced Ecosystem Development

## Problem

The Roadmap project was heavily biased toward **strata** development (28 of 28 open issues were strata).

This has been rebalanced, and this issue defines milestone phases to ensure all ecosystem areas get appropriate attention.

---

## Milestone Structure

### M1: Foundation (Infrastructure & Tooling) 🔧
**Priority:** Unblock all other work
**Target:** 2 weeks

| Issue | Repo | Description |
|-------|------|-------------|
| #395 | jbcom-control-center | Purify agentic-control, create .crew layers |
| #340 | jbcom-control-center | Clarify Agentic Ecosystem Scope |
| #22 | agentic-control | Add agentic-triage integration |
| #8 | agentic-triage | MCP Server for Claude/Cursor |
| #185 | strata | CI/CD & Infrastructure |
| #189 | strata | Fix Coveralls |

### M2: AI Tooling (vendor-connectors + agentic-crew) 🤖
**Priority:** Enable AI-powered development
**Target:** 3 weeks

| Issue | Repo | Description |
|-------|------|-------------|
| #51-55 | vendor-connectors | AI tools for all connectors |
| #19 | agentic-crew | connector_builder crew |
| #9-10 | agentic-triage | Jira + Linear providers |
| #61 | extended-data-types | MCP Server |
| #11 | directed-inputs-class | Release v1.1.0 |

### M3: Educational Platform (Professor Pixel) 🎓
**Priority:** pixels-pygame-palace as primary
**Target:** 3 weeks

| Issue | Repo | Description |
|-------|------|-------------|
| #351 | jbcom-control-center | Unify Professor Pixel |
| #12 | pixels-pygame-palace | Become primary frontend |
| #11 | pixels-pygame-palace | agentic-crew integration |
| #18-19 | ai_game_dev | Extract patterns, then archive |

### M4: Game Development (strata + games) 🎮
**Priority:** Procedural generation + game integrations
**Target:** Ongoing

| Issue | Repo | Description |
|-------|------|-------------|
| #349 | jbcom-control-center | [Game Dev Ecosystem Integration](GAME-DEV-ECOSYSTEM-INTEGRATION.md) |
| #179-184 | strata | EPICs (Materials, Biomes, Creatures, etc.) |
| #70-71 | otter-river-rush | strata + agentic-crew |
| #6 | otterfall | agentic-crew integration |
| TBD | rivermarsh | strata integration |

---

## Balance Check

| Milestone | Strata Issues | Non-Strata Issues |
|-----------|---------------|-------------------|
| M1 | 2 | 4 |
| M2 | 0 | 7 |
| M3 | 0 | 4 |
| M4 | 6+ | 3+ |

This ensures infrastructure, AI tooling, and education get proper focus before heavy strata development.

---

## Dependencies

```
M1 (Foundation)
  └─→ M2 (AI Tooling)
        └─→ M3 (Educational)
              └─→ M4 (Game Dev)
```

M1 must complete first to enable crew orchestration across the ecosystem.
