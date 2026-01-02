// Package cmd provides the command-line interface for control-center.
// It includes commands for managing AI workflows, ecosystem sync,
// Jules integration, and CodeQL analysis enhancement.
package cmd

import (
	"fmt"
	"os"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	cfgFile      string
	logLevel     string
	logFormat    string
	dryRun       bool
	outputFormat string
)

// Build information set via ldflags at build time
var (
	Version = "dev"
	Commit  = "none"
	Date    = "unknown"
)

// rootCmd represents the base command
var rootCmd = &cobra.Command{
	Use:   "control-center",
	Short: "Enterprise AI orchestration for the jbcom ecosystem",
	Long: `Control Center is the unified orchestration hub for managing AI agents,
repository synchronization, and enterprise workflows across the jbcom ecosystem.

It provides:
  - Gardener: Enterprise-level cascade orchestration
  - Curator: Nightly triage of issues and PRs
  - Fixer: Automated CI failure resolution
  - Reviewer: AI-powered code review coordination
  - Delegator: Task routing to appropriate AI agents

AI Content Generation:
  - Imagen: Google Imagen 3 text-to-image generation
  - Veo: Google Veo 3.1 text-to-video generation
  - Proxy: OpenAI-compatible LLM proxy for CodeQL integration

Built-in AI integrations:
  - Ollama (GLM 4.6 Cloud) for fast analysis
  - Google Jules for multi-file refactoring
  - Cursor Cloud Agent for long-running tasks
  - Google Gemini for advanced reasoning
  - Google Imagen 3 for image generation
  - Google Veo 3.1 for video generation

Examples:
  # Run the gardener for all organizations
  control-center gardener --target all

  # Curate a specific repository
  control-center curator --repo jbcom/control-center

  # Fix CI failures for a PR
  control-center fixer --repo jbcom/control-center --pr 123

  # Review a PR with Ollama
  control-center reviewer --repo jbcom/control-center --pr 456

  # Generate images with Imagen 3
  control-center imagen generate "cyberpunk city" --count 4

  # Generate videos with Veo 3.1
  control-center veo generate "ocean waves" --poll

  # Start LLM proxy server
  control-center proxy start --port 8080

  # Show version
  control-center version`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		// Set log level
		level, err := log.ParseLevel(logLevel)
		if err != nil {
			level = log.InfoLevel
		}
		log.SetLevel(level)

		// Set log format
		if logFormat == "json" {
			log.SetFormatter(&log.JSONFormatter{})
		} else {
			log.SetFormatter(&log.TextFormatter{
				FullTimestamp: true,
			})
		}
	},
}

// Execute runs the root command
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize(initConfig)

	// Global flags
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.control-center.yaml)")
	rootCmd.PersistentFlags().StringVar(&logLevel, "log-level", "info", "log level (debug, info, warn, error)")
	rootCmd.PersistentFlags().StringVar(&logFormat, "log-format", "text", "log format (text, json)")
	rootCmd.PersistentFlags().BoolVar(&dryRun, "dry-run", false, "run without making changes")

	// Bind to viper
	viper.BindPFlag("log.level", rootCmd.PersistentFlags().Lookup("log-level"))
	viper.BindPFlag("log.format", rootCmd.PersistentFlags().Lookup("log-format"))
	viper.BindPFlag("dry_run", rootCmd.PersistentFlags().Lookup("dry-run"))
}

func initConfig() {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		// Default config locations
		home, err := os.UserHomeDir()
		if err == nil {
			viper.AddConfigPath(home)
		}
		viper.AddConfigPath(".")
		viper.AddConfigPath("/etc/control-center")
		viper.SetConfigName(".control-center")
		viper.SetConfigType("yaml")
	}

	// Environment variables with CONTROL_CENTER prefix
	viper.SetEnvPrefix("CONTROL_CENTER")
	viper.AutomaticEnv()

	// Read config file if it exists
	if err := viper.ReadInConfig(); err == nil {
		log.WithField("file", viper.ConfigFileUsed()).Debug("Using config file")
	}
}

// GetVersion returns the version string
func GetVersion() string {
	return fmt.Sprintf("control-center %s (commit: %s, built: %s)", Version, Commit, Date)
}
