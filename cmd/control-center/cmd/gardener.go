package cmd

import (
	"context"
	"fmt"
	"os"

	"github.com/jbcom/control-center/pkg/clients/github"
	"github.com/jbcom/control-center/pkg/orchestrator"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	gardenerTarget    string
	gardenerDecompose bool
	processBacklog    bool
)

var gardenerCmd = &cobra.Command{
	Use:   "gardener",
	Short: "Enterprise-level cascade orchestrator",
	Long: `The Gardener orchestrates enterprise-level operations across all organizations.

It cascades instructions from enterprise → org control centers → repositories.

Responsibilities:
  1. Discover all organizations in the enterprise
  2. Auto-heal organization control centers (missing files, misconfig)
  3. Process prompt-queue issues for cascade execution
  4. Trigger backlog reconciliation (outstanding PRs/issues)
  5. Optionally decompose to second level (org → repos)

Examples:
  # Run for all organizations
  control-center gardener --target all

  # Run for specific organization
  control-center gardener --target extended-data-library

  # Run with decomposition to repository level
  control-center gardener --target all --decompose

  # Dry run
  control-center gardener --target all --dry-run`,
	RunE: runGardener,
}

func init() {
	rootCmd.AddCommand(gardenerCmd)

	gardenerCmd.Flags().StringVar(&gardenerTarget, "target", "all", "target: all, org-name, or org-name/repo-name")
	gardenerCmd.Flags().BoolVar(&gardenerDecompose, "decompose", false, "decompose to repository level")
	gardenerCmd.Flags().BoolVar(&processBacklog, "backlog", true, "process backlog PRs/issues")

	viper.BindPFlag("gardener.target", gardenerCmd.Flags().Lookup("target"))
	viper.BindPFlag("gardener.decompose", gardenerCmd.Flags().Lookup("decompose"))
	viper.BindPFlag("gardener.backlog", gardenerCmd.Flags().Lookup("backlog"))
}

func runGardener(cmd *cobra.Command, args []string) error {
	ctx := context.Background()

	log.WithFields(log.Fields{
		"target":    gardenerTarget,
		"decompose": gardenerDecompose,
		"backlog":   processBacklog,
		"dry_run":   dryRun,
	}).Info("Starting gardener")

	// Initialize GitHub client
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		token = os.Getenv("CI_GITHUB_TOKEN")
	}
	if token == "" {
		return fmt.Errorf("GITHUB_TOKEN or CI_GITHUB_TOKEN required")
	}

	ghClient := github.NewClient(token)

	// Create orchestrator
	orch := orchestrator.NewGardener(ghClient, orchestrator.GardenerConfig{
		Target:         gardenerTarget,
		Decompose:      gardenerDecompose,
		ProcessBacklog: processBacklog,
		DryRun:         dryRun,
	})

	// Run the gardener
	if err := orch.Run(ctx); err != nil {
		log.WithError(err).Error("Gardener failed")
		return err
	}

	log.Info("Gardener completed successfully")
	return nil
}
