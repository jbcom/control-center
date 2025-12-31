// Package cursor provides a Go client for the Cursor Cloud Agent API.
//
// Cursor Cloud Agents are long-running AI assistants that operate in the
// background with full IDE context. They're ideal for complex debugging,
// large feature implementations, and tasks requiring sustained attention.
//
// # Usage
//
//	client := cursor.New("your-api-key")
//
//	// Launch a new agent
//	agent, err := client.LaunchAgent(cursor.LaunchAgentRequest{
//	    Prompt: cursor.PromptConfig{
//	        Text: "Fix the failing tests in the auth module",
//	    },
//	    Source: cursor.SourceConfig{
//	        Repository: "jbcom/my-project",
//	        Branch:     "fix/auth-tests",
//	    },
//	})
//
//	// Check agent status
//	status, err := client.GetAgent(agent.ID)
//
//	// List all agents
//	agents, err := client.ListAgents()
//
//	// Send a follow-up message
//	err = client.SendFollowup(agent.ID, "Also update the documentation")
//
// # Agent States
//
//   - running: Agent is actively working
//   - waiting: Agent is waiting for user input
//   - completed: Agent has finished
//   - failed: Agent encountered an error
//
// # API Endpoint
//
// The client connects to https://api.cursor.com/v0.
//
// # Authentication
//
// Requires a CURSOR_API_KEY environment variable or explicit key.
package cursor
