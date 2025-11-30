# Messages 271-280

## [271] 🤖 ASSISTANT

You're right - the documentation is contradicting reality. The repo USES semantic-release (all packages have PSR configs), but the docs say it's forbidden. Let me fix this mess:

---

## [272] 🤖 ASSISTANT

The `.ruler/AGENTS.md` is **completely wrong** - it describes a workflow that doesn't exist. The repo ACTUALLY uses:
- Python Semantic Release (PSR) - every package has `[tool.semantic_release]` config
- Git tags per package (`directed-inputs-class-v202511.7.0`, etc.)
- Conventional commits with scopes (`feat(dic):`, `fix(bridge):`)

Let me fix this documentation to reflect reality:

---

## [273] 🤖 ASSISTANT

Now let me commit and push both the CI fix and documentation fix:

---

## [274] 🤖 ASSISTANT

CI changes are already there. Let me push:

---

## [275] 🤖 ASSISTANT

Main is protected - need a PR. Let me create one:

---

## [276] 🤖 ASSISTANT

PR #255 created. Let me enable auto-merge:

---

## [277] 🤖 ASSISTANT

CI is running. Let me wait and check:

---

## [278] 🤖 ASSISTANT

Tests are failing for python-terraform-bridge. Let me check the CI logs:

---

## [279] 🤖 ASSISTANT

The issue is tox doesn't have a `python-terraform-bridge` environment. Let me check and fix tox.ini:

---

## [280] 👤 USER

You have PR feedback

---

