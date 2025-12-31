// Package github provides a Go client for interacting with the GitHub API.
//
// This package wraps the GitHub CLI (gh) for reliable, authenticated access
// to GitHub resources. It provides structured types for common GitHub entities
// and methods for repository management, PR handling, and issue tracking.
//
// # Usage
//
//	client := github.New()
//
//	// List organizations
//	orgs, err := client.ListOrganizations()
//
//	// List repositories
//	repos, err := client.ListRepositories("jbcom")
//
//	// Work with PRs
//	prs, err := client.ListOpenPRs("jbcom/control-center")
//	err = client.PostComment("jbcom/control-center", 123, "Great work!")
//
// # Authentication
//
// The client uses the GITHUB_TOKEN or GH_TOKEN environment variable,
// which is automatically picked up by the gh CLI.
//
// # Why gh CLI?
//
// Using the gh CLI instead of direct API calls provides:
//   - Automatic authentication handling
//   - Rate limiting and retry logic
//   - Consistent behavior with local development
//   - No external Go dependencies
package github
