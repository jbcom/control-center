"""Replay Cursor background agent sessions into the global memory bank.

This utility ingests a Cursor conversation export (the JSON stored in
`.cursor/recovery/<agent-id>/conversation.json`) and updates the global
`memory-bank` with:
- A full chronological transcript saved under `memory-bank/recovery/`
- A structured CHRONOLOGICAL_HISTORY.md with PRs, commits, issues extracted
- A succinct progress entry appended to `memory-bank/progress.md`
- A refreshed `memory-bank/activeContext.md` reflecting the replayed focus
- An optional delegation plan that can be piped into MCP-friendly CLIs

The global `memory-bank/` directory is the single source of truth for all agents.
Subdirectory memory-banks (e.g., `.cursor/memory-bank/`) have been eliminated.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_BANK_ROOT = REPO_ROOT / "memory-bank"

DEFAULT_TIMELINE_LIMIT = 50


class ConversationLoadError(RuntimeError):
    """Raised when a conversation export cannot be parsed."""


def _load_conversation(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ConversationLoadError(f"Conversation file not found: {path}")

    try:
        payload: dict[str, Any] = json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ConversationLoadError(f"Invalid JSON in {path}") from exc

    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ConversationLoadError("Conversation export missing 'messages' list")

    parsed: list[dict[str, str]] = []
    for raw in messages:
        msg_type = str(raw.get("type", "")).strip()
        text = str(raw.get("text", "")).strip()
        role = "user" if msg_type == "user_message" else "assistant"
        parsed.append({"role": role, "text": text})

    return parsed


def _extract_artifacts(messages: list[dict[str, str]]) -> dict[str, set[str]]:
    """Extract PRs, commits, issues, branches, repos from conversation."""
    artifacts: dict[str, set[str]] = {
        "prs": set(),
        "commits": set(),
        "issues": set(),
        "branches": set(),
        "repos": set(),
        "files": set(),
    }
    
    for msg in messages:
        text = msg["text"]
        
        # Extract PRs (PR #123, #123, pull/123)
        for match in re.findall(r'(?:PR\s*)?#(\d+)', text):
            if int(match) < 10000:  # Filter out run IDs
                artifacts["prs"].add(f"#{match}")
        
        # Extract commits (7+ char hex)
        for match in re.findall(r'\b([a-f0-9]{7,40})\b', text.lower()):
            artifacts["commits"].add(match[:7])
        
        # Extract branches
        for match in re.findall(r'((?:feat|fix|docs|refactor|chore|agent|copilot|cursor)/[a-z0-9_-]+)', text):
            artifacts["branches"].add(match)
        
        # Extract repos
        for match in re.findall(r'(?:github\.com/)?([a-zA-Z][a-zA-Z0-9_-]*/[a-zA-Z][a-zA-Z0-9_-]+)', text):
            if match.split('/')[0].lower() in ('jbcom', 'flipsidecrypto', 'fsc'):
                artifacts["repos"].add(match)
        
        # Extract files
        for match in re.findall(r'([a-zA-Z0-9_/.-]+\.(?:py|ts|tsx|js|md|yml|yaml|toml|json|sh))', text):
            if len(match) < 100:  # Filter out long paths
                artifacts["files"].add(match)
    
    return artifacts


def _extract_key_events(messages: list[dict[str, str]]) -> list[str]:
    """Extract key events (commits, merges, PRs created, etc)."""
    events: list[str] = []
    keywords = [
        "✅", "❌", "merged", "created pr", "pushed", "committed", 
        "fixed", "completed", "done", "success", "failed", "error"
    ]
    
    for i, msg in enumerate(messages):
        if msg["role"] != "assistant":
            continue
        text_lower = msg["text"].lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # Extract first 200 chars of relevant message
                snippet = msg["text"][:200].replace('\n', ' ')
                events.append(f"[{i+1}] {snippet}...")
                break
    
    return events[-30:]  # Last 30 events


def _generate_chronological_history(
    messages: list[dict[str, str]], 
    session_label: str,
    artifacts: dict[str, set[str]],
    events: list[str]
) -> str:
    """Generate a structured chronological history document."""
    
    return textwrap.dedent(f"""
# Chronological History: {session_label}

**Generated**: {datetime.now(UTC).isoformat()}
**Messages**: {len(messages)}
**User Messages**: {sum(1 for m in messages if m['role'] == 'user')}
**Assistant Messages**: {sum(1 for m in messages if m['role'] == 'assistant')}

---

## Extracted Artifacts

### PRs ({len(artifacts['prs'])})
{chr(10).join(f"- {pr}" for pr in sorted(artifacts['prs'])) or "- (none)"}

### Branches ({len(artifacts['branches'])})
{chr(10).join(f"- `{b}`" for b in sorted(artifacts['branches'])) or "- (none)"}

### Repositories ({len(artifacts['repos'])})
{chr(10).join(f"- {r}" for r in sorted(artifacts['repos'])) or "- (none)"}

### Commits ({len(artifacts['commits'])})
{chr(10).join(f"- `{c}`" for c in sorted(artifacts['commits'])[:20]) or "- (none)"}
{f"- ... and {len(artifacts['commits']) - 20} more" if len(artifacts['commits']) > 20 else ""}

### Files Mentioned ({len(artifacts['files'])})
{chr(10).join(f"- `{f}`" for f in sorted(artifacts['files'])[:30]) or "- (none)"}
{f"- ... and {len(artifacts['files']) - 30} more" if len(artifacts['files']) > 30 else ""}

---

## Key Events Timeline

{chr(10).join(events) or "(No key events extracted)"}

---

## User Instructions (Chronological)

{chr(10).join(f"**[{i+1}]** {m['text'][:300]}{'...' if len(m['text']) > 300 else ''}" 
              for i, m in enumerate(messages) if m['role'] == 'user')[:20] or "(No user messages)"}

---

*Auto-generated by replay_agent_session.py*
    """).strip() + "\n"


def _normalize_session_label(path: Path, explicit_label: str | None) -> str:
    if explicit_label:
        return explicit_label

    return path.parent.name or path.stem


def _format_timeline(messages: list[dict[str, str]], limit: int | None) -> str:
    render_messages: Iterable[tuple[int, dict[str, str]]]
    if limit:
        render_messages = enumerate(messages[-limit:], start=max(len(messages) - limit + 1, 1))
    else:
        render_messages = enumerate(messages, start=1)

    lines: list[str] = []
    for idx, message in render_messages:
        role = "User" if message["role"] == "user" else "Assistant"
        snippet = textwrap.shorten(message["text"].replace("\n", " "), width=280, placeholder="…")
        lines.append(f"{idx}. [{role}] {snippet}")

    return "\n".join(lines)


def _find_best_summary(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message["role"] != "assistant":
            continue
        if "summary" in message["text"].lower():
            return message["text"].strip()

    for message in reversed(messages):
        if message["role"] == "assistant" and message["text"].strip():
            return message["text"].strip()

    return "No assistant summary available from the replayed session."


def _write_recovery_timeline(timeline: str, session_label: str) -> Path:
    recovery_dir = MEMORY_BANK_ROOT / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    output_path = recovery_dir / f"{session_label}-replay.md"
    header = f"# Replayed Session: {session_label}\n\nGenerated on {datetime.now(UTC).isoformat()}\n\n"
    output_path.write_text(header + timeline + "\n")
    return output_path


def _append_progress_entry(summary: str, timeline_path: Path, tasks: list[str], session_label: str) -> None:
    progress_path = MEMORY_BANK_ROOT / "progress.md"
    progress_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%b %d, %Y %H:%M UTC")
    task_lines = "\n".join(f"- {line}" for line in tasks) if tasks else "- No explicit task files discovered."

    entry = (
        f"\n\n## Session Replay: {session_label} ({timestamp})\n\n"
        f"### Summary\n{summary}\n\n"
        f"### Transcript\n- Stored at `{timeline_path.relative_to(REPO_ROOT)}`\n\n"
        f"### Delegation Inputs\n{task_lines}\n"
    )

    # Handle case where progress.md doesn't exist yet
    if progress_path.is_file():
        existing_content = progress_path.read_text().rstrip()
        progress_path.write_text(existing_content + entry + "\n")
    else:
        progress_path.write_text("# Progress Log\n" + entry + "\n")


def _refresh_active_context(summary: str, tasks: list[str], session_label: str) -> None:
    active_path = MEMORY_BANK_ROOT / "activeContext.md"
    tasks_block = "\n".join(f"- {task}" for task in tasks) if tasks else "- Review delegation inputs generated from replayed session tasks."

    content = textwrap.dedent(
        f"""
# Active Context

## Current Focus
- Merge Cursor and repository memory banks into the root-level `memory-bank/` without symlinks.
- Automate replay of background agent sessions into the shared memory bank and delegation prompts.

## Active Work

### Session Replay Automation
- Replayed session `{session_label}` into the recovery archive and appended its summary to the progress log.
- Captured delegation inputs for MCP-aware CLIs to spawn focused sub-agents.

## Next Actions
- Run `python scripts/replay_agent_session.py --conversation <path/to/conversation.json>` for each new recovery export.
- Pipe `memory-bank/recovery/{session_label}-delegation.md` into MCP-aware CLIs (Codex, Claude code aider) to launch sub-agents.
- All agents read from and write to the global `memory-bank/` directory (no subdirectory copies).

## Session Highlight
{summary}

## Delegation Inputs
{tasks_block}
        """
    ).strip() + "\n"

    active_path.write_text(content)


def _collect_task_summaries(tasks_dir: Path | None) -> list[str]:
    if not tasks_dir or not tasks_dir.is_dir():
        return []

    summaries: list[str] = []
    for task_file in sorted(tasks_dir.glob("*.md")):
        lines = task_file.read_text().splitlines()
        # Handle empty files gracefully
        first_line = lines[0].strip() if lines else "[Empty task file]"
        summaries.append(f"{task_file.name}: {first_line}")
    return summaries


def _write_delegation_plan(session_label: str, tasks: list[str], ai_command: str | None) -> Path:
    recovery_dir = MEMORY_BANK_ROOT / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    plan_path = recovery_dir / f"{session_label}-delegation.md"

    ai_hint = ai_command or "codex --mcp"  # sensible default hint for CLI-based MCP clients
    tasks_block = "\n".join(f"- {task}" for task in tasks) if tasks else "- No task stubs provided; derive actions from the transcript."

    content = textwrap.dedent(
        f"""
# Delegation Plan for {session_label}

These prompts are tailored for MCP-aware CLIs (e.g., Codex, Claude code aider) that can run against this repository.

## Suggested Invocation
```bash
{ai_hint} --prompt-file {plan_path.name}
```

Ensure your MCP proxy is running via `process-compose up -d` so filesystem and GitHub services are available.

## Delegation Inputs
{tasks_block}
        """
    ).strip() + "\n"

    plan_path.write_text(content)
    return plan_path


# _mirror_to_cursor_memory_bank() removed - all memory now lives in global memory-bank/


def _maybe_run_ai_summary(ai_command: str | None, timeline_path: Path) -> str | None:
    if not ai_command:
        return None

    prompt = textwrap.dedent(
        f"""
        Summarize the replayed Cursor background agent session stored in {timeline_path}.
        Provide 3-5 bullet points plus next actions suitable for populating a memory bank.
        """
    ).strip()

    try:
        result = subprocess.run(
            ai_command.split(),
            input=prompt.encode(),
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover - execution dependent
        return None

    return result.stdout.decode().strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--conversation",
        required=True,
        type=Path,
        help="Path to the Cursor conversation JSON export.",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        help="Directory containing task markdown files recovered from the agent session.",
    )
    parser.add_argument(
        "--session-label",
        help="Override the default session label (defaults to the conversation directory name).",
    )
    parser.add_argument(
        "--timeline-limit",
        type=int,
        default=DEFAULT_TIMELINE_LIMIT,
        help="Number of messages to include in the condensed timeline (full transcript is always archived).",
    )
    parser.add_argument(
        "--ai-command",
        help="Optional CLI to generate an AI-authored summary (e.g., 'codex summarize --stdin').",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for recovery artifacts (defaults to conversation parent dir).",
    )

    args = parser.parse_args()

    messages = _load_conversation(args.conversation)
    session_label = _normalize_session_label(args.conversation, args.session_label)
    
    # Extract artifacts automatically
    print(f"📊 Processing {len(messages)} messages...")
    artifacts = _extract_artifacts(messages)
    events = _extract_key_events(messages)
    
    print(f"   PRs: {len(artifacts['prs'])}")
    print(f"   Branches: {len(artifacts['branches'])}")
    print(f"   Repos: {len(artifacts['repos'])}")
    print(f"   Commits: {len(artifacts['commits'])}")
    print(f"   Files: {len(artifacts['files'])}")
    print(f"   Key Events: {len(events)}")
    
    # Generate and write chronological history
    history_content = _generate_chronological_history(messages, session_label, artifacts, events)
    recovery_dir = MEMORY_BANK_ROOT / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    history_path = recovery_dir / f"{session_label}-chronological-history.md"
    history_path.write_text(history_content)
    print(f"✅ Chronological history: {history_path}")
    
    # Also write to original recovery location if different
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "CHRONOLOGICAL_HISTORY.md").write_text(history_content)
    elif args.conversation.parent != recovery_dir:
        (args.conversation.parent / "CHRONOLOGICAL_HISTORY.md").write_text(history_content)
    
    # Generate timeline
    condensed_timeline = _format_timeline(messages, limit=args.timeline_limit)
    timeline_path = _write_recovery_timeline(condensed_timeline, session_label=session_label)

    ai_summary = _maybe_run_ai_summary(args.ai_command, timeline_path)
    summary = ai_summary or _find_best_summary(messages)

    tasks = _collect_task_summaries(args.tasks_dir)
    delegation_plan = _write_delegation_plan(session_label, tasks, args.ai_command)

    _append_progress_entry(summary, timeline_path, tasks, session_label)
    _refresh_active_context(summary, tasks, session_label)

    print("")
    print("=== Replay complete ===")
    print(f"Session label:    {session_label}")
    print(f"History:          {history_path}")
    print(f"Transcript:       {timeline_path}")
    print(f"Delegation:       {delegation_plan}")
    print(f"Progress log:     {MEMORY_BANK_ROOT / 'progress.md'}")
    print(f"Active ctx:       {MEMORY_BANK_ROOT / 'activeContext.md'}")
    print("")
    print("Artifacts extracted:")
    print(f"  PRs:      {', '.join(sorted(artifacts['prs'])[:10]) or '(none)'}")
    print(f"  Branches: {', '.join(sorted(artifacts['branches'])[:5]) or '(none)'}")
    print(f"  Repos:    {', '.join(sorted(artifacts['repos'])[:5]) or '(none)'}")


if __name__ == "__main__":
    main()
