# Enterprise Oversight Dashboard

**Overseer**: Cloud Agent (Claude)
**Last Updated**: 2025-12-29
**Scope**: All jbcom organizations

---

## 🏢 Organization Overview

| Organization | Purpose | Repos | Active PRs |
|--------------|---------|-------|------------|
| **jbcom** | Personal/Control | 4 | 0 |
| **strata-game-library** | Game dev library | 11 | 7 |
| **agentic-dev-library** | AI dev tools | 7 | 4 |
| **extended-data-library** | Data utilities | 6 | 2 |
| **arcade-cabinet** | Games | 10 | 30+ |

---

## 🔴 Critical - ESM Migration Wave

All TypeScript packages need tsup migration for Node.js ESM support.

### strata-game-library
| Package | PR | Status |
|---------|-----|--------|
| presets | [#12](https://github.com/strata-game-library/presets/pull/12) | @cursor reviewing |
| core | [#129](https://github.com/strata-game-library/core/pull/129) | **Merged** |
| shaders | [#17](https://github.com/strata-game-library/shaders/pull/17) | Open |
| audio-synth | [#3](https://github.com/strata-game-library/audio-synth/pull/3) | Open |
| react-native-plugin | [#22](https://github.com/strata-game-library/react-native-plugin/pull/22) | Open |
| capacitor-plugin | [#22](https://github.com/strata-game-library/capacitor-plugin/pull/22) | Open |

### agentic-dev-library
| Package | PR | Status |
|---------|-----|--------|
| control | [#42](https://github.com/agentic-dev-library/control/pull/42) | Open |
| triage | [#76](https://github.com/agentic-dev-library/triage/pull/76) | Open |

### extended-data-library
| Package | PR | Status |
|---------|-----|--------|
| core | [#22](https://github.com/extended-data-library/core/pull/22) | CI fix needed |

---

## 🟡 High Priority - Feature Work

### strata-game-library
| Repo | PR | Description |
|------|-----|-------------|
| presets | [#14](https://github.com/strata-game-library/presets/pull/14) | Comprehensive preset system |
| core | [#128](https://github.com/strata-game-library/core/issues/128) | ✅ RESOLVED: ESM not working |

### agentic-dev-library
| Repo | PR | Description |
|------|-----|-------------|
| control | [#41](https://github.com/agentic-dev-library/control/pull/41) | AI agent personas |
| triage | [#75](https://github.com/agentic-dev-library/triage/pull/75) | Sage handler |

### extended-data-library
| Repo | PR | Description |
|------|-----|-------------|
| core | [#18](https://github.com/extended-data-library/core/pull/18) | 1.0 stabilization |

### arcade-cabinet
| Repo | PR | Description |
|------|-----|-------------|
| otter-river-rush | [#63](https://github.com/arcade-cabinet/otter-river-rush/pull/63) | ✅ RESOLVED: SonarCloud failing |
| otter-elite-force | [#69-71](https://github.com/arcade-cabinet/otter-elite-force/pulls) | Bot PRs need review |
| rivermarsh | [#94](https://github.com/arcade-cabinet/rivermarsh/pull/94) | Store refactor |

---

## 🤖 Bot PR Backlog

### google-labs-jules[bot]
| Repo | PRs | Types |
|------|-----|-------|
| otter-elite-force | 5 | Optimization, Security, A11y |
| protocol-silent-night | 7 | Security, Performance, A11y |

### Copilot
| Repo | PRs | Types |
|------|-----|-------|
| cosmic-cults | 8 | Game systems (WIP) |

### dependabot[bot]
| Repo | PRs | Types |
|------|-----|-------|
| rivers-of-reckoning | 4 | CI, Dependencies |
| rivers-of-reckoning-legacy | 1 | CI |

---

## 📦 New Packages Pending

| Package | Org | Status | Next Step |
|---------|-----|--------|-----------|
| model-synth | strata-game-library | Code complete | CI/CD, npm publish |

---

## 🔄 Recommended Merge Order

### Phase 1: ESM Foundation
```
1. strata-game-library/presets#12
2. strata-game-library/core#129 (DONE)
3. agentic-dev-library/control#42
4. agentic-dev-library/triage#76
5. extended-data-library/core#22
```

### Phase 2: Feature PRs
```
6. strata-game-library/presets#14
7. agentic-dev-library/control#41
8. agentic-dev-library/triage#75
```

### Phase 3: Game PRs (after SonarCloud fix)
```
9. arcade-cabinet/otter-river-rush#63 (DONE)
10. arcade-cabinet/otter-elite-force#69-71
11. arcade-cabinet/rivermarsh#94
```

### Phase 4: Bot PRs (batch review)
```
12. All google-labs-jules PRs
13. All Copilot PRs
14. All dependabot PRs
```

---

## 📋 Agent Assignments

| Agent | Scope | Responsibility |
|-------|-------|----------------|
| @cursor | All repos | PR reviews, merges, AI feedback |
| @claude | Cross-org | Architecture, coordination |
| Cloud agents | Per-PR | Follow-ups, triage |

---

## 🔔 Notifications

All critical notifications have been resolved.

---

**This dashboard will be updated as work progresses.**
