# CrewAI Custom Manager Agent for Agentic Control

## Overview

The `agentic-control-crews` Python package can expose a **Custom Manager Agent** that orchestrates the entire agentic-control ecosystem, providing a high-level interface for users who prefer CrewAI's declarative approach over direct MCP integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                 AgenticControlManager (CrewAI)                       │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Custom Manager Agent                      │   │
│  │  - Understands fleet state                                   │   │
│  │  - Delegates to specialized agents                          │   │
│  │  - Manages sandbox lifecycle                                 │   │
│  │  - Handles HITL checkpoints                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │ SandboxAgent│     │ TriageAgent │     │ HandoffAgent│           │
│  │ (execution) │     │ (recovery)  │     │ (transfer)  │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    Node.js Bridge (IPC/HTTP)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│              agentic-control (Node.js Runtime)                       │
│                                                                      │
│  Fleet API │ Sandbox API │ GitHub API │ Triage API │ Handoff API    │
└─────────────────────────────────────────────────────────────────────┘
```

## Custom Manager Agent Implementation

Based on [CrewAI Custom Manager Agent docs](https://docs.crewai.com/en/learn/custom-manager-agent):

```python
# crew_agents/manager/agentic_control_manager.py

from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent, task, crew
from typing import List, Optional
import subprocess
import json

class AgenticControlManagerAgent(Agent):
    """
    Custom Manager Agent that orchestrates the agentic-control ecosystem.
    
    Capabilities:
    - Spawn sandboxed agents (Claude, Cursor, Custom)
    - Monitor fleet health and triage failures
    - Coordinate handoffs between agents
    - Manage HITL checkpoints
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            role="Agentic Control Fleet Manager",
            goal="Orchestrate AI agent fleets to accomplish complex development tasks safely and efficiently",
            backstory="""You are the central orchestrator for an AI agent fleet. 
            You understand when to delegate to specialized agents, when to spawn 
            sandboxed execution environments, and when to escalate to human review.
            
            You have access to:
            - Sandbox execution (isolated Docker containers)
            - Fleet status monitoring
            - Agent triage and recovery
            - Cross-agent handoff coordination
            
            You prioritize safety, efficiency, and clear communication with humans.""",
            allow_delegation=True,
            verbose=True,
            **kwargs
        )
        
        # Bridge to Node.js runtime
        self._node_bridge = NodeBridge()
    
    def spawn_sandbox(
        self, 
        runtime: str = "claude",
        prompt: str = "",
        workspace: str = ".",
        timeout: int = 300
    ) -> dict:
        """Spawn a sandboxed agent execution."""
        return self._node_bridge.call("sandbox", "run", {
            "runtime": runtime,
            "prompt": prompt,
            "workspace": workspace,
            "timeout": timeout
        })
    
    def get_fleet_status(self) -> dict:
        """Get current fleet status."""
        return self._node_bridge.call("fleet", "status", {})
    
    def triage_agent(self, agent_id: str) -> dict:
        """Triage a failed agent."""
        return self._node_bridge.call("triage", "analyze", {
            "agent_id": agent_id
        })
    
    def handoff_to(self, target: str, context: dict) -> dict:
        """Handoff current work to another agent or human."""
        return self._node_bridge.call("handoff", "transfer", {
            "target": target,
            "context": context
        })


class NodeBridge:
    """Bridge to agentic-control Node.js runtime."""
    
    def call(self, module: str, method: str, args: dict) -> dict:
        """Call agentic-control CLI and parse JSON response."""
        cmd = ["agentic", module, method, "--json"]
        for key, value in args.items():
            cmd.extend([f"--{key}", str(value)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
```

## Crew Configuration with Custom Manager

```yaml
# crewbase.yaml (updated)

version: "2.0"
name: "agentic_control_crew"

# Use custom manager agent
manager_agent:
  class: "crew_agents.manager.AgenticControlManagerAgent"
  llm: "claude-sonnet-4-20250514"

# Hierarchical process with custom manager
process: hierarchical
verbose: true
memory: true
planning: true

# Specialized sub-agents the manager can delegate to
agents_config: 'config/agents.yaml'

# Agent definitions
agents:
  sandbox_executor:
    role: "Sandbox Execution Specialist"
    goal: "Execute tasks safely in isolated Docker containers"
    backstory: "Expert at containerized execution with zero host impact"
    tools:
      - spawn_sandbox
      - monitor_sandbox
      - extract_output

  triage_specialist:
    role: "Agent Triage Specialist"  
    goal: "Analyze and recover from agent failures"
    backstory: "Expert at diagnosing agent issues and applying fixes"
    tools:
      - analyze_failure
      - recover_agent
      - replay_session

  handoff_coordinator:
    role: "Handoff Coordinator"
    goal: "Ensure smooth transitions between agents and humans"
    backstory: "Expert at context preservation and seamless handoffs"
    tools:
      - prepare_handoff
      - transfer_context
      - notify_target

# Tasks the manager can orchestrate
tasks:
  sandbox_execute:
    description: |
      Execute a task in an isolated sandbox.
      
      Available runtimes:
      - claude: Claude Code execution
      - cursor: Cursor background agent
      - custom: Custom script/container
      
      The sandbox provides:
      - Complete isolation from host
      - Workspace volume mounting
      - Output extraction
      - Resource limits
    agent: sandbox_executor
    
  fleet_triage:
    description: |
      Analyze a failed agent and attempt recovery.
      
      Steps:
      1. Load agent conversation history
      2. Identify failure point
      3. Determine recovery strategy
      4. Execute recovery or escalate to human
    agent: triage_specialist
    
  coordinate_handoff:
    description: |
      Prepare and execute a handoff to another agent or human.
      
      Includes:
      - Context preparation
      - State serialization
      - Target notification
      - Handoff verification
    agent: handoff_coordinator
```

## Usage Examples

### 1. Direct Python API

```python
from crew_agents.manager import AgenticControlManagerAgent
from crewai import Crew, Task

# Create manager
manager = AgenticControlManagerAgent()

# Create a task that requires sandbox execution
task = Task(
    description="""
    Create a REST API with authentication.
    Use sandbox execution for safety.
    """,
    expected_output="Working API code with tests"
)

# Manager will automatically delegate to sandbox
crew = Crew(
    agents=[manager],
    tasks=[task],
    process="hierarchical",
    manager_agent=manager
)

result = crew.kickoff()
```

### 2. CLI Integration

```bash
# Run a task through the CrewAI manager
agentic crew run \
  --task "Refactor authentication module" \
  --sandbox true \
  --runtime claude

# Check fleet status via CrewAI
agentic crew status

# Triage via CrewAI manager
agentic crew triage --agent-id abc123
```

### 3. YAML-Based Workflow

```yaml
# workflows/code-review.yaml
name: "AI Code Review Crew"

manager:
  class: AgenticControlManagerAgent
  delegation_strategy: capability_based

workflow:
  - task: fetch_pr_context
    agent: github_agent
    
  - task: sandbox_review
    agent: sandbox_executor
    inputs:
      runtime: claude
      prompt: "Review this PR for security issues"
      
  - task: compile_report
    agent: technical_writer
    
  - task: post_review
    agent: github_agent
    human_input: true  # HITL before posting
```

## Integration with Existing CrewAI Setup

The `crewbase.yaml` already has:
- MCP server configuration (conport, git, filesystem)
- Workflow patterns (TDD, Meshy)
- HITL checkpoints

Adding the Custom Manager Agent means:
1. **Unified Control**: One agent understands the full system
2. **Smart Delegation**: Manager knows when to use sandbox vs direct
3. **Failure Recovery**: Manager can invoke triage automatically
4. **Human Escalation**: Manager handles HITL checkpoints

## Comparison: MCP vs CrewAI Manager

| Aspect | Direct MCP | CrewAI Manager |
|--------|-----------|----------------|
| Interface | Tool calls | Declarative YAML |
| Learning curve | Lower | Higher (CrewAI knowledge) |
| Flexibility | Maximum | Opinionated but powerful |
| Orchestration | Manual | Automatic |
| HITL | Custom impl | Built-in |
| Multi-agent | DIY | Native support |
| Best for | Simple tasks | Complex workflows |

## Implementation Phases

### Phase 1: Core Manager (MVP)
- [ ] `AgenticControlManagerAgent` class
- [ ] `NodeBridge` for CLI integration
- [ ] Basic sandbox delegation
- [ ] Fleet status monitoring

### Phase 2: Sub-Agent Integration
- [ ] `SandboxExecutorAgent`
- [ ] `TriageSpecialistAgent`
- [ ] `HandoffCoordinatorAgent`
- [ ] Manager delegation logic

### Phase 3: Workflow Patterns
- [ ] Sandbox execution workflow
- [ ] Triage recovery workflow
- [ ] Multi-agent handoff workflow
- [ ] HITL checkpoint handling

### Phase 4: CLI & Config
- [ ] `agentic crew` commands
- [ ] YAML workflow definitions
- [ ] Integration with existing crewbase.yaml

## Benefits

1. **For Claude Code / Cursor Users**
   - Safe sandbox execution
   - No system modifications
   - Easy rollback

2. **For Teams**
   - Fleet orchestration
   - Automatic triage
   - Auditable workflows

3. **For CI/CD**
   - Declarative pipelines
   - Reproducible executions
   - Human gates when needed

4. **For Enterprises**
   - Centralized control
   - Policy enforcement
   - Compliance-friendly
