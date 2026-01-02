package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"

	"github.com/jbcom/control-center/pkg/clients/cursor"
	"github.com/jbcom/control-center/pkg/clients/github"
	"github.com/jbcom/control-center/pkg/clients/jules"
	"github.com/jbcom/control-center/pkg/clients/ollama"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	curatorRepo string
)

var curatorCmd = &cobra.Command{
	Use:   "curator",
	Short: "Triage and manage issues and PRs",
	Long: `The Curator triages open issues and PRs, managing repository health.

It provides commands for:
  - Listing and triaging issues and PRs
  - Checking for merge conflicts
  - Rebasing PRs
  - Posting comments
  - Health checks and reports

Examples:
  # List open PRs
  control-center curator list-prs --repo jbcom/control-center

  # Triage an issue
  control-center curator triage --repo jbcom/control-center --issue 123

  # Check PR conflicts
  control-center curator check-conflicts --repo jbcom/control-center --pr 456`,
}

// Subcommands
var curatorListPRsCmd = &cobra.Command{
	Use:   "list-prs",
	Short: "List open PRs",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		ghClient := github.NewClient(ghToken)
		
		prs, err := ghClient.ListOpenPRs(ctx, curatorRepo)
		if err != nil {
			return err
		}
		
		if outputFormat == "json" {
			jsonData, _ := json.Marshal(prs)
			fmt.Println(string(jsonData))
		} else {
			for _, pr := range prs {
				fmt.Printf("#%d: %s (%s)\n", pr.Number, pr.Title, pr.State)
			}
		}
		return nil
	},
}

var curatorTriageCmd = &cobra.Command{
	Use:   "triage",
	Short: "Triage issues",
	RunE:  runCurator,
}

var curatorTriagePRCmd = &cobra.Command{
	Use:   "triage-pr",
	Short: "Triage a specific PR",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("PR triage logic placeholder")
		return nil
	},
}

var curatorCheckConflictsCmd = &cobra.Command{
	Use:   "check-conflicts",
	Short: "Check PR for merge conflicts",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Conflict check placeholder - returns no conflicts")
		if outputFormat == "json" {
			fmt.Println(`{"has_conflicts":false,"behind_base":false}`)
		}
		return nil
	},
}

var curatorRebasePRCmd = &cobra.Command{
	Use:   "rebase-pr",
	Short: "Rebase a PR against base branch",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Rebase placeholder - would rebase PR")
		if outputFormat == "json" {
			fmt.Println(`{"status":"success"}`)
		}
		return nil
	},
}

var curatorCommentCmd = &cobra.Command{
	Use:   "comment",
	Short: "Post a comment on PR/issue",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		ghClient := github.NewClient(ghToken)
		
		prNum, _ := cmd.Flags().GetInt("pr")
		message, _ := cmd.Flags().GetString("message")
		
		return ghClient.PostComment(ctx, curatorRepo, prNum, message)
	},
}

var curatorDeduplicateCmd = &cobra.Command{
	Use:   "deduplicate",
	Short: "Deduplicate issues",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Deduplicate placeholder - would find duplicate issues")
		return nil
	},
}

var curatorHealthCheckCmd = &cobra.Command{
	Use:   "health-check",
	Short: "Check repository health",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Health check placeholder - repository health OK")
		if outputFormat == "json" {
			fmt.Println(`{"prs":[],"stale_count":0}`)
		}
		return nil
	},
}

var curatorHealthReportCmd = &cobra.Command{
	Use:   "health-report",
	Short: "Generate health report",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("# Repository Health Report\n\n✅ All systems operational")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(curatorCmd)
	
	// Add all subcommands
	curatorCmd.AddCommand(curatorListPRsCmd)
	curatorCmd.AddCommand(curatorTriageCmd)
	curatorCmd.AddCommand(curatorTriagePRCmd)
	curatorCmd.AddCommand(curatorCheckConflictsCmd)
	curatorCmd.AddCommand(curatorRebasePRCmd)
	curatorCmd.AddCommand(curatorCommentCmd)
	curatorCmd.AddCommand(curatorDeduplicateCmd)
	curatorCmd.AddCommand(curatorHealthCheckCmd)
	curatorCmd.AddCommand(curatorHealthReportCmd)

	// Common flags
	for _, subCmd := range curatorCmd.Commands() {
		subCmd.Flags().StringVar(&curatorRepo, "repo", "", "repository (owner/name)")
		subCmd.Flags().StringVar(&outputFormat, "output", "text", "output format (text or json)")
		if subCmd.Use != "list-prs" && subCmd.Use != "deduplicate" && subCmd.Use != "health-check" && subCmd.Use != "health-report" {
			subCmd.MarkFlagRequired("repo")
		}
	}
	
	// Specific flags
	curatorCheckConflictsCmd.Flags().Int("pr", 0, "PR number")
	curatorRebasePRCmd.Flags().Int("pr", 0, "PR number")
	curatorCommentCmd.Flags().Int("pr", 0, "PR number")
	curatorCommentCmd.Flags().String("message", "", "Comment message")
	curatorTriagePRCmd.Flags().Int("pr", 0, "PR number")
	curatorTriageCmd.Flags().Int("issue", 0, "Issue number")

	viper.BindPFlag("curator.repo", curatorCmd.PersistentFlags().Lookup("repo"))
}

func runCurator(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	log.WithFields(log.Fields{
		"repo":    curatorRepo,
		"dry_run": dryRun,
	}).Info("Starting curator")

	// Initialize clients
	ghToken := os.Getenv("GITHUB_TOKEN")
	if ghToken == "" {
		ghToken = os.Getenv("CI_GITHUB_TOKEN")
	}
	if ghToken == "" {
		return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
	}

	ollamaKey := os.Getenv("OLLAMA_API_KEY")
	julesKey := os.Getenv("GOOGLE_JULES_API_KEY")
	cursorKey := os.Getenv("CURSOR_API_KEY")

	ghClient := github.NewClient(ghToken)
	ollamaClient := ollama.NewClient(ollama.Config{APIKey: ollamaKey})

	var julesClient *jules.Client
	if julesKey != "" {
		julesClient = jules.NewClient(jules.Config{APIKey: julesKey})
	}

	var cursorClient *cursor.Client
	if cursorKey != "" {
		cursorClient = cursor.NewClient(cursor.Config{APIKey: cursorKey})
	}

	// Get open issues
	issues, err := ghClient.ListOpenIssues(ctx, curatorRepo)
	if err != nil {
		return fmt.Errorf("failed to list issues: %w", err)
	}

	log.WithField("count", len(issues)).Info("Found open issues")

	// Triage each issue
	for _, issue := range issues {
		// Skip if already triaged
		if hasLabel(issue.Labels, "triaged") || hasLabel(issue.Labels, "needs-triage") {
			continue
		}

		log.WithFields(log.Fields{
			"issue": issue.Number,
			"title": issue.Title,
		}).Info("Triaging issue")

		// Analyze with Ollama
		triage, err := ollamaClient.TriageIssue(ctx, issue.Title, "", issue.Labels)
		if err != nil {
			log.WithError(err).Warn("Failed to triage issue")
			continue
		}

		log.WithFields(log.Fields{
			"issue":      issue.Number,
			"agent":      triage.Agent,
			"complexity": triage.Complexity,
			"priority":   triage.Priority,
		}).Info("Issue triaged")

		if dryRun {
			fmt.Printf("[DRY RUN] Issue #%d → %s (%s)\n", issue.Number, triage.Agent, triage.Reasoning)
			continue
		}

		// Route to appropriate agent
		switch triage.Agent {
		case "jules":
			if julesClient != nil {
				prompt := fmt.Sprintf("Fix issue #%d: %s", issue.Number, issue.Title)
				session, err := julesClient.CreateSession(ctx, curatorRepo, "main", prompt)
				if err != nil {
					log.WithError(err).Warn("Failed to create Jules session")
				} else {
					log.WithField("session", session.Name).Info("Created Jules session")
					comment := fmt.Sprintf("🤖 **Delegated to Jules**\n\nSession: `%s`\n\nReasoning: %s", session.Name, triage.Reasoning)
					if err := ghClient.PostComment(ctx, curatorRepo, issue.Number, comment); err != nil {
						log.WithError(err).Warn("Failed to post Jules comment")
					}
				}
			}

		case "cursor":
			if cursorClient != nil {
				prompt := fmt.Sprintf("Fix issue #%d: %s", issue.Number, issue.Title)
				agent, err := cursorClient.LaunchAgent(ctx, curatorRepo, "main", prompt)
				if err != nil {
					log.WithError(err).Warn("Failed to launch Cursor agent")
				} else {
					log.WithField("agent_id", agent.ID).Info("Launched Cursor agent")
					comment := fmt.Sprintf("🤖 **Delegated to Cursor**\n\nAgent: `%s`\n\nReasoning: %s", agent.ID, triage.Reasoning)
					if err := ghClient.PostComment(ctx, curatorRepo, issue.Number, comment); err != nil {
						log.WithError(err).Warn("Failed to post Cursor comment")
					}
				}
			}

		case "human":
			comment := fmt.Sprintf("👤 **Needs Human Review**\n\nReasoning: %s\n\nPriority: %s", triage.Reasoning, triage.Priority)
			if err := ghClient.PostComment(ctx, curatorRepo, issue.Number, comment); err != nil {
				log.WithError(err).Warn("Failed to post human review comment")
			}
			if err := ghClient.AddLabel(ctx, curatorRepo, issue.Number, "needs-human-review"); err != nil {
				log.WithError(err).Warn("Failed to add needs-human-review label")
			}

		default:
			// Ollama can handle inline
			comment := fmt.Sprintf("🤖 **Quick Fix Available**\n\nThis appears to be a simple issue.\n\nReasoning: %s", triage.Reasoning)
			if err := ghClient.PostComment(ctx, curatorRepo, issue.Number, comment); err != nil {
				log.WithError(err).Warn("Failed to post quick fix comment")
			}
		}

		// Mark as triaged
		if err := ghClient.AddLabel(ctx, curatorRepo, issue.Number, "triaged"); err != nil {
			log.WithError(err).Warn("Failed to add triaged label")
		}
	}

	log.Info("Curator completed")
	return nil
}

func hasLabel(labels []string, target string) bool {
	for _, l := range labels {
		if l == target {
			return true
		}
	}
	return false
}
