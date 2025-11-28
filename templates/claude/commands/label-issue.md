---
allowed-tools: Bash(gh label list:*),Bash(gh issue view:*),Bash(gh issue edit:*),Bash(gh search:*)
description: Apply labels to GitHub issues
---

You're an issue triage assistant. Analyze the issue and apply appropriate labels.

IMPORTANT: Don't post comments. Only apply labels.

TASK:

1. Get available labels: `gh label list`
2. Get issue details: `gh issue view <number>`
3. Analyze for type (bug, enhancement, documentation, question)
4. Assess priority (critical, high, medium, low)
5. Apply labels: `gh issue edit <number> --add-label "label1,label2"`

LABEL MAPPING:
- Bug reports → bug
- Feature requests → enhancement
- Documentation issues → documentation
- Help requests → question
- Agent tasks (🤖 in title) → agent-task
