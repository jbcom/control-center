package cmd

import (
	"context"
	"encoding/json"
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
	fixerRepo  string
	fixerPR    int
	fixerRunID int64
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
  control-center fixer analyze --repo jbcom/control-center --pr 123

  # Analyze a specific workflow run
  control-center fixer analyze --repo jbcom/control-center --run-id 12345678`,
}

var fixerAnalyzeCmd = &cobra.Command{
	Use:   "analyze",
	Short: "Analyze CI failures and suggest fixes",
	RunE:  runFixer,
}

var fixerApplyCmd = &cobra.Command{
	Use:   "apply",
	Short: "Apply suggested fixes from analysis",
	Long:  "Applies fixes suggested by the analyze command. Requires --suggestion-file with analysis results.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		suggestionFile, _ := cmd.Flags().GetString("suggestion-file")
		if suggestionFile == "" {
			return fmt.Errorf("--suggestion-file is required")
		}
		
		repo, _ := cmd.Flags().GetString("repo")
		if repo == "" {
			return fmt.Errorf("--repo is required")
		}
		
		// Read suggestion file
		data, err := os.ReadFile(suggestionFile)
		if err != nil {
			return fmt.Errorf("failed to read suggestion file: %w", err)
		}
		
		var analysis struct {
			RootCause            string   `json:"root_cause"`
			FixSuggestion        string   `json:"fix_suggestion"`
			VerificationCommands []string `json:"verification_commands"`
			Confidence           string   `json:"confidence"`
		}
		
		if err := json.Unmarshal(data, &analysis); err != nil {
			return fmt.Errorf("failed to parse suggestion file: %w", err)
		}
		
		// Post the fix suggestion as a comment
		ghClient := github.NewClient(ghToken)
		prNum, _ := cmd.Flags().GetInt("pr")
		
		if prNum > 0 {
			comment := fmt.Sprintf("## 🔧 Applying Suggested Fix\n\n")
			comment += fmt.Sprintf("**Root Cause:** %s\n\n", analysis.RootCause)
			comment += fmt.Sprintf("**Fix:**\n%s\n\n", analysis.FixSuggestion)
			
			if len(analysis.VerificationCommands) > 0 {
				comment += "**Verification:**\n```bash\n"
				for _, cmd := range analysis.VerificationCommands {
					comment += cmd + "\n"
				}
				comment += "```\n"
			}
			
			if err := ghClient.PostComment(ctx, repo, prNum, comment); err != nil {
				return fmt.Errorf("failed to post fix: %w", err)
			}
			
			log.Info("Fix suggestion posted to PR")
			fmt.Printf("✅ Fix suggestion posted to PR #%d\n", prNum)
		} else {
			// Just output the fix
			fmt.Printf("Root Cause: %s\n\n", analysis.RootCause)
			fmt.Printf("Fix Suggestion:\n%s\n\n", analysis.FixSuggestion)
			fmt.Println("Note: No PR specified, fix not applied automatically")
		}
		
		return nil
	},
}

var fixerResolveConflictCmd = &cobra.Command{
	Use:   "resolve-conflict",
	Short: "Resolve merge conflicts in a PR",
	Long:  "Analyzes and provides guidance for resolving merge conflicts.",
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		
		ghToken := os.Getenv("GITHUB_TOKEN")
		if ghToken == "" {
			ghToken = os.Getenv("CI_GITHUB_TOKEN")
		}
		if ghToken == "" {
			return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
		}
		
		repo, _ := cmd.Flags().GetString("repo")
		if repo == "" {
			return fmt.Errorf("--repo is required")
		}
		
		prNum, _ := cmd.Flags().GetInt("pr")
		if prNum == 0 {
			return fmt.Errorf("--pr is required")
		}
		
		ghClient := github.NewClient(ghToken)
		
		// Get PR status to check for conflicts
		out, err := ghClient.RunGH(ctx, "pr", "view", fmt.Sprintf("%d", prNum),
			"--repo", repo, "--json", "mergeable,baseRefName,headRefName,title")
		if err != nil {
			return fmt.Errorf("failed to get PR status: %w", err)
		}
		
		var prData struct {
			Mergeable   string `json:"mergeable"`
			BaseRefName string `json:"baseRefName"`
			HeadRefName string `json:"headRefName"`
			Title       string `json:"title"`
		}
		if err := json.Unmarshal([]byte(out), &prData); err != nil {
			return fmt.Errorf("failed to parse PR data: %w", err)
		}
		
		if prData.Mergeable != "CONFLICTING" {
			fmt.Printf("✅ PR #%d has no conflicts\n", prNum)
			return nil
		}
		
		// Provide resolution instructions
		instructions := fmt.Sprintf("## 🔧 Merge Conflict Resolution Guide\n\n")
		instructions += fmt.Sprintf("**PR #%d:** %s\n\n", prNum, prData.Title)
		instructions += fmt.Sprintf("**Base branch:** `%s`\n", prData.BaseRefName)
		instructions += fmt.Sprintf("**Head branch:** `%s`\n\n", prData.HeadRefName)
		instructions += "### Resolution Steps:\n\n"
		instructions += "```bash\n"
		instructions += "# 1. Fetch latest changes\n"
		instructions += "git fetch origin\n\n"
		instructions += "# 2. Checkout your branch\n"
		instructions += fmt.Sprintf("git checkout %s\n\n", prData.HeadRefName)
		instructions += "# 3. Rebase against base branch\n"
		instructions += fmt.Sprintf("git rebase origin/%s\n\n", prData.BaseRefName)
		instructions += "# 4. Resolve conflicts in your editor\n"
		instructions += "# After resolving each file:\n"
		instructions += "git add <resolved-file>\n\n"
		instructions += "# 5. Continue rebase\n"
		instructions += "git rebase --continue\n\n"
		instructions += "# 6. Force push (CAUTION: ensure you're on the right branch)\n"
		instructions += "git push --force-with-lease\n"
		instructions += "```\n\n"
		instructions += "### Tips:\n"
		instructions += "- Use `git status` to see conflicted files\n"
		instructions += "- Look for `<<<<<<<`, `=======`, `>>>>>>>` markers\n"
		instructions += "- Keep code from both sides if needed\n"
		instructions += "- Test after resolving\n"
		
		// Post to PR
		if err := ghClient.PostComment(ctx, repo, prNum, instructions); err != nil {
			return fmt.Errorf("failed to post instructions: %w", err)
		}
		
		log.WithField("pr", prNum).Info("Conflict resolution instructions posted")
		fmt.Printf("✅ Conflict resolution guide posted to PR #%d\n", prNum)
		
		return nil
	},
}

func init() {
	rootCmd.AddCommand(fixerCmd)
	fixerCmd.AddCommand(fixerAnalyzeCmd)
	fixerCmd.AddCommand(fixerApplyCmd)
	fixerCmd.AddCommand(fixerResolveConflictCmd)

	// Flags for analyze subcommand
	fixerAnalyzeCmd.Flags().StringVar(&fixerRepo, "repo", "", "repository (owner/name)")
	fixerAnalyzeCmd.Flags().IntVar(&fixerPR, "pr", 0, "pull request number")
	fixerAnalyzeCmd.Flags().Int64Var(&fixerRunID, "run-id", 0, "workflow run ID")
	fixerAnalyzeCmd.Flags().StringVar(&outputFormat, "output", "markdown", "output format (markdown or json)")
	fixerAnalyzeCmd.MarkFlagRequired("repo")

	// Flags for apply subcommand
	fixerApplyCmd.Flags().String("suggestion-file", "", "Path to suggestion JSON file")
	fixerApplyCmd.Flags().String("repo", "", "repository (owner/name)")
	fixerApplyCmd.Flags().Int("pr", 0, "pull request number (optional)")
	fixerApplyCmd.MarkFlagRequired("suggestion-file")
	fixerApplyCmd.MarkFlagRequired("repo")

	// Flags for resolve-conflict subcommand
	fixerResolveConflictCmd.Flags().String("repo", "", "repository (owner/name)")
	fixerResolveConflictCmd.Flags().Int("pr", 0, "pull request number")
	fixerResolveConflictCmd.MarkFlagRequired("repo")
	fixerResolveConflictCmd.MarkFlagRequired("pr")

	viper.BindPFlag("fixer.repo", fixerAnalyzeCmd.Flags().Lookup("repo"))
	viper.BindPFlag("fixer.pr", fixerAnalyzeCmd.Flags().Lookup("pr"))
	viper.BindPFlag("fixer.run_id", fixerAnalyzeCmd.Flags().Lookup("run-id"))
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

	if outputFormat == "json" {
		// Output as JSON for programmatic use
		output := map[string]interface{}{
			"root_cause":            analysis.RootCause,
			"fix_suggestion":        analysis.FixSuggestion,
			"verification_commands": analysis.VerificationCommands,
			"confidence":            analysis.Confidence,
		}
		jsonData, err := json.Marshal(output)
		if err != nil {
			return fmt.Errorf("failed to marshal analysis: %w", err)
		}
		fmt.Println(string(jsonData))
		return nil
	}

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
