// Package cmd provides the command-line interface for control-center.
package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"

	"github.com/jbcom/control-center/pkg/proxy"
)

var (
	proxyPort       int
	proxyHost       string
	proxyConfigFile string
	proxyOutputFile string
)

// proxyCmd represents the proxy command
var proxyCmd = &cobra.Command{
	Use:   "proxy",
	Short: "LLM proxy server with OpenAI-compatible API",
	Long: `Start an LLM proxy server that routes requests to multiple backends
(Ollama, Gemini, etc.) with an OpenAI-compatible API.

The proxy provides:
  - OpenAI-compatible /v1/chat/completions endpoint
  - Health monitoring endpoint
  - Load balancing across multiple providers
  - Failover and retry logic
  - Provider abstraction for CodeQL and other tools

This enables CodeQL and other tools to use Ollama, Gemini, or other LLMs
through a single, standardized API.

Examples:
  # Start proxy server
  control-center proxy start --port 8080

  # Start with config file
  control-center proxy start --config proxy-config.json

  # Check proxy health
  control-center proxy health

  # Generate sample config
  control-center proxy config --output sample-config.json`,
}

// proxyStartCmd represents the proxy start command
var proxyStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start the LLM proxy server",
	Long: `Start the LLM proxy HTTP server on the specified port.

The server provides an OpenAI-compatible API that routes requests to
configured backend providers (Ollama, Gemini, etc.).

Configuration can be provided via:
  - Environment variables (OLLAMA_HOST, OLLAMA_API_KEY, etc.)
  - Config file (--config flag)
  - Command-line flags

The server will run until interrupted (Ctrl+C).

Examples:
  # Start on default port (8080)
  control-center proxy start

  # Start on custom port
  control-center proxy start --port 9000

  # Start with config file
  control-center proxy start --config proxy-config.json

  # Use with CodeQL or other tools
  export OPENAI_API_BASE=http://localhost:8080/v1
  codeql query run --llm-model glm-4.6 --query security.ql`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Load configuration
		var cfg *proxy.Config
		if proxyConfigFile != "" {
			log.WithField("file", proxyConfigFile).Info("Loading config from file")
			data, err := os.ReadFile(proxyConfigFile)
			if err != nil {
				return fmt.Errorf("failed to read config file: %w", err)
			}
			
			cfg = &proxy.Config{}
			if err := json.Unmarshal(data, cfg); err != nil {
				return fmt.Errorf("failed to parse config file: %w", err)
			}
		} else {
			// Default configuration from environment
			cfg = &proxy.Config{
				Port: proxyPort,
				Host: proxyHost,
				Providers: []proxy.ProviderConfig{
					{
						Name:     "ollama",
						Type:     "ollama",
						Enabled:  true,
						Priority: 1,
						Config: map[string]interface{}{
							"host":    getEnvOrDefault("OLLAMA_HOST", "https://ollama.com"),
							"api_key": os.Getenv("OLLAMA_API_KEY"),
							"model":   getEnvOrDefault("OLLAMA_MODEL", "glm-4.6:cloud"),
						},
					},
				},
				Routing: proxy.RoutingConfig{
					Strategy: "priority",
					Fallback: true,
				},
			}
		}

		// Create and start server
		ctx := context.Background()
		server, err := proxy.NewServer(cfg)
		if err != nil {
			return fmt.Errorf("failed to create proxy server: %w", err)
		}

		log.WithFields(log.Fields{
			"address":   fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
			"providers": len(cfg.Providers),
		}).Info("Starting LLM proxy server")

		// Setup graceful shutdown
		serverCtx, serverCancel := context.WithCancel(ctx)
		defer serverCancel()

		// Start server in goroutine
		errChan := make(chan error, 1)
		go func() {
			if err := server.Start(serverCtx); err != nil && err != http.ErrServerClosed {
				errChan <- err
			}
		}()

		// Wait for interrupt signal
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

		fmt.Printf("\n")
		fmt.Printf("🚀 LLM Proxy Server Running\n")
		fmt.Printf("   Address: http://%s:%d\n", cfg.Host, cfg.Port)
		fmt.Printf("   Health:  http://%s:%d/health\n", cfg.Host, cfg.Port)
		fmt.Printf("   API:     http://%s:%d/v1/chat/completions\n", cfg.Host, cfg.Port)
		fmt.Printf("\n")
		fmt.Printf("Press Ctrl+C to stop\n")
		fmt.Printf("\n")

		// Wait for shutdown signal or error
		select {
		case <-sigChan:
			log.Info("Received shutdown signal")
		case err := <-errChan:
			return fmt.Errorf("server error: %w", err)
		}

		// Graceful shutdown
		log.Info("Shutting down server...")
		serverCancel()

		// Give server time to finish requests
		time.Sleep(2 * time.Second)

		log.Info("Server stopped")
		return nil
	},
}

// proxyHealthCmd represents the proxy health command
var proxyHealthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check proxy server health",
	Long: `Check the health status of a running proxy server.

Makes a request to the /health endpoint and displays the status.

Examples:
  # Check health on default port
  control-center proxy health

  # Check health on custom port
  control-center proxy health --port 9000

  # Check remote proxy
  control-center proxy health --host proxy.example.com --port 8080`,
	RunE: func(cmd *cobra.Command, args []string) error {
		url := fmt.Sprintf("http://%s:%d/health", proxyHost, proxyPort)
		
		log.WithField("url", url).Debug("Checking proxy health")
		
		resp, err := http.Get(url)
		if err != nil {
			return fmt.Errorf("failed to connect to proxy: %w", err)
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return fmt.Errorf("failed to read response: %w", err)
		}

		if resp.StatusCode == http.StatusOK {
			fmt.Printf("✅ Proxy is healthy\n")
			fmt.Printf("Status: %d %s\n", resp.StatusCode, resp.Status)
			fmt.Printf("Response: %s\n", string(body))
			return nil
		}

		fmt.Printf("❌ Proxy is unhealthy\n")
		fmt.Printf("Status: %d %s\n", resp.StatusCode, resp.Status)
		fmt.Printf("Response: %s\n", string(body))
		return fmt.Errorf("proxy health check failed")
	},
}

// proxyConfigCmd represents the proxy config command
var proxyConfigCmd = &cobra.Command{
	Use:   "config",
	Short: "Generate sample proxy configuration",
	Long: `Generate a sample proxy configuration file.

The configuration file defines backend providers, routing rules,
authentication, and other proxy settings.

Examples:
  # Print sample config to stdout
  control-center proxy config

  # Save to file
  control-center proxy config --output proxy-config.json

  # Use the config file
  control-center proxy start --config proxy-config.json`,
	RunE: func(cmd *cobra.Command, args []string) error {
		sampleConfig := proxy.Config{
			Port: 8080,
			Host: "0.0.0.0",
			Providers: []proxy.ProviderConfig{
				{
					Name:     "ollama-cloud",
					Type:     "ollama",
					Enabled:  true,
					Priority: 10,
					Config: map[string]interface{}{
						"host":    "https://ollama.com",
						"api_key": "${OLLAMA_API_KEY}",
						"model":   "glm-4.6:cloud",
					},
				},
				{
					Name:     "ollama-local",
					Type:     "ollama",
					Enabled:  true,
					Priority: 5,
					Config: map[string]interface{}{
						"host":  "http://localhost:11434",
						"model": "qwen2.5-coder:7b",
					},
				},
			},
			Routing: proxy.RoutingConfig{
				Strategy: "priority",
				Fallback: true,
			},
		}

		data, err := json.MarshalIndent(sampleConfig, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal config: %w", err)
		}

		if proxyOutputFile != "" {
			if err := os.WriteFile(proxyOutputFile, data, 0644); err != nil {
				return fmt.Errorf("failed to write config file: %w", err)
			}
			fmt.Printf("✅ Sample config written to %s\n", proxyOutputFile)
		} else {
			fmt.Println(string(data))
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(proxyCmd)
	proxyCmd.AddCommand(proxyStartCmd)
	proxyCmd.AddCommand(proxyHealthCmd)
	proxyCmd.AddCommand(proxyConfigCmd)

	// Start command flags
	proxyStartCmd.Flags().IntVar(&proxyPort, "port", 8080, "Port to listen on")
	proxyStartCmd.Flags().StringVar(&proxyHost, "host", "0.0.0.0", "Host to bind to")
	proxyStartCmd.Flags().StringVar(&proxyConfigFile, "config", "", "Configuration file path")

	// Health command flags
	proxyHealthCmd.Flags().IntVar(&proxyPort, "port", 8080, "Proxy server port")
	proxyHealthCmd.Flags().StringVar(&proxyHost, "host", "localhost", "Proxy server host")

	// Config command flags
	proxyConfigCmd.Flags().StringVar(&proxyOutputFile, "output", "", "Output file path")
}

// getEnvOrDefault returns the value of an environment variable or a default value
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
