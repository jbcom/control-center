# Messages 171-180

## [171] 🤖 ASSISTANT

🎯 Exactly! The wiki is literally syncing repo content TO the wiki - it's redundant complexity.

**GitHub Issues + Projects make way more sense:**

| Need | Wiki (current) | GitHub Issues/Projects (better) |
|------|----------------|--------------------------------|
| Active context | `wiki/Active-Context.md` synced | **Issue pinned + labeled** |
| Progress tracking | `wiki/Progress.md` synced | **Project board columns** |
| Session handoffs | Wiki page updates | **Issue comments with @mentions** |
| Blockers | Wiki edits | **Issues labeled `blocked`** |
| Agent coordination | PR comments | **Issues + cross-references** |

**Benefits of Issues/Projects:**
- ✅ Native notifications (@cursor, @jbcom)
- ✅ Timeline/history built-in
- ✅ Cross-repo linking works
- ✅ Labels, milestones, assignees
- ✅ API via `gh issue` / `gh project`
- ✅ No sync tooling needed
- ✅ Single source of truth

**Simplified architecture:**
```
IN-REPO (source of truth):
├── .ruler/           → Agent rules (ruler apply → .cursorrules, CLAUDE.md)
├── packages/         → Code
└── process-compose.yml

GITHUB (tracking):
├── Issues            → Active work, context, blockers
├── Projects          → Kanban board, cross-repo view
└── PRs               → Code changes + coordination comments

DELETE:
├── wiki/             → Redundant sync
├── memory-bank/      → Use Issues instead
└── .cursor/agents/   → Scattered nonsense
```

Want me to:
1. Create a GitHub Issue template for "Agent Session Context"
2. Set up a Project board for fleet coordination
3. Delete the wiki sync workflow?

---

## [172] 👤 USER

And probably clear the wiki while we're at it so we don't leave behind outdated crap?

---

## [173] 🤖 ASSISTANT

Yes! Let's clean house:

---

## [174] 👤 USER

Ruler will actually regenerate that file

---

## [175] 🤖 ASSISTANT

Right - I should just update `.ruler/` and let ruler regenerate everything. Let me clean up:

---

## [176] 🤖 ASSISTANT

Now let me update `.ruler/AGENTS.md` to remove wiki refs and use GitHub Issues:

---

## [177] 🤖 ASSISTANT

Now let me stage everything and commit:

---

## [178] 🤖 ASSISTANT

All changes are staged. Let me push and then clear the GitHub wiki:

---

## [179] 🤖 ASSISTANT

Now let me clear the GitHub wiki (it's a separate git repo):

---

## [180] 👤 USER

If you out all these changes in your HOLD OPEN PR then your last action can be to merge in and everything will be in NYCH better shape for the next agent. Also https://github.com/intellectronica/ruler.git you can clone to /tmp so that you can review docs

---

