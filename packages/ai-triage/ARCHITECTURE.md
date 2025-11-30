# ai-triage Package Architecture

## Problem Statement

### The Gap in Current Agent Workflows

Autonomous agents (Cursor, Copilot, etc.) can **start** work but struggle to **finish** it. They:

1. **Create PRs** but don't iterate on CI failures
2. **Receive feedback** but don't systematically address it
3. **Complete tasks** but don't close related issues
4. **Get blocked** and wait for human intervention instead of self-resolving

### Real-World Example

Agent `bc-57463b64` worked for hours on terraform migrations. When its session ended:
- PR #263 was ready but not merged
- PR #264 was ready but not merged  
- Issues #256, #257, #258 were still open
- 21 stale branches were left behind

A human (or another agent) had to:
1. Read the full conversation transcript
2. Identify what was done vs pending
3. Manually merge each PR
4. Watch CI after each merge
5. Close issues with appropriate comments
6. Clean up branches

**This is the problem**: Work completion requires human orchestration.

### The Goal

```bash
ai-triage resolve issue 267
# Walk away. Come back to:
# - Issue closed
# - PR merged
# - CI green
# - All feedback addressed
# - Zero human intervention required
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ai-triage                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Triage     │  │   Resolver   │  │   Monitor    │          │
│  │   Engine     │  │   Engine     │  │   Engine     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────────┬────┴────────────────┘                   │
│                      │                                          │
│              ┌───────▼───────┐                                  │
│              │  Workflow     │                                  │
│              │  Orchestrator │                                  │
│              └───────┬───────┘                                  │
│                      │                                          │
│         ┌────────────┼────────────┐                            │
│         │            │            │                            │
│  ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐                      │
│  │ Computer    │ │ Code   │ │ GitHub   │                      │
│  │ Use Agent   │ │ Agent  │ │ Agent    │                      │
│  └─────────────┘ └────────┘ └──────────┘                      │
│         │            │            │                            │
│         └────────────┼────────────┘                            │
│                      │                                          │
│              ┌───────▼───────┐                                  │
│              │  Vercel AI    │                                  │
│              │  SDK          │                                  │
│              └───────────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Triage Engine

**Purpose**: Analyze work items and determine their state and next actions.

**Inputs**:
- GitHub Issues
- Pull Requests  
- Agent session transcripts
- CI run logs

**Outputs**:
```typescript
interface TriageResult {
  status: "needs_work" | "ready_to_merge" | "blocked" | "needs_review";
  
  blockers: Array<{
    type: "ci_failure" | "review_feedback" | "merge_conflict" | "missing_test";
    description: string;
    autoResolvable: boolean;
    suggestedFix?: string;
  }>;
  
  completedWork: Array<{
    description: string;
    evidence: string; // PR link, commit SHA, etc.
  }>;
  
  nextActions: Array<{
    action: string;
    priority: "critical" | "high" | "medium" | "low";
    automated: boolean;
    estimatedEffort: string;
  }>;
}
```

**Why it matters**: Before you can fix something, you need to understand its current state. The triage engine provides a structured assessment that downstream components can act on.

### 2. Resolver Engine

**Purpose**: Execute resolution strategies for identified blockers.

**Capabilities**:
- Generate code fixes for CI failures
- Address AI reviewer feedback (fix or justify)
- Resolve merge conflicts
- Add missing tests
- Update documentation

**Decision Flow**:
```
Blocker Identified
       │
       ▼
┌──────────────┐
│ Can we auto- │──── No ───▶ Flag for human review
│ resolve it?  │
└──────┬───────┘
       │ Yes
       ▼
┌──────────────┐
│ Generate fix │
│ using AI     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Validate fix │──── Fail ───▶ Try alternative approach
│ locally      │                (max 3 attempts)
└──────┬───────┘
       │ Pass
       ▼
┌──────────────┐
│ Commit, push │
│ re-verify    │
└──────────────┘
```

**Why it matters**: Identification without action is useless. The resolver turns insights into fixes.

### 3. Monitor Engine

**Purpose**: Watch asynchronous processes and react to state changes.

**Monitors**:
- CI pipeline status (GitHub Actions)
- AI reviewer responses (Gemini, Q, Copilot)
- PR merge status
- Issue state changes

**Behavior**:
```
Monitor Loop
     │
     ▼
┌─────────────┐
│ Poll state  │◀─────────────────┐
└──────┬──────┘                  │
       │                         │
       ▼                         │
┌─────────────┐                  │
│ State       │                  │
│ changed?    │─── No ──────────▶│ (wait interval)
└──────┬──────┘                  │
       │ Yes                     │
       ▼                         │
┌─────────────┐                  │
│ Trigger     │                  │
│ handler     │──────────────────┘
└─────────────┘
```

**Why it matters**: CI runs take minutes. Reviews take time. The monitor enables async workflows without blocking.

### 4. Workflow Orchestrator

**Purpose**: Compose engines into end-to-end workflows.

**Example Workflow: Issue-to-Merge**
```
issue-to-merge(issueNumber)
     │
     ▼
┌─────────────────┐
│ 1. Triage issue │ ← Understand requirements
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Create branch│ ← Set up workspace
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Generate code│ ← Code Agent writes implementation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Run tests    │ ← Validate locally
│    locally      │
└────────┬────────┘
         │ (loop until pass)
         ▼
┌─────────────────┐
│ 5. Create PR    │ ← Push and open PR
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Request      │ ← /gemini review, /q review
│    AI reviews   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Address      │ ← Resolver handles feedback
│    feedback     │
└────────┬────────┘
         │ (loop until all addressed)
         ▼
┌─────────────────┐
│ 8. Wait for CI  │ ← Monitor watches pipeline
└────────┬────────┘
         │ (loop: fix failures, re-run)
         ▼
┌─────────────────┐
│ 9. Ready state  │ ← All checks pass, feedback addressed
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 10. Merge or    │ ← Depending on permissions
│     await human │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 11. Close issue │ ← With summary comment
└─────────────────┘
```

**Why it matters**: Individual engines are tools. Workflows are the automation.

---

## AI Agent Integration

### Why Vercel AI SDK?

The `@ai-sdk/anthropic` package provides three critical capabilities:

#### 1. Computer Use
```typescript
// Can interact with visual interfaces
const computerTool = anthropic.tools.computer_20250124({
  displayWidthPx: 1920,
  displayHeightPx: 1080,
  async execute({ action, coordinate, text }) {
    // Screenshot, click, type, scroll
  }
});
```

**Use cases**:
- Navigate GitHub UI to find CI failure details
- View test output screenshots
- Interact with review interfaces

#### 2. Bash Tool
```typescript
// Can execute shell commands
const bashTool = anthropic.tools.bash_20250124({
  async execute({ command }) {
    return await exec(command);
  }
});
```

**Use cases**:
- Run tests locally before pushing
- Execute git commands
- Run linters and formatters

#### 3. Text Editor Tool
```typescript
// Can read, write, edit files
const editorTool = anthropic.tools.textEditor_20250124({
  async execute({ command, path, content }) {
    // view, create, str_replace, insert
  }
});
```

**Use cases**:
- Read source files to understand context
- Write new code
- Make targeted edits to fix issues

### Agent Composition

```typescript
class CodeAgent {
  private model = anthropic("claude-sonnet-4-20250514");
  
  async generateFix(failure: CIFailure): Promise<Fix> {
    const result = await generateText({
      model: this.model,
      tools: {
        bash: bashTool,
        editor: editorTool,
      },
      maxSteps: 10, // Allow multi-step reasoning
      prompt: `
        Fix this CI failure:
        ${failure.description}
        
        Error output:
        ${failure.logs}
        
        Use the tools to:
        1. Read relevant files
        2. Understand the issue
        3. Make the fix
        4. Verify it works
      `,
    });
    
    return parseFixFromResult(result);
  }
}
```

---

## Integration with Existing Packages

### cursor-fleet → ai-triage

```typescript
// cursor-fleet/src/fleet.ts
import { Triage, Resolver, Workflows } from "@jbcom/ai-triage";

class Fleet {
  private triage = new Triage();
  private resolver = new Resolver();
  
  async analyzeAgent(agentId: string): Promise<TriageResult> {
    const conversation = await this.getConversation(agentId);
    return this.triage.analyzeSession(conversation);
  }
  
  async completeAgentWork(agentId: string): Promise<void> {
    const triage = await this.analyzeAgent(agentId);
    
    for (const blocker of triage.blockers) {
      if (blocker.autoResolvable) {
        await this.resolver.resolve(blocker);
      }
    }
  }
}
```

### Standalone CLI

```bash
# Analyze only
ai-triage analyze issue 267 --output json

# Full resolution
ai-triage resolve issue 267 --auto-merge=false

# Specific workflow
ai-triage workflow ci-green --pr 266 --max-attempts 5
```

---

## Configuration

```yaml
# .ai-triage.yml
github:
  token_env: GITHUB_JBCOM_TOKEN
  
ai:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_steps: 20
  
workflows:
  issue-to-merge:
    auto_merge: false  # Require human approval
    max_ci_retries: 5
    reviewers:
      - /gemini review
      - /q review
    
  ci-green:
    max_attempts: 10
    backoff_seconds: 30
    
monitors:
  poll_interval_seconds: 30
  timeout_minutes: 60
```

---

## Success Metrics

The package succeeds if it can:

1. **Reduce human intervention** - Measure PRs merged without manual steps
2. **Improve completion rate** - Measure issues closed vs opened
3. **Decrease time-to-merge** - Measure PR open duration
4. **Handle failures gracefully** - Measure recovery rate from CI failures

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Package structure and build setup
- [ ] Triage engine with structured output
- [ ] GitHub API integration (issues, PRs, CI)

### Phase 2: AI Integration
- [ ] Vercel AI SDK setup
- [ ] Code Agent with bash + editor tools
- [ ] Computer Use for visual debugging

### Phase 3: Workflows
- [ ] CI-green workflow
- [ ] Review-complete workflow
- [ ] Issue-to-merge workflow

### Phase 4: Integration
- [ ] cursor-fleet imports ai-triage
- [ ] CLI interface
- [ ] Configuration system

---

## Open Questions

1. **Scope boundaries**: When should ai-triage give up and escalate to human?
2. **Cost management**: How to limit API calls for expensive operations?
3. **Safety rails**: How to prevent destructive actions (force push, delete branches)?
4. **Audit trail**: How to log all actions for debugging/compliance?

---

## Related

- Issue #269: Original proposal
- cursor-fleet package: Will be primary consumer
- PR #266: QA protocol this would automate

---

*Last Updated: 2024-11-30*
*Status: Architecture Document - Not Yet Implemented*
