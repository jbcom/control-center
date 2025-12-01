# Agentic Control Setup - FlipsideCrypto Ecosystem

## Setup Completed: 2025-12-01

### What Was Created

Complete agentic control configuration system for managing AI agent fleet across FlipsideCrypto repositories.

### Directory Structure

```
/workspace/agentic-control/
├── README.md                      # Overview and quick start guide
├── agents/
│   └── registry.yaml             # Agent definitions and capabilities
├── workflows/
│   ├── dependency-update.yaml   # Automated dependency management
│   └── infrastructure-deployment.yaml # Terraform deployment workflow
├── orchestration/
│   ├── fleet-config.yaml        # Fleet management configuration
│   └── handoff-protocol.md      # Agent handoff procedures
├── monitoring/
│   ├── config.yaml              # Monitoring and alerting rules
│   └── metrics.py               # Metrics collection script
└── capabilities/
    ├── matrix.yaml              # Capability matrix and routing
    └── router.py                # Intelligent task routing system
```

### Key Components

#### 1. Agent Registry
- **10 specialized agents** defined with specific capabilities
- Each agent has defined repositories, tokens, and task limits
- Priority levels from critical to low
- Max concurrent task management

#### 2. Fleet Orchestration
- Diamond pattern communication for hub-and-spoke coordination
- Automatic agent spawning based on task requirements
- Cross-repository coordination capabilities
- jbcom counterparty integration

#### 3. Capability Matrix
- **10 capability domains**: terraform, security, dependencies, lambda, automation, review, documentation, observability, continuity, coordination
- Pattern-based routing for automatic agent selection
- Repository-specific routing rules
- Performance benchmarks for each capability

#### 4. Monitoring System
- Real-time agent status tracking
- Task completion metrics
- Repository activity monitoring
- Health score calculation (0-100)
- Alert rules for critical conditions
- Audit trail with 365-day retention

#### 5. Workflows
- **Dependency Update**: Weekly automated checks of jbcom packages
- **Infrastructure Deployment**: Full Terraform deployment with security validation
- Manual and scheduled triggers
- Rollback capabilities
- Multi-stage approval processes

### Agent Capabilities

| Agent | Type | Primary Function | Max Tasks |
|-------|------|------------------|-----------|
| fsc-control-center | Orchestrator | Central coordination | 5 |
| infrastructure-agent | Specialist | Terraform management | 3 |
| security-agent | Specialist | Security scanning | 2 |
| lambda-ops-agent | Specialist | SAM Lambda operations | 3 |
| package-manager-agent | Specialist | Dependency management | 2 |
| documentation-agent | Specialist | Documentation updates | 2 |
| pipeline-agent | Specialist | CI/CD management | 3 |
| monitoring-agent | Specialist | Observability | 2 |
| code-review-agent | Specialist | Automated reviews | 4 |
| recovery-agent | Specialist | Session recovery | 1 |

### Routing Intelligence

The task router (`capabilities/router.py`) provides:
- Automatic capability detection from task descriptions
- Workload-balanced agent selection
- Complexity estimation
- Collaboration pattern selection
- Task validation before assignment

### Monitoring Capabilities

The monitoring system (`monitoring/metrics.py`) tracks:
- Agent health and performance
- Task success/failure rates
- API usage and rate limits
- Repository activity
- System health score

### Integration Points

#### GitHub Integration
- Issue-based coordination
- PR-based task tracking
- Automated reviews
- Workflow triggers

#### Cursor API Integration
- Agent spawning
- Direct agent communication
- Session recovery
- Fleet management

#### jbcom Ecosystem
- Package dependency tracking
- Upstream contribution flow
- Cross-organization handoffs
- Release coordination

### Usage Examples

#### Deploy an Agent
```bash
cd /workspace/agentic-control
./orchestration/deploy-agent.sh infrastructure "Update terraform modules"
```

#### Route a Task
```python
python capabilities/router.py "Update dependencies in terraform-modules"
# Returns: {selected_agent: "package-manager-agent", reason: "..."}
```

#### Check System Health
```python
python monitoring/metrics.py --report
# Generates comprehensive health report
```

#### Trigger Workflow
```bash
# Manual trigger
gh workflow dispatch dependency-update

# Or via orchestration
./workflows/run.sh dependency-update
```

### Security Considerations

- Least privilege access per agent
- Scoped GitHub tokens (FLIPSIDE_GITHUB_TOKEN, GITHUB_JBCOM_TOKEN)
- Audit logging enabled
- Automated security scanning in workflows
- Approval gates for production deployments

### Next Steps

1. **Activate monitoring**: Start the monitoring daemon
   ```bash
   python /workspace/agentic-control/monitoring/metrics.py &
   ```

2. **Test routing**: Validate task routing
   ```bash
   python /workspace/agentic-control/capabilities/router.py --report
   ```

3. **Schedule workflows**: Enable automated workflows
   ```bash
   # Add to GitHub Actions or cron
   ```

4. **Configure alerts**: Set up Slack/PagerDuty notifications

### Maintenance

- Review agent performance weekly
- Update capability matrix as new skills are added
- Monitor health scores daily
- Archive audit logs monthly
- Update routing patterns based on usage

### Documentation

All configuration is self-documenting through:
- YAML schemas with descriptions
- Python docstrings
- Markdown documentation in each directory
- Inline comments in configuration files

---

**Configuration Version**: 1.0.0
**Last Updated**: 2025-12-01
**Status**: Active and Ready