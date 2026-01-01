package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/jbcom/control-center/pkg/clients/jules"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

var (
	julesSessionID string
	julesRepo      string
	julesBranch    string
	julesPrompt    string
	julesMessage   string
	julesFormat    string
	julesFilter    string
)

var julesCmd = &cobra.Command{
	Use:   "jules",
	Short: "Interact with Google Jules AI agent",
	Long: `Jules integration for automated code changes and PR creation.

Jules is Google's AI coding agent that can:
  - Analyze code and create fixes
  - Automatically create pull requests
  - Handle complex multi-file refactoring

The jules command provides full access to session management,
with outputs formatted for GitHub Actions consumption.

Examples:
  # List all sessions
  control-center jules list

  # Create a new session
  control-center jules create --repo owner/name --branch main --prompt "Fix the bug"

  # Get session details (GitHub Actions format)
  control-center jules get --session sessions/123456 --format github

  # Get patch from a session
  control-center jules patch --session sessions/123456

  # Send message to active session
  control-center jules message --session sessions/123456 --message "Create the PR now"

  # Approve a pending plan
  control-center jules approve --session sessions/123456`,
}

var julesListCmd = &cobra.Command{
	Use:   "list",
	Short: "List Jules sessions",
	Long: `List all Jules sessions with optional filtering.

Filters:
  --filter completed  - Show only completed sessions
  --filter in_progress - Show only in-progress sessions
  --filter orphaned   - Show completed sessions without PRs
  --filter with_pr    - Show sessions that created PRs

Output formats:
  --format table  - Human readable table (default)
  --format json   - JSON for programmatic use
  --format github - GitHub Actions output format`,
	RunE: runJulesList,
}

var julesCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new Jules session",
	Long: `Create a new Jules session with AUTO_CREATE_PR enabled.

IMPORTANT: For Jules to work effectively:
  1. AGENTS.md in target repo MUST be current
  2. Prompt MUST be clear and unambiguous
  3. requirePlanApproval is set to false by default`,
	RunE: runJulesCreate,
}

var julesGetCmd = &cobra.Command{
	Use:   "get",
	Short: "Get Jules session details",
	Long: `Get detailed information about a Jules session.

Outputs include:
  - Session state and timestamps
  - PR URL if created
  - Changeset information if available
  - GitHub Actions compatible outputs`,
	RunE: runJulesGet,
}

var julesPatchCmd = &cobra.Command{
	Use:   "patch",
	Short: "Get patch from Jules session",
	Long: `Extract the unified diff patch from a Jules session.

This is useful for applying changes from sessions that
completed without creating a PR (orphaned sessions).

Example:
  control-center jules patch --session sessions/123 | git apply`,
	RunE: runJulesPatch,
}

var julesMessageCmd = &cobra.Command{
	Use:   "message",
	Short: "Send message to Jules session",
	Long: `Send a user message to an active Jules session.

Use this to guide Jules or request specific actions:
  - Ask for PR creation
  - Provide additional context
  - Request specific changes`,
	RunE: runJulesMessage,
}

var julesApproveCmd = &cobra.Command{
	Use:   "approve",
	Short: "Approve pending Jules plan",
	Long:  `Approve a plan for a session in PENDING_PLAN_APPROVAL state.`,
	RunE:  runJulesApprove,
}

func init() {
	rootCmd.AddCommand(julesCmd)

	// Global flags for jules commands
	julesCmd.PersistentFlags().StringVar(&julesFormat, "format", "table", "Output format (table, json, github)")

	// List command
	julesCmd.AddCommand(julesListCmd)
	julesListCmd.Flags().StringVar(&julesFilter, "filter", "", "Filter sessions (completed, in_progress, orphaned, with_pr)")

	// Create command
	julesCmd.AddCommand(julesCreateCmd)
	julesCreateCmd.Flags().StringVar(&julesRepo, "repo", "", "Repository (owner/name)")
	julesCreateCmd.Flags().StringVar(&julesBranch, "branch", "main", "Starting branch")
	julesCreateCmd.Flags().StringVar(&julesPrompt, "prompt", "", "Task prompt for Jules")
	julesCreateCmd.MarkFlagRequired("repo")
	julesCreateCmd.MarkFlagRequired("prompt")

	// Get command
	julesCmd.AddCommand(julesGetCmd)
	julesGetCmd.Flags().StringVar(&julesSessionID, "session", "", "Session name (sessions/123456)")
	julesGetCmd.MarkFlagRequired("session")

	// Patch command
	julesCmd.AddCommand(julesPatchCmd)
	julesPatchCmd.Flags().StringVar(&julesSessionID, "session", "", "Session name (sessions/123456)")
	julesPatchCmd.MarkFlagRequired("session")

	// Message command
	julesCmd.AddCommand(julesMessageCmd)
	julesMessageCmd.Flags().StringVar(&julesSessionID, "session", "", "Session name (sessions/123456)")
	julesMessageCmd.Flags().StringVar(&julesMessage, "message", "", "Message to send")
	julesMessageCmd.MarkFlagRequired("session")
	julesMessageCmd.MarkFlagRequired("message")

	// Approve command
	julesCmd.AddCommand(julesApproveCmd)
	julesApproveCmd.Flags().StringVar(&julesSessionID, "session", "", "Session name (sessions/123456)")
	julesApproveCmd.MarkFlagRequired("session")
}

func getJulesClient() (*jules.Client, error) {
	apiKey := os.Getenv("GOOGLE_JULES_API_KEY")
	if apiKey == "" {
		apiKey = os.Getenv("JULES_API_KEY")
	}
	if apiKey == "" {
		return nil, fmt.Errorf("GOOGLE_JULES_API_KEY or JULES_API_KEY required")
	}

	return jules.NewClient(jules.Config{
		APIKey: apiKey,
	}), nil
}

func runJulesList(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	sessions, err := client.ListFullSessions(ctx)
	if err != nil {
		return fmt.Errorf("failed to list sessions: %w", err)
	}

	// Apply filter
	var filtered []jules.FullSession
	for _, s := range sessions {
		switch julesFilter {
		case "completed":
			if s.State == jules.SessionStateCompleted {
				filtered = append(filtered, s)
			}
		case "in_progress":
			if s.State == jules.SessionStateInProgress {
				filtered = append(filtered, s)
			}
		case "orphaned":
			if s.State == jules.SessionStateCompleted && s.GetPRURL() == "" {
				filtered = append(filtered, s)
			}
		case "with_pr":
			if s.GetPRURL() != "" {
				filtered = append(filtered, s)
			}
		case "":
			filtered = append(filtered, s)
		default:
			return fmt.Errorf("unknown filter: %s", julesFilter)
		}
	}

	// Output based on format
	switch julesFormat {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(filtered)

	case "github":
		// GitHub Actions format - output count and session IDs
		fmt.Printf("session_count=%d\n", len(filtered))
		var ids []string
		for _, s := range filtered {
			ids = append(ids, s.GetSessionID())
		}
		fmt.Printf("session_ids=%s\n", strings.Join(ids, ","))
		return nil

	default: // table
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "STATE\tSESSION ID\tPR URL\tTITLE")
		fmt.Fprintln(w, "-----\t----------\t------\t-----")
		for _, s := range filtered {
			title := s.Title
			if len(title) > 50 {
				title = title[:47] + "..."
			}
			prURL := s.GetPRURL()
			if prURL == "" {
				prURL = "-"
			}
			fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", s.State, s.GetSessionID(), prURL, title)
		}
		return w.Flush()
	}
}

func runJulesCreate(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	log.WithFields(log.Fields{
		"repo":   julesRepo,
		"branch": julesBranch,
	}).Info("Creating Jules session")

	session, err := client.CreateSession(ctx, julesRepo, julesBranch, julesPrompt)
	if err != nil {
		return fmt.Errorf("failed to create session: %w", err)
	}

	// Output based on format
	switch julesFormat {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(session)

	case "github":
		fmt.Printf("session_id=%s\n", session.GetSessionID())
		fmt.Printf("session_name=%s\n", session.Name)
		fmt.Printf("session_url=%s\n", session.GetJulesURL())
		fmt.Printf("state=%s\n", session.State)
		return nil

	default:
		fmt.Printf("✅ Jules session created!\n\n")
		fmt.Printf("Session ID: %s\n", session.GetSessionID())
		fmt.Printf("Monitor at: %s\n", session.GetJulesURL())
		fmt.Printf("State: %s\n", session.State)
		return nil
	}
}

func runJulesGet(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	// Normalize session name
	sessionName := julesSessionID
	if !strings.HasPrefix(sessionName, "sessions/") {
		sessionName = "sessions/" + sessionName
	}

	output, err := client.ToGitHubActionsOutput(ctx, sessionName)
	if err != nil {
		return fmt.Errorf("failed to get session: %w", err)
	}

	// Output based on format
	switch julesFormat {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(output)

	case "github":
		output.PrintGitHubEnvOutputs()
		return nil

	default:
		fmt.Printf("Session: %s\n", output.SessionID)
		fmt.Printf("URL: %s\n", output.SessionURL)
		fmt.Printf("State: %s\n", output.State)
		fmt.Printf("Has PR: %t\n", output.HasPR)
		if output.PRURL != "" {
			fmt.Printf("PR URL: %s\n", output.PRURL)
		}
		fmt.Printf("Has Changeset: %t\n", output.HasChangeSet)
		if output.TargetRepo != "" {
			fmt.Printf("Target Repo: %s\n", output.TargetRepo)
		}
		if output.TargetBranch != "" {
			fmt.Printf("Target Branch: %s\n", output.TargetBranch)
		}
		if output.BaseCommit != "" {
			fmt.Printf("Base Commit: %s\n", output.BaseCommit)
		}
		if output.CommitMessage != "" {
			fmt.Printf("\nSuggested Commit Message:\n%s\n", output.CommitMessage)
		}
		return nil
	}
}

func runJulesPatch(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	// Normalize session name
	sessionName := julesSessionID
	if !strings.HasPrefix(sessionName, "sessions/") {
		sessionName = "sessions/" + sessionName
	}

	changeSet, err := client.GetLatestChangeSet(ctx, sessionName)
	if err != nil {
		return fmt.Errorf("failed to get changeset: %w", err)
	}

	// Output based on format
	switch julesFormat {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(changeSet)

	case "github":
		// For GitHub Actions, base64 encode the patch to handle multiline
		fmt.Printf("has_patch=true\n")
		fmt.Printf("base_commit=%s\n", changeSet.GitPatch.BaseCommitID)
		// Patch is output to stderr to avoid mixing with outputs
		fmt.Fprintln(os.Stderr, changeSet.GitPatch.UnidiffPatch)
		return nil

	default:
		// Output raw patch for piping to git apply
		fmt.Print(changeSet.GitPatch.UnidiffPatch)
		return nil
	}
}

func runJulesMessage(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	// Normalize session name
	sessionName := julesSessionID
	if !strings.HasPrefix(sessionName, "sessions/") {
		sessionName = "sessions/" + sessionName
	}

	if err := client.SendMessage(ctx, sessionName, julesMessage); err != nil {
		return fmt.Errorf("failed to send message: %w", err)
	}

	switch julesFormat {
	case "github":
		fmt.Printf("message_sent=true\n")
		fmt.Printf("session_id=%s\n", strings.TrimPrefix(sessionName, "sessions/"))
		return nil
	default:
		fmt.Printf("✅ Message sent to session %s\n", sessionName)
		return nil
	}
}

func runJulesApprove(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	client, err := getJulesClient()
	if err != nil {
		return err
	}

	// Normalize session name
	sessionName := julesSessionID
	if !strings.HasPrefix(sessionName, "sessions/") {
		sessionName = "sessions/" + sessionName
	}

	if err := client.ApprovePlan(ctx, sessionName); err != nil {
		return fmt.Errorf("failed to approve plan: %w", err)
	}

	switch julesFormat {
	case "github":
		fmt.Printf("plan_approved=true\n")
		fmt.Printf("session_id=%s\n", strings.TrimPrefix(sessionName, "sessions/"))
		return nil
	default:
		fmt.Printf("✅ Plan approved for session %s\n", sessionName)
		return nil
	}
}
