package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/jbcom/control-center/pkg/clients/cursor"
	"github.com/jbcom/control-center/pkg/clients/github"
	"github.com/jbcom/control-center/pkg/clients/jules"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	delegatorRepo    string
	delegatorIssue   int
	delegatorCommand string
	delegatorAgent   string
)

var delegatorCmd = &cobra.Command{
	Use:   "delegator",
	Short: "Route tasks to appropriate AI agents",
	Long: `The Delegator routes tasks to the appropriate AI agent based on command type.

Supported agents:
  - Jules: For multi-file refactoring tasks (/jules command)
  - Cursor: For long-running tasks with IDE context (/cursor command)

The delegator parses issue/PR comments for commands and dispatches them
to the appropriate backend agent, posting status updates back to GitHub.

Examples:
  # Delegate a command from an issue
  control-center delegator delegate --repo jbcom/control-center --issue 123 --command "/jules fix the bug"

  # Delegate to a specific agent
  control-center delegator delegate --repo jbcom/control-center --issue 123 --command "fix auth" --agent jules

  # List active delegations
  control-center delegator list`,
}

var delegatorDelegateCmd = &cobra.Command{
	Use:   "delegate",
	Short: "Delegate a task to an AI agent",
	RunE:  runDelegator,
}

var delegatorListCmd = &cobra.Command{
	Use:   "list",
	Short: "List active AI agent sessions",
	RunE:  runDelegatorList,
}

func init() {
	rootCmd.AddCommand(delegatorCmd)
	delegatorCmd.AddCommand(delegatorDelegateCmd)
	delegatorCmd.AddCommand(delegatorListCmd)

	// Flags for delegate subcommand
	delegatorDelegateCmd.Flags().StringVar(&delegatorRepo, "repo", "", "repository (owner/name)")
	delegatorDelegateCmd.Flags().IntVar(&delegatorIssue, "issue", 0, "issue or PR number")
	delegatorDelegateCmd.Flags().StringVar(&delegatorCommand, "command", "", "command to delegate (e.g., '/jules fix bug')")
	delegatorDelegateCmd.Flags().StringVar(&delegatorAgent, "agent", "", "force specific agent (jules or cursor)")
	delegatorDelegateCmd.Flags().StringVar(&outputFormat, "output", "text", "output format (text or json)")

	delegatorDelegateCmd.MarkFlagRequired("repo")
	delegatorDelegateCmd.MarkFlagRequired("command")

	// Flags for list subcommand
	delegatorListCmd.Flags().StringVar(&delegatorAgent, "agent", "", "filter by agent (jules or cursor)")
	delegatorListCmd.Flags().StringVar(&outputFormat, "output", "text", "output format (text or json)")

	viper.BindPFlag("delegator.repo", delegatorDelegateCmd.Flags().Lookup("repo"))
	viper.BindPFlag("delegator.issue", delegatorDelegateCmd.Flags().Lookup("issue"))
	viper.BindPFlag("delegator.command", delegatorDelegateCmd.Flags().Lookup("command"))
	viper.BindPFlag("delegator.agent", delegatorDelegateCmd.Flags().Lookup("agent"))
}

// DelegationResult represents the result of a delegation
type DelegationResult struct {
	Agent     string `json:"agent"`
	SessionID string `json:"session_id,omitempty"`
	AgentID   string `json:"agent_id,omitempty"`
	Status    string `json:"status"`
	Message   string `json:"message"`
}

func runDelegator(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	log.WithFields(log.Fields{
		"repo":    delegatorRepo,
		"issue":   delegatorIssue,
		"command": delegatorCommand,
		"agent":   delegatorAgent,
		"dry_run": dryRun,
	}).Info("Starting delegator")

	// Parse command to determine agent
	agent, task := parseCommand(delegatorCommand, delegatorAgent)
	if agent == "" {
		return fmt.Errorf("could not determine agent from command: %s", delegatorCommand)
	}

	if task == "" {
		return fmt.Errorf("empty task in command: %s", delegatorCommand)
	}

	log.WithFields(log.Fields{
		"agent": agent,
		"task":  task,
	}).Debug("Parsed command")

	// Initialize clients
	ghToken := os.Getenv("GITHUB_TOKEN")
	if ghToken == "" {
		ghToken = os.Getenv("CI_GITHUB_TOKEN")
	}
	if ghToken == "" {
		return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
	}

	ghClient := github.NewClient(ghToken)

	var result DelegationResult

	switch agent {
	case "jules":
		result = delegateToJules(ctx, delegatorRepo, task)
	case "cursor":
		result = delegateToCursor(ctx, delegatorRepo, task)
	default:
		return fmt.Errorf("unknown agent: %s", agent)
	}

	// Output result
	if outputFormat == "json" {
		jsonOut, err := json.Marshal(result)
		if err != nil {
			return fmt.Errorf("failed to marshal result: %w", err)
		}
		fmt.Println(string(jsonOut))
		return nil
	}

	// Post status comment if we have an issue
	if delegatorIssue > 0 && !dryRun {
		comment := formatDelegationComment(result)
		if err := ghClient.PostComment(ctx, delegatorRepo, delegatorIssue, comment); err != nil {
			log.WithError(err).Warn("Failed to post status comment")
		}
	}

	fmt.Printf("Delegated to %s: %s\n", result.Agent, result.Message)
	if result.SessionID != "" {
		fmt.Printf("Session ID: %s\n", result.SessionID)
	}
	if result.AgentID != "" {
		fmt.Printf("Agent ID: %s\n", result.AgentID)
	}

	return nil
}

func parseCommand(command, forceAgent string) (agent, task string) {
	command = strings.TrimSpace(command)

	// Check for explicit agent prefix
	if strings.HasPrefix(command, "/jules ") {
		return "jules", strings.TrimPrefix(command, "/jules ")
	}
	if strings.HasPrefix(command, "/cursor ") {
		return "cursor", strings.TrimPrefix(command, "/cursor ")
	}

	// If agent is forced via flag
	if forceAgent != "" {
		return forceAgent, command
	}

	// Default heuristics based on task type
	lowerCmd := strings.ToLower(command)
	if strings.Contains(lowerCmd, "refactor") ||
		strings.Contains(lowerCmd, "rename") ||
		strings.Contains(lowerCmd, "move") {
		return "jules", command
	}

	// Default to Jules for most tasks
	return "jules", command
}

func delegateToJules(ctx context.Context, repo, task string) DelegationResult {
	julesKey := os.Getenv("GOOGLE_JULES_API_KEY")
	if julesKey == "" {
		return DelegationResult{
			Agent:   "jules",
			Status:  "error",
			Message: "GOOGLE_JULES_API_KEY not configured",
		}
	}

	julesClient := jules.NewClient(jules.Config{
		APIKey: julesKey,
	})

	if dryRun {
		return DelegationResult{
			Agent:   "jules",
			Status:  "dry_run",
			Message: fmt.Sprintf("Would create Jules session for: %s", task),
		}
	}

	session, err := julesClient.CreateSession(ctx, repo, "main", task)
	if err != nil {
		return DelegationResult{
			Agent:   "jules",
			Status:  "error",
			Message: fmt.Sprintf("Failed to create session: %v", err),
		}
	}

	return DelegationResult{
		Agent:     "jules",
		SessionID: session.Name,
		Status:    session.State,
		Message:   fmt.Sprintf("Jules session created for: %s", task),
	}
}

func delegateToCursor(ctx context.Context, repo, task string) DelegationResult {
	cursorKey := os.Getenv("CURSOR_API_KEY")
	if cursorKey == "" {
		return DelegationResult{
			Agent:   "cursor",
			Status:  "error",
			Message: "CURSOR_API_KEY not configured",
		}
	}

	cursorClient := cursor.NewClient(cursor.Config{
		APIKey: cursorKey,
	})

	if dryRun {
		return DelegationResult{
			Agent:   "cursor",
			Status:  "dry_run",
			Message: fmt.Sprintf("Would launch Cursor agent for: %s", task),
		}
	}

	agent, err := cursorClient.LaunchAgent(ctx, repo, "main", task)
	if err != nil {
		return DelegationResult{
			Agent:   "cursor",
			Status:  "error",
			Message: fmt.Sprintf("Failed to launch agent: %v", err),
		}
	}

	return DelegationResult{
		Agent:   "cursor",
		AgentID: agent.ID,
		Status:  agent.Status,
		Message: fmt.Sprintf("Cursor agent launched for: %s", task),
	}
}

func formatDelegationComment(result DelegationResult) string {
	var sb strings.Builder

	sb.WriteString("## 🤖 AI Agent Delegation\n\n")

	switch result.Status {
	case "error":
		sb.WriteString(fmt.Sprintf("❌ **Error**: %s\n", result.Message))
	case "dry_run":
		sb.WriteString(fmt.Sprintf("🔍 **Dry Run**: %s\n", result.Message))
	default:
		agentName := result.Agent
		if len(agentName) > 0 {
			agentName = strings.ToUpper(agentName[:1]) + agentName[1:]
		}
		sb.WriteString(fmt.Sprintf("✅ **Delegated to %s**\n\n", agentName))
		sb.WriteString(fmt.Sprintf("%s\n\n", result.Message))
		if result.SessionID != "" {
			sb.WriteString(fmt.Sprintf("📋 Session: `%s`\n", result.SessionID))
		}
		if result.AgentID != "" {
			sb.WriteString(fmt.Sprintf("📋 Agent: `%s`\n", result.AgentID))
		}
	}

	sb.WriteString("\n---\n")
	sb.WriteString("<sub>Delegated by Control Center</sub>")

	return sb.String()
}

func runDelegatorList(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	type AgentSession struct {
		Agent  string `json:"agent"`
		ID     string `json:"id"`
		Status string `json:"status"`
		Repo   string `json:"repo,omitempty"`
		Task   string `json:"task,omitempty"`
	}

	var sessions []AgentSession

	// List Jules sessions
	if delegatorAgent == "" || delegatorAgent == "jules" {
		julesKey := os.Getenv("GOOGLE_JULES_API_KEY")
		if julesKey != "" {
			julesClient := jules.NewClient(jules.Config{APIKey: julesKey})
			julesSessions, err := julesClient.ListSessions(ctx)
			if err != nil {
				log.WithError(err).Warn("Failed to list Jules sessions")
			} else {
				for _, s := range julesSessions {
					sessions = append(sessions, AgentSession{
						Agent:  "jules",
						ID:     s.Name,
						Status: s.State,
						Task:   s.Prompt,
					})
				}
			}
		}
	}

	// List Cursor agents
	if delegatorAgent == "" || delegatorAgent == "cursor" {
		cursorKey := os.Getenv("CURSOR_API_KEY")
		if cursorKey != "" {
			cursorClient := cursor.NewClient(cursor.Config{APIKey: cursorKey})
			cursorAgents, err := cursorClient.ListAgents(ctx)
			if err != nil {
				log.WithError(err).Warn("Failed to list Cursor agents")
			} else {
				for _, a := range cursorAgents {
					sessions = append(sessions, AgentSession{
						Agent:  "cursor",
						ID:     a.ID,
						Status: a.Status,
						Repo:   a.Repository,
						Task:   a.Prompt,
					})
				}
			}
		}
	}

	if outputFormat == "json" {
		jsonOut, err := json.Marshal(sessions)
		if err != nil {
			return fmt.Errorf("failed to marshal sessions: %w", err)
		}
		fmt.Println(string(jsonOut))
		return nil
	}

	if len(sessions) == 0 {
		fmt.Println("No active AI agent sessions found")
		return nil
	}

	fmt.Printf("%-10s %-40s %-15s %s\n", "AGENT", "ID", "STATUS", "TASK")
	fmt.Println(strings.Repeat("-", 80))
	for _, s := range sessions {
		task := s.Task
		if len(task) > 30 {
			task = task[:27] + "..."
		}
		fmt.Printf("%-10s %-40s %-15s %s\n", s.Agent, s.ID, s.Status, task)
	}

	return nil
}
