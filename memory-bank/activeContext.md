# Active Context

## Current Status: PR #16 In Review with Security Fixes

The cross-repository scope clarification effort is progressing:

### Completed Today
1. **Fixed Cursor Bugbot HIGH severity issues** in PR #16:
   - IPv6 SSRF bypass in webhook validation
   - Missing None checks causing ValidationError
   - Async/sync mismatch in execute_agent_task

2. **Created AI Sub-Package Architecture Issue** (#17):
   - LangChain/LangGraph integration plan
   - Exposes vendor connectors as AI-callable tools
   - Unified multi-provider AI interface

### PR Status
- **jbcom/vendor-connectors#16**: 6 commits, all security feedback addressed
- Awaiting AI reviewer re-verification (Cursor Bugbot, Amazon Q)

### Architecture Vision

```
vendor_connectors/
├── ai/                    # NEW: LangChain-based
│   ├── providers/         # Anthropic, OpenAI, Google, xAI, Ollama
│   └── tools/             # AWS, GitHub, Slack, Vault as AI tools
├── cursor/                # Keep - unique API
└── [existing connectors]
```

This enables:
- `agentic-control` becomes pure orchestration
- AI tools from vendor connectors for any LLM
- LangGraph workflows for complex tasks

## For Next Agent

1. **Wait for PR #16 reviews** to complete
2. **Once merged**, start AI sub-package implementation (Issue #17)
3. **Track progress** in Epic #340

Key files created:
- `vendor-connectors/src/vendor_connectors/cursor/__init__.py`
- `vendor-connectors/src/vendor_connectors/anthropic/__init__.py`
- Tests in `tests/test_cursor.py` and `tests/test_anthropic.py`
