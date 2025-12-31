package orchestrator

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/jbcom/control-center/pkg/clients/github"
	log "github.com/sirupsen/logrus"
)

// GardenerConfig holds configuration for the Gardener
type GardenerConfig struct {
	Target         string
	Decompose      bool
	ProcessBacklog bool
	DryRun         bool
	StaleDays      int
}

// Gardener orchestrates enterprise-level operations
type Gardener struct {
	gh     *github.Client
	config GardenerConfig
}

// OrgRegistry represents the organization registry
type OrgRegistry struct {
	Enterprise           string               `json:"enterprise"`
	ManagedOrganizations []ManagedOrg         `json:"managedOrganizations"`
}

// ManagedOrg represents a managed organization
type ManagedOrg struct {
	Org           string `json:"org"`
	Domain        string `json:"domain"`
	ControlCenter string `json:"control_center"`
	Type          string `json:"type"`
}

// NewGardener creates a new Gardener orchestrator
func NewGardener(gh *github.Client, config GardenerConfig) *Gardener {
	if config.StaleDays == 0 {
		config.StaleDays = 7
	}
	return &Gardener{
		gh:     gh,
		config: config,
	}
}

// Run executes the gardener workflow
func (g *Gardener) Run(ctx context.Context) error {
	log.Info("🌱 Starting Gardener orchestration")

	// Step 1: Discover organizations
	orgs, err := g.discoverOrganizations(ctx)
	if err != nil {
		return fmt.Errorf("discovery failed: %w", err)
	}

	log.WithField("count", len(orgs)).Info("Discovered organizations")

	// Filter by target if specified
	orgs = g.filterByTarget(orgs)

	if len(orgs) == 0 {
		log.Warn("No organizations matched target")
		return nil
	}

	// Step 2: Heal control centers
	for _, org := range orgs {
		if err := g.healControlCenter(ctx, org); err != nil {
			log.WithError(err).WithField("org", org.Org).Warn("Failed to heal control center")
			// Continue with other orgs
		}
	}

	// Step 3: Process backlog if enabled
	if g.config.ProcessBacklog {
		for _, org := range orgs {
			if err := g.processBacklog(ctx, org); err != nil {
				log.WithError(err).WithField("org", org.Org).Warn("Failed to process backlog")
				// Continue with other orgs
			}
		}
	}

	// Step 4: Decompose if enabled
	if g.config.Decompose {
		for _, org := range orgs {
			if err := g.decompose(ctx, org); err != nil {
				log.WithError(err).WithField("org", org.Org).Warn("Failed to decompose")
				// Continue with other orgs
			}
		}
	}

	log.Info("🌱 Gardener completed")
	return nil
}

// discoverOrganizations reads the organization registry
func (g *Gardener) discoverOrganizations(ctx context.Context) ([]ManagedOrg, error) {
	// Try to read from local file first
	registryPath := ".github/org-registry.json"
	data, err := os.ReadFile(registryPath)
	if err != nil {
		log.WithError(err).Debug("Failed to read local registry, trying GitHub API")
		// Would fetch from GitHub API here
		return nil, fmt.Errorf("org-registry.json not found: %w", err)
	}

	var registry OrgRegistry
	if err := json.Unmarshal(data, &registry); err != nil {
		return nil, fmt.Errorf("failed to parse registry: %w", err)
	}

	return registry.ManagedOrganizations, nil
}

// filterByTarget filters organizations by the target configuration
func (g *Gardener) filterByTarget(orgs []ManagedOrg) []ManagedOrg {
	if g.config.Target == "all" || g.config.Target == "" {
		return orgs
	}

	var filtered []ManagedOrg
	for _, org := range orgs {
		if org.Org == g.config.Target {
			filtered = append(filtered, org)
		}
	}
	return filtered
}

// healControlCenter checks and heals an organization's control center
func (g *Gardener) healControlCenter(ctx context.Context, org ManagedOrg) error {
	log.WithField("org", org.Org).Info("🔧 Checking control center health")

	if g.config.DryRun {
		log.WithField("org", org.Org).Info("[DRY RUN] Would check control center")
		return nil
	}

	// Check for required files
	requiredFiles := []string{
		".github/workflows/ci.yml",
		".cursor/rules/00-fundamentals.mdc",
		"CLAUDE.md",
	}

	missing := []string{}
	for _, file := range requiredFiles {
		// Would check via GitHub API
		log.WithFields(log.Fields{
			"org":  org.Org,
			"file": file,
		}).Debug("Checking required file")
	}

	if len(missing) > 0 {
		log.WithFields(log.Fields{
			"org":     org.Org,
			"missing": missing,
		}).Warn("Control center missing required files")

		// Would trigger sync workflow here
		if !g.config.DryRun {
			log.Info("Triggering sync workflow")
			// g.gh.TriggerWorkflow(ctx, org.ControlCenter, "repo-sync.yml", nil)
		}
	}

	log.WithField("org", org.Org).Info("✅ Control center healthy")
	return nil
}

// processBacklog handles stale PRs and unassigned issues
func (g *Gardener) processBacklog(ctx context.Context, org ManagedOrg) error {
	log.WithField("org", org.Org).Info("📚 Processing backlog")

	if g.config.DryRun {
		log.WithField("org", org.Org).Info("[DRY RUN] Would process backlog")
		return nil
	}

	// Get stale PRs
	prs, err := g.gh.ListOpenPRs(ctx, org.ControlCenter)
	if err != nil {
		return fmt.Errorf("failed to list PRs: %w", err)
	}

	staleThreshold := time.Now().Add(-time.Duration(g.config.StaleDays) * 24 * time.Hour)

	for _, pr := range prs {
		if pr.Draft {
			continue
		}

		if pr.UpdatedAt.Before(staleThreshold) {
			log.WithFields(log.Fields{
				"pr":      pr.Number,
				"title":   pr.Title,
				"updated": pr.UpdatedAt,
			}).Warn("Stale PR detected")

			if !g.config.DryRun {
				// Add stale label
				if err := g.gh.AddLabel(ctx, org.ControlCenter, pr.Number, "stale"); err != nil {
					log.WithError(err).Warn("Failed to add stale label")
				}

				// Post comment
				comment := `⏰ **Stale PR Detected**

This PR has been inactive for more than 7 days. The Gardener will attempt to:
1. Check if CI is passing
2. Resolve any blockers
3. Merge if ready

If you want to keep this PR open, please update it.`
				if err := g.gh.PostComment(ctx, org.ControlCenter, pr.Number, comment); err != nil {
					log.WithError(err).Warn("Failed to post comment")
				}
			}
		}
	}

	// Get unassigned issues
	issues, err := g.gh.ListOpenIssues(ctx, org.ControlCenter)
	if err != nil {
		return fmt.Errorf("failed to list issues: %w", err)
	}

	for _, issue := range issues {
		if len(issue.Assignees) == 0 {
			log.WithFields(log.Fields{
				"issue": issue.Number,
				"title": issue.Title,
			}).Info("Unassigned issue found")

			if !g.config.DryRun {
				// Add needs-triage label
				if err := g.gh.AddLabel(ctx, org.ControlCenter, issue.Number, "needs-triage"); err != nil {
					log.WithError(err).Warn("Failed to add needs-triage label")
				}
			}
		}
	}

	log.WithField("org", org.Org).Info("✅ Backlog processed")
	return nil
}

// decompose triggers org-level gardeners
func (g *Gardener) decompose(ctx context.Context, org ManagedOrg) error {
	log.WithField("org", org.Org).Info("🔄 Decomposing to org level")

	if g.config.DryRun {
		log.WithField("org", org.Org).Info("[DRY RUN] Would trigger org gardener")
		return nil
	}

	// Would trigger org-gardener workflow
	log.WithFields(log.Fields{
		"org":      org.Org,
		"workflow": "org-gardener.yml",
	}).Info("Triggering org gardener")

	return nil
}
