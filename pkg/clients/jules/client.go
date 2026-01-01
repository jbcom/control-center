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
	host       string
	httpClient *http.Client
}

// Config holds Jules client configuration
type Config struct {
	APIKey string
	Host   string
}

// NewClient creates a new Jules client
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

// Session represents a Jules session
type Session struct {
	Name           string        `json:"name"`
	State          string        `json:"state"`
	Title          string        `json:"title"`
	Prompt         string        `json:"prompt"`
	SourceContext  SourceContext `json:"sourceContext"`
	CreateTime     string        `json:"createTime"`
	UpdateTime     string        `json:"updateTime"`
	PullRequestID  string        `json:"pullRequestId,omitempty"`
	PullRequestURL string        `json:"pullRequestUrl,omitempty"`
}

// SessionState constants
const (
	SessionStateCreated    = "CREATED"
	SessionStateInProgress = "IN_PROGRESS"
	SessionStateCompleted  = "COMPLETED"
	SessionStateFailed     = "FAILED"
	SessionStateCancelled  = "CANCELLED"
	SessionStatePending    = "PENDING_PLAN_APPROVAL"
)

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
	Prompt              string        `json:"prompt"`
	SourceContext       SourceContext `json:"sourceContext"`
	AutomationMode      string        `json:"automationMode"`
	RequirePlanApproval bool          `json:"requirePlanApproval"`
	Title               string        `json:"title,omitempty"`
	// Metadata for PR labels - passed to Jules for PR creation
	Metadata *SessionMetadata `json:"metadata,omitempty"`
}

// SessionMetadata contains additional metadata for the session
type SessionMetadata struct {
	Labels     []string          `json:"labels,omitempty"`
	Properties map[string]string `json:"properties,omitempty"`
}

// CreateSessionOptions provides options for creating a session
type CreateSessionOptions struct {
	Title              string
	Labels             []string
	RequirePlanApproval bool
}

// CreateSession creates a new Jules session with AUTO_CREATE_PR enabled
// IMPORTANT: For Jules to work effectively:
// 1. AGENTS.md in the target repo MUST be up-to-date with goals and current state
// 2. The prompt MUST be clear, unambiguous, and fully communicate context
func (c *Client) CreateSession(ctx context.Context, repo, branch, prompt string) (*Session, error) {
	return c.CreateSessionWithOptions(ctx, repo, branch, prompt, CreateSessionOptions{
		Labels:              []string{"jules-pr", "ai-generated"},
		RequirePlanApproval: false, // Auto-approve plans for automatic PR creation
	})
}

// CreateSessionWithOptions creates a Jules session with custom options
func (c *Client) CreateSessionWithOptions(ctx context.Context, repo, branch, prompt string, opts CreateSessionOptions) (*Session, error) {
	req := CreateSessionRequest{
		Prompt: prompt,
		SourceContext: SourceContext{
			Source: fmt.Sprintf("sources/github/%s", repo),
			GitHubRepoContext: GitHubRepoContext{
				StartingBranch: branch,
			},
		},
		// CRITICAL: AUTO_CREATE_PR ensures Jules creates a PR when work is complete
		AutomationMode: "AUTO_CREATE_PR",
		// CRITICAL: Set to false to skip plan approval - otherwise session waits forever
		RequirePlanApproval: opts.RequirePlanApproval,
		Title:               opts.Title,
	}

	// Add metadata with labels for triage pickup
	if len(opts.Labels) > 0 {
		req.Metadata = &SessionMetadata{
			Labels: opts.Labels,
			Properties: map[string]string{
				"source":     "control-center",
				"repository": repo,
				"branch":     branch,
			},
		}
	}

	log.WithFields(log.Fields{
		"repo":                repo,
		"branch":              branch,
		"automationMode":      req.AutomationMode,
		"requirePlanApproval": req.RequirePlanApproval,
		"labels":              opts.Labels,
	}).Debug("Creating Jules session")

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/v1alpha/sessions", bytes.NewReader(body))
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
	}).Info("Jules session created with AUTO_CREATE_PR")

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
	case SessionStateCompleted, SessionStateFailed, SessionStateCancelled:
		return true
	default:
		return false
	}
}

// IsPendingApproval returns true if the session is waiting for plan approval
func (s *Session) IsPendingApproval() bool {
	return s.State == SessionStatePending
}

// HasPR returns true if the session created a pull request
func (s *Session) HasPR() bool {
	return s.PullRequestID != "" || s.PullRequestURL != ""
}

// GetPRURL returns the pull request URL if available
func (s *Session) GetPRURL() string {
	return s.PullRequestURL
}

// GetSessionID extracts the session ID from the full name
func (s *Session) GetSessionID() string {
	// Name is like "sessions/1234567890"
	if len(s.Name) > 9 && s.Name[:9] == "sessions/" {
		return s.Name[9:]
	}
	return s.Name
}

// GetJulesURL returns the Jules UI URL for this session
func (s *Session) GetJulesURL() string {
	return fmt.Sprintf("https://jules.google.com/session/%s", s.GetSessionID())
}

// WaitForCompletion polls the session until it completes or times out
func (c *Client) WaitForCompletion(ctx context.Context, sessionName string, pollInterval, timeout time.Duration) (*Session, error) {
	deadline := time.Now().Add(timeout)

	for time.Now().Before(deadline) {
		session, err := c.GetSession(ctx, sessionName)
		if err != nil {
			return nil, fmt.Errorf("failed to get session: %w", err)
		}

		log.WithFields(log.Fields{
			"session": sessionName,
			"state":   session.State,
			"hasPR":   session.HasPR(),
		}).Debug("Polling Jules session")

		if session.IsComplete() {
			return session, nil
		}

		// If pending approval and we didn't expect that, auto-approve
		if session.IsPendingApproval() {
			log.WithField("session", sessionName).Warn("Session pending approval - auto-approving")
			if err := c.ApprovePlan(ctx, sessionName); err != nil {
				log.WithError(err).Warn("Failed to auto-approve plan")
			}
		}

		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(pollInterval):
			// Continue polling
		}
	}

	return nil, fmt.Errorf("timeout waiting for session completion")
}

// ListSessionsWithPRs returns only sessions that have created PRs
func (c *Client) ListSessionsWithPRs(ctx context.Context) ([]Session, error) {
	sessions, err := c.ListSessions(ctx)
	if err != nil {
		return nil, err
	}

	var withPRs []Session
	for _, s := range sessions {
		if s.HasPR() {
			withPRs = append(withPRs, s)
		}
	}
	return withPRs, nil
}

// ListOrphanedSessions returns completed sessions without PRs (potential issues)
func (c *Client) ListOrphanedSessions(ctx context.Context) ([]Session, error) {
	sessions, err := c.ListSessions(ctx)
	if err != nil {
		return nil, err
	}

	var orphaned []Session
	for _, s := range sessions {
		if s.IsComplete() && !s.HasPR() && s.State == SessionStateCompleted {
			orphaned = append(orphaned, s)
		}
	}
	return orphaned, nil
}
