package cursor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	log "github.com/sirupsen/logrus"
)

const (
	// DefaultHost is the Cursor Cloud Agent API endpoint
	DefaultHost = "https://api.cursor.com"
)

// Client provides access to Cursor Cloud Agent API
type Client struct {
	apiKey     string
	host       string
	httpClient *http.Client
}

// Config holds Cursor client configuration
type Config struct {
	APIKey string
	Host   string
}

// NewClient creates a new Cursor client
func NewClient(cfg Config) *Client {
	if cfg.Host == "" {
		cfg.Host = DefaultHost
	}

	return &Client{
		apiKey: cfg.APIKey,
		host:   cfg.Host,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// Agent represents a Cursor Cloud Agent
type Agent struct {
	ID         string    `json:"id"`
	Status     string    `json:"status"`
	Repository string    `json:"repository"`
	Branch     string    `json:"branch"`
	Prompt     string    `json:"prompt"`
	CreatedAt  time.Time `json:"createdAt"`
	UpdatedAt  time.Time `json:"updatedAt"`
}

// LaunchAgentRequest is the request to launch a Cursor agent
type LaunchAgentRequest struct {
	Prompt     PromptConfig `json:"prompt"`
	Source     SourceConfig `json:"source"`
	WaitForPR  bool         `json:"waitForPr,omitempty"`
	Background bool         `json:"background,omitempty"`
}

// PromptConfig holds the agent prompt
type PromptConfig struct {
	Text string `json:"text"`
}

// SourceConfig holds the repository source
type SourceConfig struct {
	Repository string `json:"repository"`
	Branch     string `json:"branch,omitempty"`
}

// LaunchAgent launches a new Cursor Cloud Agent
func (c *Client) LaunchAgent(ctx context.Context, repo, branch, prompt string) (*Agent, error) {
	req := LaunchAgentRequest{
		Prompt: PromptConfig{
			Text: prompt,
		},
		Source: SourceConfig{
			Repository: repo,
			Branch:     branch,
		},
		Background: true,
	}

	log.WithFields(log.Fields{
		"repo":   repo,
		"branch": branch,
	}).Debug("Launching Cursor agent")

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/v0/agents", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(c.apiKey, "")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("Cursor API error %d: %s", resp.StatusCode, string(respBody))
	}

	var agent Agent
	if err := json.Unmarshal(respBody, &agent); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	log.WithFields(log.Fields{
		"agent_id": agent.ID,
		"status":   agent.Status,
	}).Info("Cursor agent launched")

	return &agent, nil
}

// GetAgent gets a Cursor agent by ID
func (c *Client) GetAgent(ctx context.Context, id string) (*Agent, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", c.host+"/v0/agents/"+id, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.SetBasicAuth(c.apiKey, "")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("Cursor API error %d: %s", resp.StatusCode, string(respBody))
	}

	var agent Agent
	if err := json.Unmarshal(respBody, &agent); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &agent, nil
}

// ListAgents lists all Cursor agents
func (c *Client) ListAgents(ctx context.Context) ([]Agent, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", c.host+"/v0/agents", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.SetBasicAuth(c.apiKey, "")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("Cursor API error %d: %s", resp.StatusCode, string(respBody))
	}

	var agents []Agent
	if err := json.Unmarshal(respBody, &agents); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return agents, nil
}

// SendFollowup sends a follow-up message to an agent
func (c *Client) SendFollowup(ctx context.Context, id, message string) error {
	req := struct {
		Message string `json:"message"`
	}{Message: message}

	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/v0/agents/"+id+"/followup", bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.SetBasicAuth(c.apiKey, "")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Cursor API error %d: %s", resp.StatusCode, string(respBody))
	}

	log.WithField("agent_id", id).Info("Follow-up sent to Cursor agent")
	return nil
}

// IsComplete returns true if the agent is in a terminal state
func (a *Agent) IsComplete() bool {
	switch a.Status {
	case "completed", "failed", "cancelled":
		return true
	default:
		return false
	}
}
