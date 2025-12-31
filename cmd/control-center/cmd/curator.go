package cmd

import (
	"context"
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
	Short: "Nightly triage of issues and PRs",
	Long: `The Curator triages open issues and PRs, routing them to appropriate agents.

It uses Ollama to analyze and route:
  - Simple issues → Ollama (inline fix)
  - Multi-file refactors → Jules
  - Complex debugging → Cursor Cloud Agent
  - Ambiguous/sensitive → Human review

Examples:
  # Curate a specific repository
  control-center curator --repo jbcom/control-center

  # Dry run
  control-center curator --repo jbcom/control-center --dry-run`,
	RunE: runCurator,
}

func init() {
	rootCmd.AddCommand(curatorCmd)

	curatorCmd.Flags().StringVar(&curatorRepo, "repo", "", "repository (owner/name)")
	curatorCmd.MarkFlagRequired("repo")

	viper.BindPFlag("curator.repo", curatorCmd.Flags().Lookup("repo"))
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
