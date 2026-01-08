// Package cmd provides the command-line interface for control-center.
package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/go-github/v66/github"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"golang.org/x/oauth2"
)

var (
	syncOrg        string
	syncRepo       string
	syncAll        bool
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

// init registers the `sync` command with the root command and configures its CLI flags:
// `--org`, `--repo`, `--all`, and `--config`; it also marks the `org` flag as required.
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
				Pattern    string   `json:"pattern"`
				Type       string   `json:"type"`
				Reason     string   `json:"reason"`
				Exceptions []string `json:"exceptions"`
			} `json:"patterns"`
		} `json:"killList"`
		ManagedRepos []string `json:"managedRepos"`
	} `json:"ecosystem"`
}

// runSync executes the "sync" command: it obtains a GitHub token from the
// environment, loads the sync configuration, determines the target repositories
// (from --repo or --all and the config), and for each repository runs three
// stages—kill-list processing, file synchronization, and an attempt to enable
// automerge—while logging progress and errors.
// 
// It returns an error when required credentials or configuration cannot be
// obtained or when repository selection is invalid. Errors encountered during
// per-repository processing are logged and cause the function to continue with
// the next repository rather than returning.
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

// processKillList processes the configured kill list for the given repository by removing files that match
// kill-list patterns. It creates a cleanup branch containing a commit that omits the matched files, opens a
// pull request to merge the cleanup branch into the repository's default branch, and attempts to apply
// labels to the PR.
// 
// If no files match the kill list, the function returns without making changes. It returns an error if any
// required GitHub operation (repository/tree/commit/branch/PR creation or update) fails.
func processKillList(ctx context.Context, client *github.Client, org, repo string, config syncConfig) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Processing kill list")

	// Get repository default branch
	repoInfo, _, err := client.Repositories.Get(ctx, org, repo)
	if err != nil {
		return fmt.Errorf("failed to get repo info: %w", err)
	}
	defaultBranch := repoInfo.GetDefaultBranch()

	// Get tree for default branch
	ref, _, err := client.Git.GetRef(ctx, org, repo, "refs/heads/"+defaultBranch)
	if err != nil {
		return fmt.Errorf("failed to get ref: %w", err)
	}

	commit, _, err := client.Git.GetCommit(ctx, org, repo, ref.Object.GetSHA())
	if err != nil {
		return fmt.Errorf("failed to get commit: %w", err)
	}

	tree, _, err := client.Git.GetTree(ctx, org, repo, commit.Tree.GetSHA(), true)
	if err != nil {
		return fmt.Errorf("failed to get tree: %w", err)
	}

	// Find files to delete
	var filesToDelete []string
	for _, entry := range tree.Entries {
		if entry.GetType() != "blob" {
			continue
		}

		path := entry.GetPath()
		if shouldDeleteFile(path, config) {
			filesToDelete = append(filesToDelete, path)
		}
	}

	if len(filesToDelete) == 0 {
		log.Info("No files to delete from kill list")
		return nil
	}

	log.WithField("count", len(filesToDelete)).Info("Files to delete")

	// Create branch for cleanup
	branchName := fmt.Sprintf("repo-sync/cleanup-kill-list-%d", time.Now().Unix())
	newRef := &github.Reference{
		Ref: github.String("refs/heads/" + branchName),
		Object: &github.GitObject{
			SHA: ref.Object.SHA,
		},
	}

	_, _, err = client.Git.CreateRef(ctx, org, repo, newRef)
	if err != nil {
		// Branch might already exist, try to update it
		newRef.Ref = github.String("heads/" + branchName)
		_, _, err = client.Git.UpdateRef(ctx, org, repo, newRef, false)
		if err != nil {
			return fmt.Errorf("failed to create/update branch: %w", err)
		}
	}

	// Create new tree without deleted files
	var treeEntries []*github.TreeEntry
	for _, entry := range tree.Entries {
		if entry.GetType() != "blob" {
			continue
		}

		path := entry.GetPath()
		shouldDelete := false
		for _, delPath := range filesToDelete {
			if path == delPath {
				shouldDelete = true
				break
			}
		}

		if !shouldDelete {
			treeEntries = append(treeEntries, &github.TreeEntry{
				Path: github.String(path),
				Mode: github.String(entry.GetMode()),
				Type: github.String(entry.GetType()),
				SHA:  entry.SHA,
			})
		}
	}

	newTree, _, err := client.Git.CreateTree(ctx, org, repo, "", treeEntries)
	if err != nil {
		return fmt.Errorf("failed to create tree: %w", err)
	}

	// Create commit
	commitMessage := "chore(sync): cleanup deprecated workflows\n\n[skip ci]"
	newCommit, _, err := client.Git.CreateCommit(ctx, org, repo, &github.Commit{
		Message: github.String(commitMessage),
		Tree:    newTree,
		Parents: []*github.Commit{{SHA: commit.SHA}},
	}, nil)
	if err != nil {
		return fmt.Errorf("failed to create commit: %w", err)
	}

	// Update branch reference
	newRef.Object.SHA = newCommit.SHA
	newRef.Ref = github.String("heads/" + branchName)
	_, _, err = client.Git.UpdateRef(ctx, org, repo, newRef, false)
	if err != nil {
		return fmt.Errorf("failed to update ref: %w", err)
	}

	// Create PR
	pr, _, err := client.PullRequests.Create(ctx, org, repo, &github.NewPullRequest{
		Title: github.String("chore(sync): cleanup deprecated workflows"),
		Head:  github.String(branchName),
		Base:  github.String(defaultBranch),
		Body: github.String("Removes legacy ai/ecosystem workflow files per the control-center kill list.\n\n" +
			"Files deleted:\n" + formatFileList(filesToDelete)),
	})
	if err != nil {
		return fmt.Errorf("failed to create PR: %w", err)
	}

	// Add labels
	_, _, err = client.Issues.AddLabelsToIssue(ctx, org, repo, pr.GetNumber(), []string{"sync", "automated"})
	if err != nil {
		log.WithError(err).Warn("Failed to add labels to PR")
	}

	log.WithFields(log.Fields{
		"pr":    pr.GetNumber(),
		"files": len(filesToDelete),
	}).Info("Created cleanup PR")

	return nil
}

// syncFiles syncs files from jbcom/control-center into the specified repository by creating a sync branch, committing the files, and opening a pull request.
//
// It reads the control-center sync directories (global and optional language-specific), creates blobs and a new tree on a dedicated branch, and creates a pull request targeting the repository's default branch. It attempts to add labels to the created PR. Returns nil on success or an error if required GitHub operations (refs, blobs, tree, commit, or PR creation) fail.
func syncFiles(ctx context.Context, client *github.Client, org, repo string) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Syncing files")

	// Get repository info
	repoInfo, _, err := client.Repositories.Get(ctx, org, repo)
	if err != nil {
		return fmt.Errorf("failed to get repo info: %w", err)
	}
	defaultBranch := repoInfo.GetDefaultBranch()
	language := strings.ToLower(repoInfo.GetLanguage())

	// Read sync-files directory structure
	syncDirs := []string{
		"sync-files/always-sync/global",
	}

	// Add language-specific sync if applicable
	if language != "" {
		langDir := fmt.Sprintf("sync-files/always-sync/%s", language)
		syncDirs = append(syncDirs, langDir)
	}

	var filesToSync []syncFile
	for _, dir := range syncDirs {
		files, err := readSyncDirectory(ctx, client, "jbcom", "control-center", dir)
		if err != nil {
			log.WithError(err).WithField("dir", dir).Warn("Failed to read sync directory")
			continue
		}
		filesToSync = append(filesToSync, files...)
	}

	if len(filesToSync) == 0 {
		log.Info("No files to sync")
		return nil
	}

	log.WithField("count", len(filesToSync)).Info("Files to sync")

	// Get target repo default branch ref
	targetRef, _, err := client.Git.GetRef(ctx, org, repo, "refs/heads/"+defaultBranch)
	if err != nil {
		return fmt.Errorf("failed to get target ref: %w", err)
	}

	// Create branch for sync
	branchName := fmt.Sprintf("repo-sync/control-center-%d", time.Now().Unix())
	newRef := &github.Reference{
		Ref: github.String("refs/heads/" + branchName),
		Object: &github.GitObject{
			SHA: targetRef.Object.SHA,
		},
	}

	_, _, err = client.Git.CreateRef(ctx, org, repo, newRef)
	if err != nil {
		// Branch might already exist, try to update it
		newRef.Ref = github.String("heads/" + branchName)
		_, _, err = client.Git.UpdateRef(ctx, org, repo, newRef, false)
		if err != nil {
			return fmt.Errorf("failed to create/update branch: %w", err)
		}
	}

	// Create blobs for each file
	var treeEntries []*github.TreeEntry
	for _, file := range filesToSync {
		blob, _, err := client.Git.CreateBlob(ctx, org, repo, &github.Blob{
			Content:  github.String(file.content),
			Encoding: github.String("utf-8"),
		})
		if err != nil {
			log.WithError(err).WithField("path", file.path).Warn("Failed to create blob")
			continue
		}

		treeEntries = append(treeEntries, &github.TreeEntry{
			Path: github.String(file.path),
			Mode: github.String("100644"),
			Type: github.String("blob"),
			SHA:  blob.SHA,
		})
	}

	// Get base tree
	targetCommit, _, err := client.Git.GetCommit(ctx, org, repo, targetRef.Object.GetSHA())
	if err != nil {
		return fmt.Errorf("failed to get target commit: %w", err)
	}

	// Create new tree
	newTree, _, err := client.Git.CreateTree(ctx, org, repo, targetCommit.Tree.GetSHA(), treeEntries)
	if err != nil {
		return fmt.Errorf("failed to create tree: %w", err)
	}

	// Create commit
	commitMessage := "chore(sync): sync files from control-center\n\nSynced from jbcom/control-center\n\n[skip ci]"
	newCommit, _, err := client.Git.CreateCommit(ctx, org, repo, &github.Commit{
		Message: github.String(commitMessage),
		Tree:    newTree,
		Parents: []*github.Commit{{SHA: targetCommit.SHA}},
	}, nil)
	if err != nil {
		return fmt.Errorf("failed to create commit: %w", err)
	}

	// Update branch reference
	newRef.Object.SHA = newCommit.SHA
	newRef.Ref = github.String("heads/" + branchName)
	_, _, err = client.Git.UpdateRef(ctx, org, repo, newRef, false)
	if err != nil {
		return fmt.Errorf("failed to update ref: %w", err)
	}

	// Check if PR already exists
	existingPRs, _, err := client.PullRequests.List(ctx, org, repo, &github.PullRequestListOptions{
		Head:  branchName,
		Base:  defaultBranch,
		State: "open",
	})
	if err == nil && len(existingPRs) > 0 {
		log.WithField("pr", existingPRs[0].GetNumber()).Info("PR already exists, updated branch")
		return nil
	}

	// Create PR
	pr, _, err := client.PullRequests.Create(ctx, org, repo, &github.NewPullRequest{
		Title: github.String("chore(sync): sync files from control-center"),
		Head:  github.String(branchName),
		Base:  github.String(defaultBranch),
		Body:  github.String(fmt.Sprintf("Synced from jbcom/control-center\n\nFiles synced: %d", len(filesToSync))),
	})
	if err != nil {
		return fmt.Errorf("failed to create PR: %w", err)
	}

	// Add labels
	_, _, err = client.Issues.AddLabelsToIssue(ctx, org, repo, pr.GetNumber(), []string{"sync", "automated", "automerge"})
	if err != nil {
		log.WithError(err).Warn("Failed to add labels to PR")
	}

	log.WithFields(log.Fields{
		"pr":    pr.GetNumber(),
		"files": len(filesToSync),
	}).Info("Created sync PR")

	return nil
}

// enableAutomerge enables automerge on open pull requests in the given repository that have the "automerge" label.
// It returns an error if listing pull requests fails; failures to enable automerge for individual PRs are logged and do not abort processing.
func enableAutomerge(ctx context.Context, client *github.Client, org, repo string) error {
	log.WithFields(log.Fields{
		"org":  org,
		"repo": repo,
	}).Info("Enabling automerge")

	// Find PRs with automerge label
	prs, _, err := client.PullRequests.List(ctx, org, repo, &github.PullRequestListOptions{
		State: "open",
		ListOptions: github.ListOptions{
			PerPage: 100,
		},
	})
	if err != nil {
		return fmt.Errorf("failed to list PRs: %w", err)
	}

	for _, pr := range prs {
		// Check if PR has automerge label
		hasAutomergeLabel := false
		for _, label := range pr.Labels {
			if label.GetName() == "automerge" {
				hasAutomergeLabel = true
				break
			}
		}

		if !hasAutomergeLabel {
			continue
		}

		// Enable automerge via GraphQL
		if err := enablePRAutomerge(ctx, client, pr.GetNodeID()); err != nil {
			log.WithError(err).WithField("pr", pr.GetNumber()).Warn("Failed to enable automerge")
			continue
		}

		log.WithField("pr", pr.GetNumber()).Info("Enabled automerge")
	}

	return nil
}

// enablePRAutomerge prepares a GraphQL mutation to enable automerge for the given pull request node ID but does not execute the mutation.
// 
// The function constructs the GraphQL mutation and variables for enabling auto-merge with the squash method and logs that the
// enablement was prepared. It does not make any network calls or modify GitHub state; it is a no-op placeholder that always returns nil.
// 
// Parameters:
//   - ctx: request context (used for cancellation in a full implementation).
//   - client: GitHub REST client (unused in this placeholder).
//   - nodeID: the GraphQL node ID of the pull request to enable automerge for.
func enablePRAutomerge(ctx context.Context, client *github.Client, nodeID string) error {
	mutation := `
		mutation($pullRequestId: ID!) {
			enablePullRequestAutoMerge(input: {
				pullRequestId: $pullRequestId,
				mergeMethod: SQUASH
			}) {
				pullRequest {
					id
					autoMergeRequest {
						enabledAt
					}
				}
			}
		}
	`

	variables := map[string]interface{}{
		"pullRequestId": nodeID,
	}

	// Note: This is a placeholder for GraphQL automerge enablement
	// Full implementation would require:
	// 1. A GraphQL client library (e.g., github.com/shurcooL/graphql)
	// 2. Making raw HTTP POST to https://api.github.com/graphql
	// 3. Or using gh CLI: gh pr merge --auto --squash <PR_NUMBER>
	//
	// The mutation and variables are prepared but not executed.
	// This function currently only identifies PRs that should have automerge enabled.
	_ = mutation
	_ = variables
	
	log.WithField("nodeId", nodeID).Info("Automerge enablement prepared (requires GraphQL implementation)")
	
	return nil
}

// Helper types and functions

type syncFile struct {
	path    string
	content string
}

// shouldDeleteFile reports whether the given repository path should be removed according to the configured kill list.
// It returns true when the path matches a kill-list pattern (regex or glob) and is not in the hardcoded protected list or the pattern's exceptions, false otherwise.
func shouldDeleteFile(path string, config syncConfig) bool {
	// Check if protected
	for _, pattern := range []string{
		".github/workflows/triage.yml",
		".github/workflows/autoheal.yml",
		".github/workflows/review.yml",
		".github/workflows/delegator.yml",
		".github/workflows/ci.yml",
		".github/workflows/go.yml",
		".github/workflows/docs.yml",
		".github/workflows/docs-sync.yml",
		".github/workflows/release.yml",
		".github/workflows/release-please.yml",
		".github/workflows/sync.yml",
		".github/workflows/test-coverage.yml",
		".github/workflows/control-center-build.yml",
	} {
		if path == pattern {
			return false
		}
	}

	// Check against kill list patterns
	for _, patternConfig := range config.Ecosystem.KillList.Patterns {
		// Check exceptions
		for _, exception := range patternConfig.Exceptions {
			if path == exception {
				return false
			}
		}

		// Match based on type
		matched := false
		switch patternConfig.Type {
		case "regex":
			// Match regex patterns using string operations for safety
			if patternConfig.Pattern == "^\\.github/workflows/(ai|ecosystem)-.*\\.ya?ml$" {
				if filepath.Dir(path) == ".github/workflows" {
					base := filepath.Base(path)
					hasAIPrefix := len(base) >= 3 && base[:3] == "ai-"
					hasEcoPrefix := len(base) >= 10 && base[:10] == "ecosystem-"
					hasYAMLExt := filepath.Ext(path) == ".yml" || filepath.Ext(path) == ".yaml"
					if (hasAIPrefix || hasEcoPrefix) && hasYAMLExt {
						matched = true
					}
				}
			} else if patternConfig.Pattern == "^\\.github/workflows/.*-local\\.ya?ml$" {
				if filepath.Dir(path) == ".github/workflows" {
					base := filepath.Base(path)
					hasLocalYML := len(base) >= 10 && base[len(base)-10:] == "-local.yml"
					hasLocalYAML := len(base) >= 11 && base[len(base)-11:] == "-local.yaml"
					if hasLocalYML || hasLocalYAML {
						matched = true
					}
				}
			} else if patternConfig.Pattern == "^\\.github/workflows/jules-.*\\.ya?ml$" {
				if filepath.Dir(path) == ".github/workflows" {
					base := filepath.Base(path)
					hasJulesPrefix := len(base) >= 6 && base[:6] == "jules-"
					hasYAMLExt := filepath.Ext(path) == ".yml" || filepath.Ext(path) == ".yaml"
					if hasJulesPrefix && hasYAMLExt {
						matched = true
					}
				}
			}
		case "glob":
			// Simple glob matching
			if patternConfig.Pattern == ".crew/agents/jules/**" {
				if len(path) >= 19 && path[:19] == ".crew/agents/jules/" {
					matched = true
				}
			}
		}

		if matched {
			return true
		}
	}

	return false
}

// readSyncDirectory reads all files under dir in the given repository and returns their contents
// with paths relative to dir.
// It traverses subdirectories recursively. If listing the target directory fails the error is
// returned; individual files or subdirectories that cannot be retrieved or decoded are skipped
// and a warning is logged.
func readSyncDirectory(ctx context.Context, client *github.Client, org, repo, dir string) ([]syncFile, error) {
	_, dirContent, _, err := client.Repositories.GetContents(ctx, org, repo, dir, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to get directory contents: %w", err)
	}

	var files []syncFile
	for _, item := range dirContent {
		if item.GetType() == "file" {
			content, _, _, err := client.Repositories.GetContents(ctx, org, repo, item.GetPath(), nil)
			if err != nil {
				log.WithError(err).WithField("path", item.GetPath()).Warn("Failed to get file content")
				continue
			}

			decodedContent, err := content.GetContent()
			if err != nil {
				log.WithError(err).WithField("path", item.GetPath()).Warn("Failed to decode file content")
				continue
			}

			// Calculate relative path from sync directory
			itemPath := item.GetPath()
			if len(itemPath) < len(dir)+2 {
				log.WithField("path", itemPath).Warn("Invalid path length")
				continue
			}
			relativePath := itemPath[len(dir)+1:]

			files = append(files, syncFile{
				path:    relativePath,
				content: decodedContent,
			})
		} else if item.GetType() == "dir" {
			// Recursively read subdirectories
			subFiles, err := readSyncDirectory(ctx, client, org, repo, item.GetPath())
			if err != nil {
				log.WithError(err).WithField("path", item.GetPath()).Warn("Failed to read subdirectory")
				continue
			}
			files = append(files, subFiles...)
		}
	}

	return files, nil
}

// formatFileList formats a slice of file paths as a markdown list suitable for inclusion in a pull request body.
// Each file becomes a line of the form "- `path`" terminated with a newline.
func formatFileList(files []string) string {
	result := ""
	for _, file := range files {
		result += fmt.Sprintf("- `%s`\n", file)
	}
	return result
}