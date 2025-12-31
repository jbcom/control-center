// Package orchestrator provides enterprise-level AI orchestration logic.
//
// This package implements the core orchestration patterns for managing
// AI agents across the jbcom ecosystem. It coordinates between GitHub,
// Ollama, Jules, and Cursor to automate repository management.
//
// # Gardener
//
// The Gardener orchestrates enterprise-level cascade operations:
//
//	gardener := orchestrator.NewGardener(orchestrator.GardenerConfig{
//	    GitHubClient: ghClient,
//	    Target:       "all",
//	    Decompose:    false,
//	    Backlog:      true,
//	})
//
//	results, err := gardener.Run(ctx)
//
// The Gardener:
//   - Discovers organizations from org-registry.json
//   - Auto-heals control centers (missing files, misconfigs)
//   - Processes backlog (stale PRs, unassigned issues)
//   - Decomposes to org-level gardeners (optional)
//
// # Cascade Pattern
//
// The cascade flows from enterprise to repositories:
//
//	jbcom-gardener (enterprise)
//	    └─> org-gardener (organization)
//	            └─> repository workflows
//
// Instructions can be "planted" at any level and will decompose downward.
//
// # Prompt Queue
//
// The Gardener processes prompt queue issues with this format:
//
//	Title: 🌱 PLANT: <instruction>
//	Body:
//	  🎯 TARGET: <all|org-name|org/repo>
//	  📋 SCOPE: <enterprise|organization|repository>
//
// # Related Packages
//
//   - github.com/jbcom/control-center/pkg/clients/github - GitHub operations
//   - github.com/jbcom/control-center/pkg/clients/ollama - AI analysis
package orchestrator
