package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

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
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		prNum, _ := cmd.Flags().GetInt("pr")
		if prNum == 0 {
			return fmt.Errorf("--pr flag is required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Get PR details using gh CLI
		out, err := ghClient.RunGH(ctx, "pr", "view", fmt.Sprintf("%d", prNum),
			"--repo", curatorRepo, "--json", "title,body,state,labels")
		if err != nil {
			return fmt.Errorf("failed to get PR details: %w", err)
		}
		
		var prData struct {
			Title  string   `json:"title"`
			Body   string   `json:"body"`
			State  string   `json:"state"`
			Labels []string `json:"labels"`
		}
		if err := json.Unmarshal([]byte(out), &prData); err != nil {
			return fmt.Errorf("failed to parse PR data: %w", err)
		}
		
		log.WithFields(log.Fields{
			"pr":    prNum,
			"title": prData.Title,
			"state": prData.State,
		}).Info("PR triaged")
		
		if outputFormat == "json" {
			jsonData, _ := json.Marshal(map[string]interface{}{
				"pr":     prNum,
				"title":  prData.Title,
				"state":  prData.State,
				"labels": prData.Labels,
			})
			fmt.Println(string(jsonData))
		} else {
			fmt.Printf("PR #%d: %s\nState: %s\nLabels: %v\n", 
				prNum, prData.Title, prData.State, prData.Labels)
		}
		
		return nil
	},
}

var curatorCheckConflictsCmd = &cobra.Command{
	Use:   "check-conflicts",
	Short: "Check PR for merge conflicts",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		prNum, _ := cmd.Flags().GetInt("pr")
		if prNum == 0 {
			return fmt.Errorf("--pr flag is required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Get PR mergeable state
		out, err := ghClient.RunGH(ctx, "pr", "view", fmt.Sprintf("%d", prNum),
			"--repo", curatorRepo, "--json", "mergeable,mergeStateStatus,baseRefName,headRefName")
		if err != nil {
			return fmt.Errorf("failed to get PR status: %w", err)
		}
		
		var prStatus struct {
			Mergeable        string `json:"mergeable"`
			MergeStateStatus string `json:"mergeStateStatus"`
			BaseRefName      string `json:"baseRefName"`
			HeadRefName      string `json:"headRefName"`
		}
		if err := json.Unmarshal([]byte(out), &prStatus); err != nil {
			return fmt.Errorf("failed to parse PR status: %w", err)
		}
		
		hasConflicts := prStatus.Mergeable == "CONFLICTING"
		behindBase := prStatus.MergeStateStatus == "BEHIND"
		
		log.WithFields(log.Fields{
			"pr":            prNum,
			"mergeable":     prStatus.Mergeable,
			"merge_status":  prStatus.MergeStateStatus,
			"has_conflicts": hasConflicts,
			"behind_base":   behindBase,
		}).Info("Checked PR conflicts")
		
		if outputFormat == "json" {
			result := map[string]interface{}{
				"has_conflicts": hasConflicts,
				"behind_base":   behindBase,
				"mergeable":     prStatus.Mergeable,
				"merge_status":  prStatus.MergeStateStatus,
				"base_ref":      prStatus.BaseRefName,
				"head_ref":      prStatus.HeadRefName,
			}
			jsonData, _ := json.Marshal(result)
			fmt.Println(string(jsonData))
		} else {
			if hasConflicts {
				fmt.Printf("❌ PR #%d has merge conflicts\n", prNum)
			} else if behindBase {
				fmt.Printf("⚠️  PR #%d is behind base branch\n", prNum)
			} else {
				fmt.Printf("✅ PR #%d has no conflicts\n", prNum)
			}
		}
		
		return nil
	},
}

var curatorRebasePRCmd = &cobra.Command{
	Use:   "rebase-pr",
	Short: "Rebase a PR against base branch",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		prNum, _ := cmd.Flags().GetInt("pr")
		if prNum == 0 {
			return fmt.Errorf("--pr flag is required")
		}
		
		autoResolve, _ := cmd.Flags().GetBool("auto-resolve")
		
		ghClient := github.NewClient(ghToken)
		
		// Update branch (equivalent to rebase in GitHub UI)
		// Use gh pr merge --rebase would actually merge, so we comment suggesting update
		comment := fmt.Sprintf("🔄 Rebase requested for PR #%d\n\n", prNum)
		comment += "To rebase this PR, please:\n"
		comment += "1. Fetch latest changes: `git fetch origin`\n"
		comment += "2. Rebase: `git rebase origin/main`\n"
		comment += "3. Force push: `git push --force-with-lease`\n"
		
		if autoResolve {
			comment += "\n⚠️  Auto-resolve conflicts requested but requires manual intervention.\n"
		}
		
		if err := ghClient.PostComment(ctx, curatorRepo, prNum, comment); err != nil {
			return fmt.Errorf("failed to post rebase instructions: %w", err)
		}
		
		log.WithField("pr", prNum).Info("Rebase instructions posted")
		
		if outputFormat == "json" {
			result := map[string]interface{}{
				"status":       "instructions_posted",
				"pr":           prNum,
				"auto_resolve": autoResolve,
			}
			jsonData, _ := json.Marshal(result)
			fmt.Println(string(jsonData))
		} else {
			fmt.Printf("✅ Rebase instructions posted to PR #%d\n", prNum)
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
	Short: "Find and report duplicate issues",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Get all open issues
		issues, err := ghClient.ListOpenIssues(ctx, curatorRepo)
		if err != nil {
			return fmt.Errorf("failed to list issues: %w", err)
		}
		
		// Find potential duplicates by title similarity
		type duplicate struct {
			issue1 github.Issue
			issue2 github.Issue
			similarity float64
		}
		
		var duplicates []duplicate
		for i := 0; i < len(issues); i++ {
			for j := i + 1; j < len(issues); j++ {
				// Simple similarity check: count common words
				title1 := strings.ToLower(issues[i].Title)
				title2 := strings.ToLower(issues[j].Title)
				
				words1 := strings.Fields(title1)
				words2 := strings.Fields(title2)
				
				common := 0
				for _, w1 := range words1 {
					for _, w2 := range words2 {
						if w1 == w2 && len(w1) > 3 { // Only count words > 3 chars
							common++
							break
						}
					}
				}
				
				if common > 0 {
					similarity := float64(common) / float64(len(words1)+len(words2)-common)
					if similarity > 0.5 { // 50% similarity threshold
						duplicates = append(duplicates, duplicate{
							issue1:     issues[i],
							issue2:     issues[j],
							similarity: similarity,
						})
					}
				}
			}
		}
		
		log.WithFields(log.Fields{
			"total_issues": len(issues),
			"duplicates":   len(duplicates),
		}).Info("Deduplication complete")
		
		if outputFormat == "json" {
			result := map[string]interface{}{
				"total_issues":      len(issues),
				"potential_duplicates": len(duplicates),
				"duplicates":        duplicates,
			}
			jsonData, _ := json.Marshal(result)
			fmt.Println(string(jsonData))
		} else {
			fmt.Printf("Analyzed %d issues\n", len(issues))
			fmt.Printf("Found %d potential duplicate pairs:\n\n", len(duplicates))
			for _, dup := range duplicates {
				fmt.Printf("  #%d: %s\n", dup.issue1.Number, dup.issue1.Title)
				fmt.Printf("  #%d: %s\n", dup.issue2.Number, dup.issue2.Title)
				fmt.Printf("  Similarity: %.0f%%\n\n", dup.similarity*100)
			}
		}
		
		return nil
	},
}

var curatorHealthCheckCmd = &cobra.Command{
	Use:   "health-check",
	Short: "Check repository health",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Check PRs
		prs, err := ghClient.ListOpenPRs(ctx, curatorRepo)
		if err != nil {
			return fmt.Errorf("failed to list PRs: %w", err)
		}
		
		// Check for stale PRs (>30 days old)
		staleThreshold := time.Now().AddDate(0, 0, -30)
		var stalePRs []github.PullRequest
		var draftPRs []github.PullRequest
		
		for _, pr := range prs {
			if pr.UpdatedAt.Before(staleThreshold) {
				stalePRs = append(stalePRs, pr)
			}
			if pr.Draft {
				draftPRs = append(draftPRs, pr)
			}
		}
		
		// Check issues
		issues, err := ghClient.ListOpenIssues(ctx, curatorRepo)
		if err != nil {
			return fmt.Errorf("failed to list issues: %w", err)
		}
		
		log.WithFields(log.Fields{
			"total_prs":   len(prs),
			"stale_prs":   len(stalePRs),
			"draft_prs":   len(draftPRs),
			"open_issues": len(issues),
		}).Info("Health check complete")
		
		if outputFormat == "json" {
			result := map[string]interface{}{
				"status":      "healthy",
				"total_prs":   len(prs),
				"stale_prs":   len(stalePRs),
				"draft_prs":   len(draftPRs),
				"open_issues": len(issues),
				"stale_threshold_days": 30,
			}
			jsonData, _ := json.Marshal(result)
			fmt.Println(string(jsonData))
		} else {
			fmt.Printf("Repository Health Check\n")
			fmt.Printf("=======================\n\n")
			fmt.Printf("Open PRs: %d\n", len(prs))
			fmt.Printf("  - Stale (>30 days): %d\n", len(stalePRs))
			fmt.Printf("  - Draft: %d\n", len(draftPRs))
			fmt.Printf("Open Issues: %d\n\n", len(issues))
			
			if len(stalePRs) > 0 {
				fmt.Printf("⚠️  Stale PRs need attention:\n")
				for _, pr := range stalePRs {
					fmt.Printf("  #%d: %s (updated %s)\n", pr.Number, pr.Title, pr.UpdatedAt.Format("2006-01-02"))
				}
			} else {
				fmt.Printf("✅ No stale PRs\n")
			}
		}
		
		return nil
	},
}

var curatorHealthReportCmd = &cobra.Command{
	Use:   "health-report",
	Short: "Generate detailed health report",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Gather metrics
		prs, err := ghClient.ListOpenPRs(ctx, curatorRepo)
		if err != nil {
			return fmt.Errorf("failed to list PRs: %w", err)
		}
		
		issues, err := ghClient.ListOpenIssues(ctx, curatorRepo)
		if err != nil {
			return fmt.Errorf("failed to list issues: %w", err)
		}
		
		// Calculate stats
		staleThreshold := time.Now().AddDate(0, 0, -30)
		var stalePRs, draftPRs int
		for _, pr := range prs {
			if pr.UpdatedAt.Before(staleThreshold) {
				stalePRs++
			}
			if pr.Draft {
				draftPRs++
			}
		}
		
		// Generate report
		report := "# Repository Health Report\n"
		report += fmt.Sprintf("**Repository:** %s\n", curatorRepo)
		report += fmt.Sprintf("**Generated:** %s\n\n", time.Now().Format("2006-01-02 15:04:05"))
		report += "## Summary\n\n"
		report += "| Metric | Count |\n"
		report += "|--------|-------|\n"
		report += fmt.Sprintf("| Open PRs | %d |\n", len(prs))
		report += fmt.Sprintf("| Stale PRs (>30d) | %d |\n", stalePRs)
		report += fmt.Sprintf("| Draft PRs | %d |\n", draftPRs)
		report += fmt.Sprintf("| Open Issues | %d |\n\n", len(issues))

		healthScore := 100.0
		if len(prs) > 0 {
			healthScore -= float64(stalePRs) / float64(len(prs)) * 30
		}

		report += "## Health Score\n\n"
		report += fmt.Sprintf("**%.0f/100**\n\n", healthScore)
		
		if healthScore >= 90 {
			report += "✅ Excellent health\n"
		} else if healthScore >= 70 {
			report += "⚠️  Good health, minor issues\n"
		} else {
			report += "❌ Needs attention\n"
		}
		
		fmt.Println(report)
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
	curatorRebasePRCmd.Flags().Bool("auto-resolve", false, "Attempt to auto-resolve conflicts")
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
