// Package jules provides a Go client for the Google Jules API.
//
// Google Jules is an AI agent for automated code changes. It creates PRs
// automatically based on natural language prompts, making it ideal for
// multi-file refactoring and documentation updates.
//
// # Usage
//
//	client := jules.New("your-api-key")
//
//	// Create a session with auto PR creation
//	session, err := client.CreateSession(jules.CreateSessionRequest{
//	    Prompt: "Add input validation to the User model",
//	    SourceContext: jules.SourceContext{
//	        Source: "sources/github/jbcom/my-project",
//	        GitHubRepoContext: &jules.GitHubRepoContext{
//	            StartingBranch: "main",
//	        },
//	    },
//	    AutomationMode: "AUTO_CREATE_PR",
//	})
//
//	// Check session status
//	status, err := client.GetSession(session.Name)
//
//	// List all sessions
//	sessions, err := client.ListSessions()
//
//	// Approve a pending plan
//	err = client.ApprovePlan(session.Name)
//
// # Automation Modes
//
//   - AUTO_CREATE_PR: Automatically creates a PR when done
//   - MANUAL: Requires explicit approval of the plan
//
// # API Endpoint
//
// The client connects to https://jules.googleapis.com/v1alpha.
//
// # Authentication
//
// Requires a GOOGLE_JULES_API_KEY environment variable or explicit key.
package jules
