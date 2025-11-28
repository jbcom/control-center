#!/bin/bash
# Fleet Manager - Control Center Agent Orchestration
# Usage: fleet-manager.sh <command> [args]

set -e

export PATH="/home/ubuntu/.local/bin:$PATH"

# Ensure mcp-proxy is installed
pip show mcp-proxy >/dev/null 2>&1 || pip install mcp-proxy >/dev/null 2>&1

# MCP helper function
mcp_call() {
    local tool="$1"
    local args="$2"
    
    (
        echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"fleet-manager","version":"1.0"}}}'
        sleep 2
        echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$args}}"
        sleep 5
    ) | timeout 30 npx -y cursor-background-agent-mcp-server 2>/dev/null | tail -1
}

case "$1" in
    list)
        echo "=== Active Fleet ==="
        LIST_OUTPUT=$(mcp_call "listAgents" "{}" | jq -r '.result.content[0].text | fromjson | .agents[] | "\(.status)\t\(.id)\t\(.source.repository | split("/")[-1])\t\(.name)"')
        if command -v column >/dev/null 2>&1; then
            echo "$LIST_OUTPUT" | column -t -s $'\t'
        else
            echo "$LIST_OUTPUT"
        fi
        ;;
    
    running)
        echo "=== Running Agents ==="
        mcp_call "listAgents" "{}" | jq -r '.result.content[0].text | fromjson | .agents[] | select(.status == "RUNNING") | {id, repo: .source.repository, branch: .target.branchName, name}'
        ;;
    
    status)
        AGENT_ID="$2"
        if [ -z "$AGENT_ID" ]; then
            echo "Usage: fleet-manager.sh status <agent-id>"
            exit 1
        fi
        echo "=== Agent Status: $AGENT_ID ==="
        mcp_call "getAgentStatus" "{\"agentId\":\"$AGENT_ID\"}" | jq -r '.result.content[0].text | fromjson'
        ;;
    
    spawn)
        REPO="$2"
        TASK="$3"
        REF="${4:-main}"
        
        if [ -z "$REPO" ] || [ -z "$TASK" ]; then
            echo "Usage: fleet-manager.sh spawn <repo-url> <task-description> [ref]"
            echo "Example: fleet-manager.sh spawn https://github.com/FlipsideCrypto/terraform-modules 'Update dependencies' main"
            exit 1
        fi
        
        # Get my own agent ID for context
        MY_ID=$(mcp_call "listAgents" "{}" | jq -r '.result.content[0].text | fromjson | .agents[] | select(.status == "RUNNING") | .id' | head -1)
        
        SPAWN_CONTEXT="TASK: $TASK

COORDINATION:
- Control Manager Agent: $MY_ID
- Control Center: FSC Control Center
- Report progress via PR and addFollowup

INSTRUCTIONS:
1. Complete the assigned task
2. Create PR when done
3. The control manager can send you updates via addFollowup"

        echo "=== Spawning Agent ==="
        echo "Repository: $REPO"
        echo "Ref: $REF"
        echo "Task: $TASK"
        echo "Control Manager: $MY_ID"
        echo ""
        
        ARGS=$(jq -n \
            --arg task "$SPAWN_CONTEXT" \
            --arg repo "$REPO" \
            --arg ref "$REF" \
            '{prompt: {text: $task}, source: {repository: $repo, ref: $ref}}')
        
        RESULT=$(mcp_call "launchAgent" "$ARGS")
        echo "$RESULT" | jq -r '.result.content[0].text | fromjson'
        ;;
    
    followup)
        AGENT_ID="$2"
        MESSAGE="$3"
        
        if [ -z "$AGENT_ID" ] || [ -z "$MESSAGE" ]; then
            echo "Usage: fleet-manager.sh followup <agent-id> <message>"
            exit 1
        fi
        
        echo "=== Sending Followup to $AGENT_ID ==="
        ARGS=$(jq -n --arg id "$AGENT_ID" --arg msg "$MESSAGE" '{agentId: $id, prompt: {text: $msg}}')
        mcp_call "addFollowup" "$ARGS" | jq -r '.result.content[0].text'
        ;;
    
    conversation)
        AGENT_ID="$2"
        if [ -z "$AGENT_ID" ]; then
            echo "Usage: fleet-manager.sh conversation <agent-id>"
            exit 1
        fi
        echo "=== Conversation for $AGENT_ID ==="
        mcp_call "getAgentConversation" "{\"agentId\":\"$AGENT_ID\"}" | jq -r '.result.content[0].text | fromjson | .messages[] | "[\(.type)] \(.text[0:200])..."'
        ;;
    
    archive)
        AGENT_ID="$2"
        if [ -z "$AGENT_ID" ]; then
            echo "Usage: fleet-manager.sh archive <agent-id>"
            exit 1
        fi
        OUTPUT="/workspace/memory-bank/recovery/conversation-${AGENT_ID}.json"
        mkdir -p /workspace/memory-bank/recovery
        echo "=== Archiving conversation to $OUTPUT ==="
        mcp_call "getAgentConversation" "{\"agentId\":\"$AGENT_ID\"}" | jq -r '.result.content[0].text' > "$OUTPUT"
        echo "Archived. Size: $(wc -c < "$OUTPUT") bytes"
        ;;
    
    repos)
        echo "=== Available Repositories ==="
        mcp_call "listRepositories" "{}" | jq -r '.result.content[0].text | fromjson | .repositories[] | "\(.owner)/\(.name)"' | head -30
        ;;
    
    help|*)
        echo "Fleet Manager - Control Center Agent Orchestration"
        echo ""
        echo "Commands:"
        echo "  list                         List all agents"
        echo "  running                      Show only running agents"
        echo "  status <agent-id>            Get detailed agent status"
        echo "  spawn <repo> <task> [ref]    Spawn new agent in repository"
        echo "  followup <agent-id> <msg>    Send message to agent"
        echo "  conversation <agent-id>      View agent conversation"
        echo "  archive <agent-id>           Archive conversation to file"
        echo "  repos                        List available repositories"
        echo ""
        echo "Examples:"
        echo "  fleet-manager.sh list"
        echo "  fleet-manager.sh spawn https://github.com/FlipsideCrypto/terraform-modules 'Update deps' main"
        echo "  fleet-manager.sh followup bc-xxx 'Please also update tests'"
        ;;
esac
