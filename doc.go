// Package controlcenter provides enterprise AI orchestration for the jbcom ecosystem.
//
// Control Center is the unified CLI and library for managing AI agents,
// repository synchronization, and enterprise workflows across the jbcom
// organization and its child organizations.
//
// # Installation
//
//	go install github.com/jbcom/control-center/cmd/control-center@latest
//
// # CLI Usage
//
//	# Review a PR with AI
//	control-center reviewer --repo jbcom/my-project --pr 123
//
//	# Analyze CI failures
//	control-center fixer --repo jbcom/my-project --pr 123
//
//	# Triage issues across a repository
//	control-center curator --repo jbcom/my-project
//
//	# Run enterprise orchestration
//	control-center gardener --target all
//
// # Package Structure
//
// The library is organized into the following packages:
//
//   - [github.com/jbcom/control-center/pkg/clients/github] - GitHub API client
//   - [github.com/jbcom/control-center/pkg/clients/ollama] - Ollama GLM 4.6 client
//   - [github.com/jbcom/control-center/pkg/clients/jules] - Google Jules client
//   - [github.com/jbcom/control-center/pkg/clients/cursor] - Cursor Cloud Agent client
//   - [github.com/jbcom/control-center/pkg/orchestrator] - Orchestration logic
//
// # Configuration
//
// Control Center uses Viper for configuration. Set these environment variables:
//
//	GITHUB_TOKEN       - GitHub token with repo scope (required)
//	OLLAMA_API_KEY     - Ollama Cloud API key
//	GOOGLE_JULES_API_KEY - Google Jules API key
//	CURSOR_API_KEY     - Cursor Cloud Agent API key
//
// Or create ~/.control-center.yaml:
//
//	log:
//	  level: info
//	  format: text
//
// # Related Projects
//
//   - jbcom/docs - Enterprise documentation site
//   - agentic-dev-library - AI agent packages
//   - extended-data-library - Data utilities
//   - strata-game-library - 3D graphics library
package controlcenter
