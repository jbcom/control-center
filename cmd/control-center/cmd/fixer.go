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
	fixerRepo   string
	fixerPR     int
	fixerRunID  int64
)

var fixerCmd = &cobra.Command{
	Use:   "fixer",
	Short: "Automated CI failure resolution",
	Long: `The Fixer analyzes CI failures and suggests or applies fixes.

It uses Ollama to analyze failure logs and provide:
  - Root cause analysis
  - Specific fix suggestions
  - Verification commands

Examples:
  # Analyze and suggest fix for a PR
  control-center fixer --repo jbcom/control-center --pr 123

  # Analyze a specific workflow run
  control-center fixer --repo jbcom/control-center --run-id 12345678

  # Dry run
  control-center fixer --repo jbcom/control-center --pr 123 --dry-run`,
	RunE: runFixer,
}

func init() {
	rootCmd.AddCommand(fixerCmd)

	fixerCmd.Flags().StringVar(&fixerRepo, "repo", "", "repository (owner/name)")
	fixerCmd.Flags().IntVar(&fixerPR, "pr", 0, "pull request number")
	fixerCmd.Flags().Int64Var(&fixerRunID, "run-id", 0, "workflow run ID")

	fixerCmd.MarkFlagRequired("repo")

	viper.BindPFlag("fixer.repo", fixerCmd.Flags().Lookup("repo"))
	viper.BindPFlag("fixer.pr", fixerCmd.Flags().Lookup("pr"))
	viper.BindPFlag("fixer.run_id", fixerCmd.Flags().Lookup("run-id"))
}

func runFixer(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	log.WithFields(log.Fields{
		"repo":    fixerRepo,
		"pr":      fixerPR,
		"run_id":  fixerRunID,
		"dry_run": dryRun,
	}).Info("Starting fixer")

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

	// Get failure log
	var failureLog string
	var err error

	if fixerRunID > 0 {
		failureLog, err = getRunLog(ctx, fixerRepo, fixerRunID, ghToken)
	} else if fixerPR > 0 {
		failureLog, err = getPRFailureLog(ctx, fixerRepo, fixerPR, ghToken)
	} else {
		return fmt.Errorf("either --pr or --run-id is required")
	}

	if err != nil {
		return fmt.Errorf("failed to get failure log: %w", err)
	}

	if failureLog == "" {
		log.Info("No failures found")
		return nil
	}

	log.WithField("log_size", len(failureLog)).Debug("Got failure log")

	// Analyze with Ollama
	analysis, err := ollamaClient.AnalyzeFailure(ctx, failureLog)
	if err != nil {
		return fmt.Errorf("failed to analyze failure: %w", err)
	}

	// Format fix suggestion
	suggestion := formatFixSuggestion(analysis)

	log.WithField("confidence", analysis.Confidence).Info("Analysis completed")

	if dryRun {
		fmt.Println("=== Fix Suggestion (Dry Run) ===")
		fmt.Println(suggestion)
		return nil
	}

	// Post suggestion to PR
	if fixerPR > 0 {
		if err := ghClient.PostComment(ctx, fixerRepo, fixerPR, suggestion); err != nil {
			return fmt.Errorf("failed to post comment: %w", err)
		}
		log.Info("Fix suggestion posted successfully")
	} else {
		fmt.Println(suggestion)
	}

	return nil
}

func getRunLog(ctx context.Context, repo string, runID int64, token string) (string, error) {
	cmd := exec.CommandContext(ctx, "gh", "run", "view", fmt.Sprintf("%d", runID),
		"--repo", repo, "--log-failed")
	cmd.Env = append(os.Environ(), fmt.Sprintf("GH_TOKEN=%s", token))

	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("gh run view failed: %w", err)
	}

	return string(out), nil
}

func getPRFailureLog(ctx context.Context, repo string, pr int, token string) (string, error) {
	// Get the checks for the PR and find failed ones
	cmd := exec.CommandContext(ctx, "gh", "pr", "checks", fmt.Sprintf("%d", pr),
		"--repo", repo, "--json", "name,state,link")
	cmd.Env = append(os.Environ(), fmt.Sprintf("GH_TOKEN=%s", token))

	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("gh pr checks failed: %w", err)
	}

	// For now, return the raw output. In production, would parse and get specific run logs.
	return string(out), nil
}

func formatFixSuggestion(analysis *ollama.FailureAnalysis) string {
	var sb strings.Builder

	sb.WriteString("## 🔧 CI Fix Suggestion\n\n")

	sb.WriteString("### Root Cause\n")
	sb.WriteString(analysis.RootCause)
	sb.WriteString("\n\n")

	sb.WriteString("### Suggested Fix\n")
	sb.WriteString(analysis.FixSuggestion)
	sb.WriteString("\n\n")

	if len(analysis.VerificationCommands) > 0 {
		sb.WriteString("### Verification Commands\n")
		sb.WriteString("```bash\n")
		for _, cmd := range analysis.VerificationCommands {
			sb.WriteString(cmd)
			sb.WriteString("\n")
		}
		sb.WriteString("```\n\n")
	}

	sb.WriteString(fmt.Sprintf("**Confidence**: %s\n\n", analysis.Confidence))

	sb.WriteString("---\n")
	sb.WriteString("<sub>🤖 Generated by Control Center using Ollama GLM 4.6</sub>")

	return sb.String()
}
