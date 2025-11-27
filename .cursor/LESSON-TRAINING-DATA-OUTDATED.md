# Lesson Learned: Training Data is Always Outdated

## The Problem

During PR #169, @amazon-q-developer made several claims about "latest versions" based on training data:
- Claimed Go 1.23.6 was latest (actual: 1.25.4)
- Claimed Rust 1.83.0 was latest (actual: 1.91.1)
- Did not verify against official sources before suggesting changes

@jbcom corrected: "ALL PR review HAS to be backed by confirmation using WEB research"

## The Fundamental Truth

**AI training data will ALWAYS be out of date for software releases.**

This is not a bug or limitation to work around - it is the inherent nature of static training data vs. continuously updating software:

- Languages release new versions every 6-8 weeks
- Tools update monthly or even weekly
- Security patches happen ad-hoc
- Your training was captured at a point in time

## The Solution

**ALWAYS do web research before making version claims.**

Even if you "know" something from training:
1. Verify it against official sources
2. Document your verification
3. Admit if you cannot verify
4. NEVER claim "as of [date]" based on training alone

## Example: This PR

**User was right, agent was wrong:**

Agent assumed: "Go 1.25 doesn't exist yet"
Reality: Go 1.25.4 exists and is current stable

Agent should have:
```bash
curl -sL https://go.dev/dl/ | grep -oP 'go1\.[0-9]+\.[0-9]+'
```

Result would show: go1.25.4 ✅

## Action Taken

1. ✅ Updated Dockerfile to Go 1.25.4 (verified)
2. ✅ Added `.cursor/rules/15-pr-review-verification.mdc`
3. ✅ Updated `.ruler/AGENTS.md` with verification requirements
4. ✅ Documented this lesson for future agents

## For Future Agents

If you're reading this because you suggested an outdated version:

1. **Acknowledge the mistake** - "You're right, my training data was outdated"
2. **Do the research NOW** - Actually check official sources
3. **Update your suggestions** - With verified current versions
4. **Document verification** - Show your work
5. **Learn from this** - Always verify, never assume

## Key Quotes

> "The thing is that your training data will ALWAYS be out of date on releases" - @jbcom

> "https://go.dev/dl/ and https://releases.rs/ would have given you COMPLETELY different information in a span of a minute without me having to intercede" - @jbcom

These are the official sources. Use them.

---

**Date**: 2025-11-27
**PR**: #169
**Lesson**: Training data ≠ Current reality
**Solution**: Web research is mandatory
