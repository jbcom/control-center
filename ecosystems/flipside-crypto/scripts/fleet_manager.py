#!/usr/bin/env python3
"""
Fleet Manager - Cursor Background Agent Orchestration

Provides a unified interface for managing Cursor background agents, with
automatic fallback from MCP proxy to direct MCP protocol calls.

Usage:
    fleet_manager.py list [--running] [--json]
    fleet_manager.py spawn <repo> <task> [--ref REF] [--json]
    fleet_manager.py status <agent_id> [--json]
    fleet_manager.py followup <agent_id> <message>
    fleet_manager.py conversation <agent_id> [--json]
    fleet_manager.py archive <agent_id> [--output PATH]
    fleet_manager.py repos [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Configuration
MCP_PROXY_URL = os.environ.get("MCP_PROXY_CURSOR_AGENTS_URL", "http://localhost:3011")
CURSOR_API_KEY = os.environ.get("CURSOR_API_KEY", "")
MEMORY_BANK_ROOT = Path(__file__).resolve().parent.parent / "memory-bank"


@dataclass
class MCPResponse:
    """Response from MCP call."""
    success: bool
    data: Any
    error: str | None = None


def check_proxy_available() -> bool:
    """Check if MCP proxy is responding."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{MCP_PROXY_URL}/mcp", method="GET")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def call_mcp_via_proxy(tool: str, arguments: dict) -> MCPResponse:
    """Call MCP tool via HTTP proxy."""
    import urllib.request
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments}
    }
    
    try:
        req = urllib.request.Request(
            f"{MCP_PROXY_URL}/mcp",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            
        if "error" in result:
            return MCPResponse(False, None, result["error"].get("message", str(result["error"])))
        
        content = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        return MCPResponse(True, json.loads(content))
        
    except Exception as e:
        return MCPResponse(False, None, str(e))


def call_mcp_direct(tool: str, arguments: dict) -> MCPResponse:
    """Call MCP tool directly via stdin/stdout to cursor-background-agent-mcp-server."""
    
    # Build the MCP protocol messages
    init_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fleet-manager", "version": "1.0"}
        }
    })
    
    call_msg = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments}
    })
    
    # Combine with delays (using shell for timing)
    script = f"""
(echo '{init_msg}'; sleep 2; echo '{call_msg}'; sleep 8) | timeout 30 npx -y cursor-background-agent-mcp-server 2>/dev/null
"""
    
    try:
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=45,
            env={**os.environ, "PATH": f"/home/ubuntu/.local/bin:{os.environ.get('PATH', '')}"}
        )
        
        # Parse the output - look for the response to our call (id: 1)
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
                if msg.get("id") == 1:
                    if "error" in msg:
                        return MCPResponse(False, None, msg["error"].get("message", str(msg["error"])))
                    content = msg.get("result", {}).get("content", [{}])[0].get("text", "{}")
                    return MCPResponse(True, json.loads(content))
            except json.JSONDecodeError:
                continue
        
        return MCPResponse(False, None, f"No valid response found. stdout: {result.stdout[:500]}")
        
    except subprocess.TimeoutExpired:
        return MCPResponse(False, None, "MCP call timed out")
    except Exception as e:
        return MCPResponse(False, None, str(e))


def call_mcp(tool: str, arguments: dict) -> MCPResponse:
    """Call MCP tool, trying proxy first, then falling back to direct."""
    if check_proxy_available():
        return call_mcp_via_proxy(tool, arguments)
    return call_mcp_direct(tool, arguments)


def cmd_list(args):
    """List agents."""
    resp = call_mcp("listAgents", {})
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    agents = resp.data.get("agents", [])
    
    if args.running:
        agents = [a for a in agents if a.get("status") == "RUNNING"]
    
    if args.json:
        print(json.dumps(agents, indent=2))
    else:
        print("=== Fleet Status ===\n")
        print(f"{'STATUS':<10} {'ID':<40} {'REPO':<30} {'NAME'}")
        print("-" * 120)
        for agent in agents:
            status = agent.get("status", "?")
            agent_id = agent.get("id", "?")
            repo = agent.get("source", {}).get("repository", "?").split("/")[-1]
            name = agent.get("name", "?")[:50]
            print(f"{status:<10} {agent_id:<40} {repo:<30} {name}")


def cmd_spawn(args):
    """Spawn a new agent."""
    # Get my own agent ID for context
    my_id = os.environ.get("CURSOR_AGENT_ID", "unknown")
    list_resp = call_mcp("listAgents", {})
    if list_resp.success:
        running = [a for a in list_resp.data.get("agents", []) if a.get("status") == "RUNNING"]
        if running:
            my_id = running[0].get("id", my_id)
    
    task_with_context = f"""{args.task}

COORDINATION:
- Control Manager Agent: {my_id}
- Control Center: FSC Control Center
- Report progress via PR and addFollowup
"""
    
    arguments = {
        "prompt": {"text": task_with_context},
        "source": {"repository": args.repo, "ref": args.ref}
    }
    
    resp = call_mcp("launchAgent", arguments)
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(resp.data, indent=2))
    else:
        print("=== Agent Spawned ===")
        print(f"ID: {resp.data.get('id')}")
        print(f"Status: {resp.data.get('status')}")
        print(f"Branch: {resp.data.get('target', {}).get('branchName')}")
        print(f"URL: {resp.data.get('target', {}).get('url')}")


def cmd_status(args):
    """Get agent status."""
    resp = call_mcp("getAgentStatus", {"agentId": args.agent_id})
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(resp.data, indent=2))
    else:
        print(f"=== Agent: {args.agent_id} ===")
        print(json.dumps(resp.data, indent=2))


def cmd_followup(args):
    """Send followup to agent."""
    arguments = {
        "agentId": args.agent_id,
        "prompt": {"text": args.message}
    }
    
    resp = call_mcp("addFollowup", arguments)
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Followup sent to {args.agent_id}")


def cmd_conversation(args):
    """Get agent conversation."""
    resp = call_mcp("getAgentConversation", {"agentId": args.agent_id})
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    if args.json:
        print(json.dumps(resp.data, indent=2))
    else:
        messages = resp.data.get("messages", [])
        print(f"=== Conversation: {args.agent_id} ({len(messages)} messages) ===\n")
        for i, msg in enumerate(messages[-20:], 1):  # Last 20 messages
            role = "USER" if msg.get("type") == "user_message" else "ASSISTANT"
            text = msg.get("text", "")[:300]
            print(f"[{i}] {role}: {text}...")
            print()


def cmd_archive(args):
    """Archive agent conversation."""
    resp = call_mcp("getAgentConversation", {"agentId": args.agent_id})
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    output_path = args.output
    if not output_path:
        recovery_dir = MEMORY_BANK_ROOT / "recovery"
        recovery_dir.mkdir(parents=True, exist_ok=True)
        output_path = recovery_dir / f"conversation-{args.agent_id}.json"
    else:
        output_path = Path(output_path)
    
    output_path.write_text(json.dumps(resp.data, indent=2))
    print(f"✅ Archived to {output_path} ({output_path.stat().st_size} bytes)")


def cmd_repos(args):
    """List available repositories."""
    resp = call_mcp("listRepositories", {})
    if not resp.success:
        print(f"❌ Error: {resp.error}", file=sys.stderr)
        sys.exit(1)
    
    repos = resp.data.get("repositories", [])
    
    if args.json:
        print(json.dumps(repos, indent=2))
    else:
        print("=== Available Repositories ===\n")
        for repo in repos[:50]:
            print(f"  {repo.get('owner')}/{repo.get('name')}")
        if len(repos) > 50:
            print(f"\n  ... and {len(repos) - 50} more")


def main():
    parser = argparse.ArgumentParser(description="Fleet Manager - Cursor Agent Orchestration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # list
    list_parser = subparsers.add_parser("list", help="List agents")
    list_parser.add_argument("--running", action="store_true", help="Show only running agents")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # spawn
    spawn_parser = subparsers.add_parser("spawn", help="Spawn new agent")
    spawn_parser.add_argument("repo", help="Repository URL (https://github.com/org/repo)")
    spawn_parser.add_argument("task", help="Task description")
    spawn_parser.add_argument("--ref", default="main", help="Git ref (default: main)")
    spawn_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # status
    status_parser = subparsers.add_parser("status", help="Get agent status")
    status_parser.add_argument("agent_id", help="Agent ID")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # followup
    followup_parser = subparsers.add_parser("followup", help="Send followup to agent")
    followup_parser.add_argument("agent_id", help="Agent ID")
    followup_parser.add_argument("message", help="Message to send")
    
    # conversation
    conv_parser = subparsers.add_parser("conversation", help="Get agent conversation")
    conv_parser.add_argument("agent_id", help="Agent ID")
    conv_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # archive
    archive_parser = subparsers.add_parser("archive", help="Archive agent conversation")
    archive_parser.add_argument("agent_id", help="Agent ID")
    archive_parser.add_argument("--output", "-o", help="Output path")
    
    # repos
    repos_parser = subparsers.add_parser("repos", help="List available repositories")
    repos_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Check for API key
    if not CURSOR_API_KEY:
        print("❌ Error: CURSOR_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    # Dispatch to command
    commands = {
        "list": cmd_list,
        "spawn": cmd_spawn,
        "status": cmd_status,
        "followup": cmd_followup,
        "conversation": cmd_conversation,
        "archive": cmd_archive,
        "repos": cmd_repos,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
