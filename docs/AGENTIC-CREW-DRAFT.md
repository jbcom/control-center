# agentic-crew Repository Draft

> **Status**: BLOCKED by jbcom/vendor-connectors#17 (AI sub-package)
> 
> This document captures the research and design work done in preparation for repository creation.

## Research Summary

### Reference Implementations Studied

#### 1. jbcom/otterfall/.crewai
```
.crewai/
├── manifest.yaml          # Crew registry, LLM config, flows
├── crews/                 # Crew definitions
│   └── <crew_name>/
│       ├── agents.yaml    # Agent configurations
│       └── tasks.yaml     # Task configurations
└── knowledge/             # Knowledge bases for crews
```

**Key Pattern**: YAML-based crew definitions with knowledge integration.

#### 2. jbcom/agentic-control/python
```
python/
├── src/crew_agents/
│   ├── __init__.py        # Package exports (Crews + Flows)
│   ├── crews/             # Python crew implementations
│   │   └── <crew>/
│   │       ├── <crew>_crew.py  # @CrewBase decorated class
│   │       └── config/         # agents.yaml, tasks.yaml
│   ├── flows/             # Multi-crew orchestration
│   ├── tools/             # Custom tools (file_tools.py)
│   ├── base/              # Shared archetypes
│   └── config/            # LLM configuration
├── crewbase.yaml          # Root crew config with tasks
└── pyproject.toml         # Package definition
```

**Key Pattern**: Python @CrewBase classes + YAML configs + multi-crew Flows.

---

## Proposed agentic-crew Structure

### Repository Layout

```
agentic-crew/
├── src/
│   └── agentic_crew/
│       ├── __init__.py           # Package exports
│       ├── core/                 # Core abstractions
│       │   ├── __init__.py
│       │   ├── client.py         # AgenticCrew main client
│       │   └── modes.py          # OperationMode enum
│       │
│       ├── crews/                # Reusable crew definitions
│       │   ├── __init__.py
│       │   ├── triage/           # PR/Issue triage crew
│       │   │   ├── __init__.py
│       │   │   ├── triage_crew.py
│       │   │   └── config/
│       │   │       ├── agents.yaml
│       │   │       └── tasks.yaml
│       │   ├── review/           # Code review crew
│       │   │   ├── __init__.py
│       │   │   ├── review_crew.py
│       │   │   └── config/
│       │   └── ops/              # DevOps crew
│       │       ├── __init__.py
│       │       ├── ops_crew.py
│       │       └── config/
│       │
│       ├── tools/                # Tool wrappers
│       │   ├── __init__.py
│       │   └── connector_tools.py  # vendor_connectors.ai.tools wrapper
│       │
│       ├── server/               # HTTP API for agentic-control
│       │   ├── __init__.py
│       │   ├── app.py            # FastAPI/Starlette app
│       │   ├── routes/
│       │   │   ├── tasks.py      # POST /tasks - receive delegated tasks
│       │   │   ├── health.py     # GET /health - health check
│       │   │   └── registration.py  # POST /register - fleet registration
│       │   └── middleware/
│       │       └── auth.py       # Authentication for agentic-control
│       │
│       └── cli/                  # Command-line interface
│           ├── __init__.py
│           └── main.py           # CLI entry point
│
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_crews/
│   └── test_server/
│
├── .cursor/                      # Cursor rules (synced from control-center)
│   └── rules/
│
├── pyproject.toml
├── README.md
└── LICENSE
```

### Package Exports

```python
# src/agentic_crew/__init__.py
from agentic_crew.core.client import AgenticCrew
from agentic_crew.core.modes import OperationMode
from agentic_crew.crews import (
    TriageCrew,
    ReviewCrew,
    OpsCrew,
)

__all__ = [
    "AgenticCrew",
    "OperationMode",
    "TriageCrew",
    "ReviewCrew",
    "OpsCrew",
]
```

---

## Dual-Mode Operation Design

### Operation Modes

```python
from enum import Enum

class OperationMode(Enum):
    """How agentic-crew communicates with external systems."""
    
    STANDALONE = "standalone"
    """Direct vendor-connectors import. Low-latency, no audit trail."""
    
    REGISTERED = "registered" 
    """HTTP API for agentic-control. Fleet membership, audit trail."""
    
    HYBRID = "hybrid"
    """Both direct access + fleet registration. Best of both worlds."""
```

### Client Interface

```python
from typing import Optional
from agentic_crew.core.modes import OperationMode

class AgenticCrew:
    """Main client for agentic-crew.
    
    Usage:
        # Mode 1: Standalone (direct vendor-connectors)
        crew = AgenticCrew(mode=OperationMode.STANDALONE)
        result = crew.run_triage(pr_url)
        
        # Mode 2: Registered (part of agentic-control fleet)
        crew = AgenticCrew(
            mode=OperationMode.REGISTERED,
            agentic_control_url="http://localhost:3000",
        )
        await crew.register()  # Registers with agentic-control
        # Now agentic-control can delegate tasks to this crew
        
        # Mode 3: Hybrid (both)
        crew = AgenticCrew(
            mode=OperationMode.HYBRID,
            agentic_control_url="http://localhost:3000",
        )
        await crew.register()
        # Direct calls + fleet participation
    """
    
    def __init__(
        self,
        mode: OperationMode = OperationMode.STANDALONE,
        agentic_control_url: Optional[str] = None,
    ):
        self.mode = mode
        self.agentic_control_url = agentic_control_url
        self._connectors = None
        self._registered = False
    
    def _get_connectors(self):
        """Lazy load vendor-connectors."""
        if self._connectors is None:
            from vendor_connectors import VendorConnectors
            self._connectors = VendorConnectors()
        return self._connectors
    
    async def register(self):
        """Register with agentic-control for fleet membership."""
        if self.mode == OperationMode.STANDALONE:
            raise ValueError("Cannot register in standalone mode")
        
        # POST to agentic-control with our capabilities
        # ...
        self._registered = True
    
    def run_triage(self, pr_url: str):
        """Run the triage crew on a PR."""
        from agentic_crew.crews import TriageCrew
        
        crew = TriageCrew(
            connectors=self._get_connectors(),
            mode=self.mode,
        )
        return crew.kickoff(inputs={"pr_url": pr_url})
```

### Communication Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       agentic-crew                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                            │
│  │   Inbound   │                                            │
│  ├─────────────┤                                            │
│  │ HTTP API    │◄─── Tasks from agentic-control            │
│  │ CLI         │◄─── Local execution                       │
│  └─────────────┘                                            │
│                                                             │
│  ┌─────────────┐                                            │
│  │  Internal   │                                            │
│  ├─────────────┤                                            │
│  │ CrewAI      │     Agent-to-agent within crews           │
│  └─────────────┘                                            │
│                                                             │
│  ┌─────────────┐                                            │
│  │  Outbound   │                                            │
│  ├─────────────┤                                            │
│  │ vendor-     │───► Direct Python import (STANDALONE)     │
│  │ connectors  │                                            │
│  │             │───► Via agentic-control HTTP (REGISTERED) │
│  │             │     (for audit trail, rate limiting)      │
│  └─────────────┘                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Integration with vendor-connectors

### When vendor-connectors#17 Lands

The `vendor_connectors.ai.tools` module will provide LangChain-compatible tools:

```python
# From vendor-connectors (after #17)
from vendor_connectors.ai.tools import (
    get_all_tools,
    get_tools_for_crew,
    GitHubTools,
    SlackTools,
)
```

### agentic-crew Tool Wrapper

```python
# src/agentic_crew/tools/connector_tools.py
from typing import List, Optional
from crewai_tools import BaseTool

def get_tools_for_crew(
    tool_names: List[str],
    connectors: Optional["VendorConnectors"] = None,
) -> List[BaseTool]:
    """Get vendor-connector tools wrapped for CrewAI.
    
    Args:
        tool_names: List of tool names (e.g., "github.get_pr", "slack.send")
        connectors: Optional VendorConnectors instance (creates one if not provided)
    
    Returns:
        List of CrewAI-compatible tools
    
    Example:
        tools = get_tools_for_crew([
            "github.get_pr",
            "github.list_files",
            "github.post_comment",
            "slack.send_message",
        ])
        
        agent = Agent(
            role="Reviewer",
            tools=tools,
        )
    """
    from vendor_connectors.ai.tools import get_tools_for_crew as _get_tools
    
    if connectors is None:
        from vendor_connectors import VendorConnectors
        connectors = VendorConnectors()
    
    return _get_tools(tool_names, connectors=connectors)
```

---

## Crew Definitions

### Triage Crew

```python
# src/agentic_crew/crews/triage/triage_crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from agentic_crew.tools.connector_tools import get_tools_for_crew

@CrewBase
class TriageCrew:
    """Multi-agent crew for PR/Issue triage.
    
    Agents:
    - Analyzer: Reads PR details, identifies type and scope
    - Reviewer: Checks files changed, identifies risk areas
    - Reporter: Summarizes findings, posts to Slack/GitHub
    """
    
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    def __init__(self, connectors=None, mode=None):
        self.connectors = connectors
        self.mode = mode
        
        # Load tools from vendor-connectors
        self.tools = get_tools_for_crew([
            "github.get_pr",
            "github.list_files",
            "github.get_diff",
            "github.post_comment",
            "slack.send_message",
        ], connectors=connectors)
    
    @agent
    def analyzer(self) -> Agent:
        """Analyzes PR/issue to determine type and scope."""
        return Agent(
            config=self.agents_config["analyzer"],
            tools=[
                self.tools["github.get_pr"],
                self.tools["github.list_files"],
            ],
            verbose=True,
        )
    
    @agent
    def reviewer(self) -> Agent:
        """Reviews code changes and identifies risks."""
        return Agent(
            config=self.agents_config["reviewer"],
            tools=[
                self.tools["github.get_diff"],
            ],
            verbose=True,
        )
    
    @agent
    def reporter(self) -> Agent:
        """Reports findings to appropriate channels."""
        return Agent(
            config=self.agents_config["reporter"],
            tools=[
                self.tools["github.post_comment"],
                self.tools["slack.send_message"],
            ],
            verbose=True,
        )
    
    @task
    def analyze_pr(self) -> Task:
        return Task(config=self.tasks_config["analyze_pr"])
    
    @task
    def review_changes(self) -> Task:
        return Task(config=self.tasks_config["review_changes"])
    
    @task
    def report_findings(self) -> Task:
        return Task(config=self.tasks_config["report_findings"])
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

### Agent Configuration

```yaml
# src/agentic_crew/crews/triage/config/agents.yaml
analyzer:
  role: "PR Analyzer"
  goal: "Analyze pull requests to determine their type, scope, and priority"
  backstory: |
    You are an expert at understanding code changes and their implications.
    You can quickly identify the purpose of a PR, whether it's a bug fix,
    feature, refactor, or documentation change. You assess the scope and
    risk level to help prioritize reviews.

reviewer:
  role: "Code Reviewer"
  goal: "Review code changes to identify potential issues and risks"
  backstory: |
    You are a senior engineer with deep experience in code review.
    You look for common issues like security vulnerabilities, performance
    problems, missing tests, and style inconsistencies. You provide
    constructive feedback to help improve code quality.

reporter:
  role: "Findings Reporter"
  goal: "Summarize and report triage findings to appropriate channels"
  backstory: |
    You are skilled at communicating technical information clearly and
    concisely. You know how to craft messages that are informative without
    being overwhelming, and you route information to the right channels.
```

---

## HTTP Server for Fleet Registration

### FastAPI Application

```python
# src/agentic_crew/server/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="agentic-crew",
    description="CrewAI-based AI agent crews",
    version="0.1.0",
)

class TaskRequest(BaseModel):
    """Task delegated from agentic-control."""
    task_id: str
    crew_name: str
    inputs: dict
    callback_url: Optional[str] = None

class TaskResponse(BaseModel):
    """Response after task execution."""
    task_id: str
    status: str  # "completed", "failed", "in_progress"
    result: Optional[dict] = None
    error: Optional[str] = None

@app.post("/tasks", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """Execute a task delegated from agentic-control."""
    from agentic_crew.crews import get_crew_by_name
    
    crew_class = get_crew_by_name(request.crew_name)
    if crew_class is None:
        raise HTTPException(404, f"Crew '{request.crew_name}' not found")
    
    try:
        crew = crew_class()
        result = await crew.crew().kickoff_async(inputs=request.inputs)
        return TaskResponse(
            task_id=request.task_id,
            status="completed",
            result={"output": str(result)},
        )
    except Exception as e:
        return TaskResponse(
            task_id=request.task_id,
            status="failed",
            error=str(e),
        )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "crews": ["triage", "review", "ops"]}

@app.post("/register")
async def register(agentic_control_url: str):
    """Register with agentic-control fleet."""
    # Implementation: POST our capabilities to agentic-control
    pass
```

---

## Dependencies

```toml
# pyproject.toml
[project]
name = "agentic-crew"
version = "0.1.0"
description = "CrewAI-based AI agent crews for the jbcom ecosystem"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "Jon Bogaty", email = "jon@jonbogaty.com" }]
keywords = ["crewai", "ai-agents", "automation", "langchain"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]

dependencies = [
    "crewai[tools,anthropic]>=1.5.0",
    "vendor-connectors[ai]>=0.3.0",  # For AI tools - REQUIRES #17
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
server = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
]
tests = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "pytest-cov>=4.1.0",
]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[project.scripts]
agentic-crew = "agentic_crew.cli.main:main"
agentic-crew-server = "agentic_crew.server.app:run"

[project.urls]
Homepage = "https://github.com/jbcom/agentic-crew"
Repository = "https://github.com/jbcom/agentic-crew"
Documentation = "https://github.com/jbcom/agentic-crew#readme"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/agentic_crew"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "C4"]
ignore = ["D", "T201"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## Implementation Order

### Phase 1: Scaffold (Can Start Now)
1. Create repository structure
2. Set up pyproject.toml with placeholder dependencies
3. Create core abstractions (modes, client interface)
4. Add Cursor rules from control-center

### Phase 2: Crews (After vendor-connectors#17)
1. Wire up `vendor_connectors.ai.tools`
2. Implement TriageCrew
3. Implement ReviewCrew
4. Implement OpsCrew

### Phase 3: Server (After Crews)
1. Implement FastAPI server
2. Add task execution endpoint
3. Add fleet registration endpoint
4. Test with agentic-control

### Phase 4: Integration (Final)
1. End-to-end testing
2. Documentation
3. CI/CD setup
4. Initial release

---

## Related Issues

- **Blocked by**: jbcom/vendor-connectors#17 (AI sub-package)
- **Blocks**: jbcom/agentic-control#8 (refactor)
- **Epic**: jbcom/jbcom-control-center#340

---

*Draft created: 2025-12-07*
*Last updated: 2025-12-07*
