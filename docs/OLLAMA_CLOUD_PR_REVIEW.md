# Ollama Cloud PR Review Workflow

This document explains the comprehensive AI-powered PR review workflow using Ollama Cloud models, specifically designed to fix the AI PR review workflow sync issues and provide a robust alternative to existing solutions.

## Overview

The workflow provides a complete AI code review solution using GLM-4.6:cloud model with the following capabilities:

- **Structured JSON output** with validation
- **Multi-turn conversation support** for follow-up reviews
- **Auto-fix capabilities** with git-auto-commit integration
- **Complementary AI review requests** (Gemini, Amazon Q)
- **Error handling and fallback mechanisms**

## Prerequisites

### Required Secrets
Add these secrets to your repository settings:

- `OLLAMA_API_KEY` - Your Ollama.com API key for cloud model access

### Required Variables (Optional)
Set these repository variables for customization:

- `OLLAMA_HOST` - Ollama API endpoint (defaults to `https://ollama.com`)
- `OLLAMA_MODEL` - Model to use (defaults to `glm-4.6:cloud`)

## Workflow Triggers

The workflow is triggered by:

1. **PR Open/Synchronize** - Initial review when PR is opened or updated
2. **Issue Comments** - Follow-up reviews when users comment with `/ollama-review`
3. **PR Review Comments** - Follow-up reviews on review comments

## Features

### 1. Initial PR Review (`pr-review` job)

**Triggers**: `pull_request` events (opened, synchronize)

**Process**:
1. Installs Ollama CLI and configures for cloud access
2. Pulls the `glm-4.6:cloud` model
3. Retrieves the PR diff
4. Sends structured prompt to GLM-4.6 with JSON schema
5. Validates the JSON response
6. Optionally applies suggested fixes automatically
7. Posts comprehensive review comment

**Output**: Structured JSON with:
- Summary of changes
- Issues found (file, line, severity, description, suggestion)
- Suggested fixes (unified diff patches)
- Overall score (1-10)
- Auto-apply flag

### 2. Multi-turn Follow-up Review (`follow-up-review` job)

**Triggers**: Comments containing `/ollama-review`

**Process**:
1. Retrieves previous AI comments for context
2. Builds conversation history with initial diff + previous responses + user comment
3. Sends multi-turn request to GLM-4.6
4. Handles follow-up questions, clarifications, or additional analysis

**Use Cases**:
- "Can you explain issue #3 in more detail?"
- "What about security implications?"
- "Can you suggest alternative approaches?"

### 3. AI Review Coordination (`request-ai-reviews` job)

**Triggers**: PR opened events

**Process**:
1. Automatically requests reviews from other AI tools
2. Posts comments with `/gemini review` and `/q review`
3. Enables complementary review from multiple AI sources

## JSON Schema

The workflow uses a strict JSON schema for structured output:

```json
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": { "type": "string" },
          "line": { "type": "integer", "minimum": 1 },
          "severity": { "type": "string", "enum": ["low", "medium", "high"] },
          "description": { "type": "string" },
          "suggestion": { "type": "string" }
        },
        "required": ["file", "severity", "description"],
        "additionalProperties": false
      }
    },
    "suggested_fixes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": { "type": "string" },
          "patch": { "type": "string", "description": "Unified diff patch compatible with 'git apply'" },
          "description": { "type": "string" }
        },
        "required": ["file", "patch", "description"],
        "additionalProperties": false
      }
    },
    "overall_score": { "type": "integer", "minimum": 1, "maximum": 10 },
    "should_auto_apply": { "type": "boolean" }
  },
  "required": ["summary", "issues", "suggested_fixes", "overall_score", "should_auto_apply"],
  "additionalProperties": false
}
```

## Auto-Fix Capabilities

The workflow can automatically apply safe fixes:

1. **Safety Check**: Only applies fixes when `should_auto_apply` is true
2. **Patch Application**: Uses `git apply` to apply unified diff patches
3. **Error Handling**: Continues if individual patches fail
4. **Auto-Commit**: Uses `stefanzweifel/git-auto-commit-action` to push fixes back to PR branch

## Model Optimizations

The workflow includes GLM-4.6 specific optimizations:

- **Temperature**: 0.1 (for deterministic, structured output)
- **Mirostat**: 2 with tau=5.0, eta=0.1 (for coherent responses)
- **Top_p**: 0.95 (nucleus sampling)
- **Context**: 196608 tokens (leverages GLM-4.6's 200K context window)
- **Predict**: 4096 tokens (for detailed responses)

## Error Handling

The workflow includes comprehensive error handling:

1. **Empty Response Check**: Validates model responses aren't empty
2. **JSON Validation**: Uses `jq` to validate JSON structure
3. **Patch Application**: Gracefully handles patch failures
4. **Git Operations**: Uses robust git commands with error checking

## Usage Examples

### Basic PR Review
When a PR is opened or synchronized, the workflow automatically:
1. Reviews the code changes
2. Identifies issues with severity levels
3. Suggests fixes as unified diff patches
4. Posts a structured review comment

### Follow-up Review
Users can request additional analysis by commenting:
```
/ollama-review Can you check for security vulnerabilities?
```

The workflow will:
1. Retrieve the conversation history
2. Analyze the new request in context
3. Provide additional insights or clarifications

### Multi-AI Review
The workflow automatically requests reviews from:
- Google Gemini Code Assist (`/gemini review`)
- Amazon Q Developer (`/q review`)

This provides complementary perspectives from different AI models.

## Troubleshooting

### Common Issues

1. **"Empty or invalid response from model"**
   - Check `OLLAMA_API_KEY` is valid
   - Verify model `glm-4.6:cloud` is available in your plan
   - Check Ollama.com API status

2. **JSON validation failures**
   - Usually temporary model issues
   - The workflow will retry on next trigger

3. **Patch application failures**
   - Patches may be outdated if code changes
   - Workflow continues and reports which patches failed

4. **Rate limiting**
   - Ollama Cloud has usage limits
   - Consider reducing review frequency for high-traffic repos

### Debugging

Enable debug logging by adding to your workflow:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
```

## Integration with Existing Workflows

This workflow is designed to complement existing AI review workflows:

- **Replaces Claude Code**: This workflow replaces the legacy `claude-code.yml`.
- **Replaces Agentic Triage**: This workflow replaces the legacy `agentic-triage.yml`.
- **Multi-AI**: Requests reviews from Gemini and Q for comprehensive coverage

## Security Considerations

1. **API Key Security**: Store `OLLAMA_API_KEY` as a repository secret
2. **Code Privacy**: Ollama Cloud states no prompt/response logging
3. **Auto-Fix Safety**: Only applies fixes when explicitly marked safe
4. **Branch Protection**: Ensure branch protection rules are configured appropriately

## Performance

- **Review Time**: Typically 30-60 seconds per PR
- **Context Usage**: Efficiently uses GLM-4.6's 200K context window
- **Cost**: Depends on Ollama Cloud usage plan

## Future Enhancements

Potential improvements:
1. **Custom Model Selection**: Allow per-repository model configuration
2. **Review Templates**: Customizable review templates per language
3. **Integration with CI/CD**: Block merges on critical issues
4. **Metrics Collection**: Track review quality and auto-fix success rates

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Ollama Cloud documentation
3. Examine workflow run logs for detailed error information
