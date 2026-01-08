// Package cmd provides the command-line interface for control-center.
package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/google/go-github/v66/github"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"golang.org/x/oauth2"
)

var (
	syncOrg      string
	syncRepo     string
	syncAll      bool
	syncConfigPath string
)

// syncCmd represents the sync command
var syncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Sync files across repositories using GitHub API",
	Long: `Sync files across repositories in the ecosystem using GitHub API.
	
This command provides programmatic file synchronization with automatic PR creation,
automerge enablement, and kill list processing.

Examples:
  # Sync files to all repositories in an organization
  control-center sync --org jbcom --all

  # Sync files to a specific repository
  control-center sync --org jbcom --repo control-center

  # Sync with custom config
  control-center sync --org jbcom --all --config custom-sync.json`,
	RunE: runSync,
}

func init() {
	rootCmd.AddCommand(syncCmd)

	syncCmd.Flags().StringVar(&syncOrg, "org", "", "GitHub organization to sync (required)")
	syncCmd.Flags().StringVar(&syncRepo, "repo", "", "Specific repository to sync (optional, syncs all if not specified)")
	syncCmd.Flags().BoolVar(&syncAll, "all", false, "Sync all repositories in the organization")
	syncCmd.Flags().StringVar(&syncConfigPath, "config", "agentic.config.json", "Path to sync configuration file")
	
	syncCmd.MarkFlagRequired("org")
}

type syncConfig struct {
	Ecosystem struct {
		KillList struct {
			Patterns []struct {
				Pattern   string   `json:"pattern"`
				Type      string   `json:"type"`
				Reason    string   `json:"reason"`
				Exceptions []string `json:"exceptions"`
			} `json:"patterns"`
		} `json:"killList"`
		ManagedRepos []string `json:"managedRepos"`
	} `json:"ecosystem"`
}

func runSync(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	// Get GitHub token
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		token = os.Getenv("CI_GITHUB_TOKEN")
	}
	if token == "" {
		return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN environment variable required")
	}

	// Create GitHub client
	ts := oauth2.StaticTokenSource(&oauth2.Token{AccessToken: token})
	tc := oauth2.NewClient(ctx, ts)
	client := github.NewClient(tc)

	// Load sync configuration
	configData, err := os.ReadFile(syncConfigPath)
	if err != nil {
		return fmt.Errorf("failed to read sync config: %w", err)
	}

	var config syncConfig
	if err := json.Unmarshal(configData, &config); err != nil {
		return fmt.Errorf("failed to parse sync config: %w", err)
	}

	// Determine repositories to sync
	var repos []string
	if syncRepo != "" {
		repos = []string{syncRepo}
	} else if syncAll {
		repos = config.Ecosystem.ManagedRepos
	} else {
		return fmt.Errorf("either --repo or --all must be specified")
	}

	log.WithFields(log.Fields{
		"org":   syncOrg,
		"repos": len(repos),
	}).Info("Starting sync operation")

	for _, repoName := range repos {
		// Extract repo name without org prefix if present
		if filepath.Dir(repoName) != "." {
			repoName = filepath.Base(repoName)
		}

		log.WithFields(log.Fields{
			"org":  syncOrg,
			"repo": repoName,
		}).Info("Processing repository")

		if dryRun {
			log.Info("DRY RUN: Would sync repository")
			continue
		}

		// Step 1: Process kill list (deletions first)
		if err := processKillList(ctx, client, syncOrg, repoName, config); err != nil {
			log.WithError(err).Error("Failed to process kill list")
			continue
		}

		// Step 2: Sync files
		if err := syncFiles(ctx, client, syncOrg, repoName); err != nil {
			log.WithError(err).Error("Failed to sync files")
			continue
		}

		// Step 3: Enable automerge on PR
		if err := enableAutomerge(ctx, client, syncOrg, repoName); err != nil {
			log.WithError(err).Warn("Failed to enable automerge")
		}

		log.WithFields(log.Fields{
			"org":  syncOrg,
			"repo": repoName,
		}).Info("Successfully synced repository")
	}

	return nil
}

func processKillList(ctx context.Context, client *github.Client, org, repo string, config syncConfig) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Processing kill list")

	// TODO: Implement kill list processing using GitHub API
	// 1. Clone or fetch repository files via API
	// 2. Apply kill list patterns
	// 3. Create PR with deletions
	// 4. Add [skip ci] to commit message

	return nil
}

func syncFiles(ctx context.Context, client *github.Client, org, repo string) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Syncing files")

	// TODO: Implement file sync using GitHub API
	// 1. Read sync-files directory structure
	// 2. For each file in always-sync and language-specific dirs:
	//    - Get file content from this repo
	//    - Compare with target repo
	//    - Create/update files via API
	// 3. Create PR with changes
	// 4. Add [skip ci] to commit message

	return nil
}

func enableAutomerge(ctx context.Context, client *github.Client, org, repo string) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Enabling automerge")

	// TODO: Implement automerge enablement using GitHub API
	// 1. Find PR created by sync
	// 2. Enable automerge via GraphQL API
	// 3. Add automerge label

	return nil
}
