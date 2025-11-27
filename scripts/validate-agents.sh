#!/bin/bash
# Agent Configuration Validation Script
echo "🔍 Agent Configuration Validation"
echo "=================================="
echo ""

PASSED=0
FAILED=0

check() {
    if [ $1 -eq 0 ]; then
        echo "✓ $2"
        ((PASSED++))
    else
        echo "✗ $2"
        ((FAILED++))
    fi
}

# Check Copilot agents
for agent in ci-deployer dependency-coordinator ecosystem-manager game-dev release-coordinator vendor-connectors-consolidator; do
    [ -f ".github/copilot/agents/${agent}.agent.yaml" ]
    check $? "Copilot: ${agent}.agent.yaml"
done

# Check Cursor agents
for agent in ci-deployer dependency-coordinator game-dev jbcom-ecosystem-manager release-coordinator vendor-connectors-consolidator cursor-environment-triage; do
    [ -f ".cursor/agents/${agent}.md" ]
    check $? "Cursor: ${agent}.md"
done

# Check docs
for doc in .github/copilot/AGENTS_GUIDE.md .cursor/MCP_CONFIGURATION_GUIDE.md .cursor/DOCKERFILE_ANALYSIS.md AGENT_FIXES_SUMMARY.md .github/AGENT_QUICK_REFERENCE.md; do
    [ -f "$doc" ]
    check $? "Doc: $(basename $doc)"
done

# Check configs
[ -f ".cursor/mcp.json" ]
check $? "Config: mcp.json"
[ -f ".cursor/Dockerfile" ]
check $? "Config: Dockerfile"
[ -f ".ruler/ruler.toml" ]
check $? "Config: ruler.toml"

echo ""
echo "=================================="
echo "Passed: $PASSED | Failed: $FAILED"
[ $FAILED -eq 0 ] && echo "✓ All checks passed!" || echo "✗ Some checks failed"
exit $FAILED
