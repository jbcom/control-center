package cmd

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/jbcom/control-center/pkg/clients/github"
	"github.com/jbcom/control-center/pkg/clients/ollama"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	reviewerRepo string
	reviewerPR   int
)

var reviewerCmd = &cobra.Command{
	Use:   "reviewer",
	Short: "AI-powered code review coordinator",
	Long: `The Reviewer provides AI-powered code review using Ollama GLM 4.6.

It analyzes PR diffs and provides structured feedback on:
  - Security vulnerabilities
  - Performance issues
  - Bug risks
  - Code style and maintainability

Examples:
  # Review a specific PR
  control-center reviewer --repo jbcom/control-center --pr 123

  # Review with debug output
  control-center reviewer --repo jbcom/control-center --pr 123 --log-level debug`,
	RunE: runReviewer,
}

func init() {
	rootCmd.AddCommand(reviewerCmd)

	reviewerCmd.Flags().StringVar(&reviewerRepo, "repo", "", "repository (owner/name)")
	reviewerCmd.Flags().IntVar(&reviewerPR, "pr", 0, "pull request number")

	reviewerCmd.MarkFlagRequired("repo")
	reviewerCmd.MarkFlagRequired("pr")

	viper.BindPFlag("reviewer.repo", reviewerCmd.Flags().Lookup("repo"))
	viper.BindPFlag("reviewer.pr", reviewerCmd.Flags().Lookup("pr"))
}

func runReviewer(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	log.WithFields(log.Fields{
		"repo":    reviewerRepo,
		"pr":      reviewerPR,
		"dry_run": dryRun,
	}).Info("Starting reviewer")

	// Initialize clients
	ghToken := os.Getenv("GITHUB_TOKEN")
	if ghToken == "" {
		ghToken = os.Getenv("CI_GITHUB_TOKEN")
	}
	if ghToken == "" {
		return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
	}

	ollamaKey := os.Getenv("OLLAMA_API_KEY")

	ghClient := github.NewClient(ghToken)
	ollamaClient := ollama.NewClient(ollama.Config{
		APIKey: ollamaKey,
	})

	// Get PR diff
	diff, err := getPRDiff(ctx, reviewerRepo, reviewerPR, ghToken)
	if err != nil {
		return fmt.Errorf("failed to get PR diff: %w", err)
	}

	log.WithField("diff_size", len(diff)).Debug("Got PR diff")

	// Review with Ollama
	review, err := ollamaClient.ReviewCode(ctx, diff)
	if err != nil {
		return fmt.Errorf("failed to review code: %w", err)
	}

	// Format review comment
	comment := formatReviewComment(review)

	log.WithFields(log.Fields{
		"issues":   len(review.Issues),
		"approval": review.Approval,
	}).Info("Review completed")

	if dryRun {
		fmt.Println("=== Review Comment (Dry Run) ===")
		fmt.Println(comment)
		return nil
	}

	// Post review comment
	if err := ghClient.PostComment(ctx, reviewerRepo, reviewerPR, comment); err != nil {
		return fmt.Errorf("failed to post comment: %w", err)
	}

	log.Info("Review posted successfully")
	return nil
}

func getPRDiff(ctx context.Context, repo string, pr int, token string) (string, error) {
	// Use gh CLI to get diff
	cmd := exec.CommandContext(ctx, "gh", "pr", "diff", fmt.Sprintf("%d", pr), "--repo", repo)
	cmd.Env = append(os.Environ(), fmt.Sprintf("GH_TOKEN=%s", token))

	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("gh pr diff failed: %w", err)
	}

	return string(out), nil
}

func formatReviewComment(review *ollama.CodeReview) string {
	var sb strings.Builder

	sb.WriteString("## 🤖 AI Code Review\n\n")
	sb.WriteString("### Summary\n")
	sb.WriteString(review.Summary)
	sb.WriteString("\n\n")

	if len(review.Issues) > 0 {
		sb.WriteString("### Issues Found\n")
		for _, issue := range review.Issues {
			emoji := severityEmoji(issue.Severity)
			sb.WriteString(fmt.Sprintf("%s **%s**: %s\n", emoji, issue.Category, issue.Message))
			if issue.Suggestion != "" {
				sb.WriteString(fmt.Sprintf("  - 💡 %s\n", issue.Suggestion))
			}
			sb.WriteString("\n")
		}
	} else {
		sb.WriteString("### ✅ No Issues Found\n\n")
	}

	if review.Comments != "" {
		sb.WriteString("### Additional Comments\n")
		sb.WriteString(review.Comments)
		sb.WriteString("\n\n")
	}

	sb.WriteString("---\n")
	sb.WriteString("<sub>Reviewed by Control Center using Ollama GLM 4.6</sub>")

	return sb.String()
}

func severityEmoji(severity string) string {
	switch severity {
	case "critical":
		return "🔴"
	case "high":
		return "🟠"
	case "medium":
		return "🟡"
	case "low":
		return "🟢"
	default:
		return "⚪"
	}
}
