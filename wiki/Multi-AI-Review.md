# Multi-AI PR Review Workflow

## Overview

This repository uses a comprehensive multi-AI review system to ensure code quality, security, and architectural consistency.

## AI Reviewers

### 1. Claude Code (Anthropic)
**Role**: Primary code reviewer and auto-healer
- **Model**: claude-haiku-4-5-20251001
- **Strengths**: 
  - Deep code understanding
  - Contextual refactoring
  - Auto-fix capabilities
- **Focus Areas**:
  - Code quality and best practices
  - Architecture consistency
  - Documentation completeness
  - Test coverage

### 2. Amazon Q Developer
**Role**: AWS and cloud infrastructure expert
- **Strengths**:
  - AWS best practices
  - Security patterns
  - Infrastructure as Code
- **Focus Areas**:
  - AWS resource configuration
  - IAM policies
  - Cloud architecture
  - Security compliance

### 3. DiffGuard AI
**Role**: Breaking change detection
- **Strengths**:
  - API compatibility analysis
  - Dependency impact assessment
  - Version compatibility
- **Focus Areas**:
  - Breaking changes
  - Dependency management
  - Backward compatibility

## Workflow Phases

### Phase 1: Initial Reviews (Parallel)
```
PR Opened
    ├─> Claude Code Review (primary)
    ├─> Amazon Q Review (AWS focus)
    └─> DiffGuard Review (breaking changes)
```

**Trigger**: New PR or PR update

**Actions**:
- Each AI performs independent review
- Posts comments with severity tags:
  - 🔴 Critical
  - 🟡 Warning
  - 🔵 Suggestion

### Phase 2: Synthesis
```
All Reviews Complete
    └─> Claude Synthesis
           ├─> Read all reviews
           ├─> Identify common themes
           ├─> Resolve conflicts
           └─> Post synthesis comment
```

**Trigger**: After all Phase 1 reviews complete

**Output**: Comprehensive action plan with:
- Executive Summary
- Critical Issues (must fix)
- Recommended Improvements
- Optional Enhancements
- Consensus vs Disagreements

### Phase 3: Auto-Healing
```
Synthesis Complete
    └─> Claude Auto-Heal
           ├─> Fix critical issues only
           ├─> Run tests
           ├─> Commit fixes
           └─> Comment on PR
```

**Trigger**: After synthesis

**Auto-fixes**:
- ✅ Linting errors
- ✅ Import errors
- ✅ Type errors
- ✅ Security vulnerabilities
- ❌ Architecture decisions
- ❌ Feature implementations

### Phase 4: Interactive Collaboration
```
Developer/AI Question
    ├─> @claude → Claude responds
    └─> /q → Amazon Q responds
```

**Trigger**: Comment mentions @claude or /q

**Capabilities**:
- Answer questions about code
- Implement requested changes
- Discuss trade-offs
- Provide examples

### Phase 5: CI Failure Auto-Fix
```
CI Fails
    └─> Claude Auto-Fix
           ├─> Analyze failure logs
           ├─> Fix issues
           ├─> Re-run CI
           └─> Report results
```

**Trigger**: CI workflow failure on PR

**Auto-fixes**:
- Test failures
- Linting failures
- Build errors
- Type check errors

## Using the Workflow

### For Developers

**Starting a PR**:
```bash
git checkout -b feature/my-feature
# Make changes
git commit -m "Add feature"
git push origin feature/my-feature
gh pr create
```

**Result**: All AI reviewers automatically engage

**Interacting with AIs**:
```markdown
@claude Can you refactor this function for better performance?

/q What's the AWS best practice for this IAM policy?
```

**Accepting auto-fixes**:
- Review the auto-heal commit
- If good: merge directly
- If needs work: comment with @claude for revisions

### For AI Agents

**Reading reviews**:
```bash
# Get all PR comments
gh pr view <number> --json comments --jq '.comments'

# Filter by reviewer
gh pr view <number> --json comments --jq '.comments[] | select(.author.login == "amazon-q-developer")'
```

**Collaborating**:
1. Read all existing reviews first
2. Don't duplicate feedback
3. Build on others' suggestions
4. Tag other AIs if needed: @claude or /q

**Making changes**:
```bash
# Checkout PR branch
gh pr checkout <number>

# Make changes
# ... edit files ...

# Commit and push
git commit -am "Fix: issue described in review"
git push
```

## Configuration

### Secrets Required

Add these to repository secrets:

```yaml
ANTHROPIC_API_KEY: # For Claude Code
GITHUB_JBCOM_TOKEN: # For gh CLI operations
OPENAI_API_KEY: # For DiffGuard (optional)
```

### Custom Rules

**Amazon Q Rules**: `.amazonq/rules/*.md`
- Custom coding standards
- Security requirements
- Project-specific patterns

**Claude System Prompts**: In workflow `claude_args`
- Model selection
- Tool permissions
- Behavioral guidelines

### Adjusting Behavior

**To change Claude's model**:
```yaml
claude_args: |
  --model claude-haiku-4-5-20251001  # Standard for all agentic tasks
```

**To restrict Claude's tools**:
```yaml
claude_args: |
  --allowedTools "Read,Grep,LS"  # Read-only
  # or
  --allowedTools "Read,Write,Bash(git:*)"  # Can edit and use git
```

**To disable auto-healing**:
Comment out the `auto-heal` job in the workflow.

## Monitoring

### View Workflow Runs
```bash
gh run list --workflow multi-ai-review.yml
gh run view <run-id>
```

### Check AI Activity
```bash
# Recent Claude comments
gh api repos/:owner/:repo/issues/comments --jq '.[] | select(.user.login == "claude-code") | {id, body[:100], created_at}'

# Recent Amazon Q comments
gh api repos/:owner/:repo/issues/comments --jq '.[] | select(.user.login == "amazon-q-developer") | {id, body[:100], created_at}'
```

## Troubleshooting

### Claude not responding
1. Check workflow run logs
2. Verify `ANTHROPIC_API_KEY` is set
3. Check if PR trigger conditions are met
4. Look for rate limit errors

### Amazon Q not responding
1. Ensure Amazon Q GitHub App is installed
2. Check `/q` command syntax
3. Verify permissions

### Auto-heal not working
1. Check if branch name starts with `claude-auto-heal-` (will skip to avoid loops)
2. Verify `GITHUB_JBCOM_TOKEN` has write permissions
3. Check git identity configuration

### Too many reviews
Adjust trigger conditions in workflow:
```yaml
if: |
  github.event_name == 'pull_request' &&
  !contains(github.event.pull_request.labels.*.name, 'skip-ai-review')
```

Then add `skip-ai-review` label to PRs you don't want reviewed.

## Best Practices

### For Humans
1. Let AIs do initial review before manual review
2. Read synthesis comment first
3. Use @claude for quick questions
4. Review auto-fixes before merging
5. Provide feedback on AI suggestions

### For AI Agents
1. Read all reviews before commenting
2. Don't duplicate feedback
3. Provide code examples
4. Explain reasoning
5. Tag severity levels
6. Link to documentation

## Future Enhancements

Planned improvements:
- [ ] Automatic issue labeling based on review content
- [ ] PR size analysis and split suggestions
- [ ] Dependency vulnerability scanning integration
- [ ] Performance regression detection
- [ ] Documentation coverage analysis
- [ ] Test coverage tracking and alerts

## Support

For issues with the workflow:
1. Check workflow logs
2. Review this documentation
3. Create issue with `workflow` label
4. Tag @claude for assistance
