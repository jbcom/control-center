package jules

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
	// DefaultHost is the Jules API endpoint
	DefaultHost = "https://jules.googleapis.com"
)

// Client provides access to Google Jules API
type Client struct {
	apiKey     string
	projectID  string
	host       string
	httpClient *http.Client
}

// Config holds Jules client configuration
type Config struct {
	APIKey    string
	ProjectID string
	Host      string
}

// NewClient creates a new Jules client
func NewClient(cfg Config) *Client {
	if cfg.Host == "" {
		cfg.Host = DefaultHost
	}

	return &Client{
		apiKey:    cfg.APIKey,
		projectID: cfg.ProjectID,
		host:      cfg.Host,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// Session represents a Jules session
type Session struct {
	Name          string        `json:"name"`
	URL           string        `json:"url"`
	State         string        `json:"state"`
	Title         string        `json:"title"`
	Prompt        string        `json:"prompt"`
	SourceContext SourceContext `json:"sourceContext"`
	CreateTime    string        `json:"createTime"`
	UpdateTime    string        `json:"updateTime"`
	PullRequestID string        `json:"pullRequestId,omitempty"`
}

// SourceContext defines the repository context for a session
type SourceContext struct {
	Source            string            `json:"source"`
	GitHubRepoContext GitHubRepoContext `json:"githubRepoContext"`
}

// GitHubRepoContext holds GitHub-specific context
type GitHubRepoContext struct {
	StartingBranch string `json:"startingBranch"`
}

// CreateSessionRequest is the request to create a Jules session
type CreateSessionRequest struct {
	Prompt         string        `json:"prompt"`
	SourceContext  SourceContext `json:"sourceContext"`
	AutomationMode string        `json:"automationMode"`
	Title          string        `json:"title,omitempty"`
}

// CreateSession creates a new Jules session
func (c *Client) CreateSession(ctx context.Context, repo, branch, prompt string) (*Session, error) {
	if c.projectID == "" {
		return nil, fmt.Errorf("jules ProjectID is required")
	}

	req := CreateSessionRequest{
		Prompt: prompt,
		SourceContext: SourceContext{
			Source: fmt.Sprintf("sources/github/%s", repo),
			GitHubRepoContext: GitHubRepoContext{
				StartingBranch: branch,
			},
		},
		AutomationMode: "AUTO_CREATE_PR",
	}

	log.WithFields(log.Fields{
		"repo":      repo,
		"branch":    branch,
		"projectID": c.projectID,
	}).Debug("Creating Jules session")

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	endpoint := fmt.Sprintf("%s/v1alpha/projects/%s/sessions", c.host, c.projectID)
	httpReq, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("X-Goog-Api-Key", c.apiKey)

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
		return nil, fmt.Errorf("Jules API error %d: %s", resp.StatusCode, string(respBody))
	}

	var session Session
	if err := json.Unmarshal(respBody, &session); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	log.WithFields(log.Fields{
		"session": session.Name,
		"state":   session.State,
	}).Info("Jules session created")

	return &session, nil
}

// GetSession gets a Jules session by name
func (c *Client) GetSession(ctx context.Context, name string) (*Session, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", c.host+"/v1alpha/"+name, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("X-Goog-Api-Key", c.apiKey)

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
		return nil, fmt.Errorf("Jules API error %d: %s", resp.StatusCode, string(respBody))
	}

	var session Session
	if err := json.Unmarshal(respBody, &session); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &session, nil
}

// ListSessions lists Jules sessions
func (c *Client) ListSessions(ctx context.Context) ([]Session, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", c.host+"/v1alpha/sessions", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("X-Goog-Api-Key", c.apiKey)

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
		return nil, fmt.Errorf("Jules API error %d: %s", resp.StatusCode, string(respBody))
	}

	var result struct {
		Sessions []Session `json:"sessions"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return result.Sessions, nil
}

// ApprovePlan approves a pending Jules plan
func (c *Client) ApprovePlan(ctx context.Context, sessionName string) error {
	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/v1alpha/"+sessionName+":approvePlan", nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("X-Goog-Api-Key", c.apiKey)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Jules API error %d: %s", resp.StatusCode, string(respBody))
	}

	log.WithField("session", sessionName).Info("Jules plan approved")
	return nil
}

// IsComplete returns true if the session is in a terminal state
func (s *Session) IsComplete() bool {
	switch s.State {
	case "COMPLETED", "FAILED", "CANCELLED":
		return true
	default:
		return false
	}
}

// HasPR returns true if the session created a pull request
func (s *Session) HasPR() bool {
	return s.PullRequestID != ""
}
