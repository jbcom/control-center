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

// ========================================
// Activity and ChangeSet Types
// ========================================

// Activity represents a Jules session activity
type Activity struct {
	Name             string              `json:"name"`
	CreateTime       string              `json:"createTime"`
	Originator       string              `json:"originator"`
	ID               string              `json:"id"`
	Artifacts        []Artifact          `json:"artifacts,omitempty"`
	ProgressUpdated  *ProgressUpdate     `json:"progressUpdated,omitempty"`
	SessionCompleted *SessionCompletion  `json:"sessionCompleted,omitempty"`
	UserMessage      *UserMessage        `json:"userMessage,omitempty"`
}

// Artifact represents output from an activity
type Artifact struct {
	ChangeSet  *ChangeSet  `json:"changeSet,omitempty"`
	BashOutput *BashOutput `json:"bashOutput,omitempty"`
}

// ChangeSet contains code changes from Jules
type ChangeSet struct {
	Source   string   `json:"source"`
	GitPatch GitPatch `json:"gitPatch"`
}

// GitPatch contains the actual diff
type GitPatch struct {
	UnidiffPatch           string `json:"unidiffPatch"`
	BaseCommitID           string `json:"baseCommitId"`
	SuggestedCommitMessage string `json:"suggestedCommitMessage,omitempty"`
}

// BashOutput contains command execution results
type BashOutput struct {
	Command string `json:"command"`
	Output  string `json:"output"`
}

// ProgressUpdate contains progress information
type ProgressUpdate struct {
	Title       string `json:"title"`
	Description string `json:"description"`
}

// SessionCompletion marks session as completed
type SessionCompletion struct{}

// UserMessage is a message sent to the session
type UserMessage struct {
	Text string `json:"text"`
}

// SessionOutput contains the outputs from a completed session
type SessionOutput struct {
	PullRequest *PullRequestOutput `json:"pullRequest,omitempty"`
}

// PullRequestOutput contains PR information
type PullRequestOutput struct {
	URL         string `json:"url"`
	Title       string `json:"title"`
	Description string `json:"description"`
}

// FullSession includes outputs for completed sessions
type FullSession struct {
	Session
	Outputs []SessionOutput `json:"outputs,omitempty"`
	URL     string          `json:"url,omitempty"`
	ID      string          `json:"id,omitempty"`
}

// GetFullSession gets complete session data including outputs
func (c *Client) GetFullSession(ctx context.Context, name string) (*FullSession, error) {
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

	var session FullSession
	if err := json.Unmarshal(respBody, &session); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &session, nil
}

// GetActivities gets all activities for a session
func (c *Client) GetActivities(ctx context.Context, sessionName string) ([]Activity, error) {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", c.host+"/v1alpha/"+sessionName+"/activities", nil)
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
		Activities []Activity `json:"activities"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return result.Activities, nil
}

// GetLatestChangeSet returns the most recent changeset from a session
func (c *Client) GetLatestChangeSet(ctx context.Context, sessionName string) (*ChangeSet, error) {
	activities, err := c.GetActivities(ctx, sessionName)
	if err != nil {
		return nil, err
	}

	// Walk backwards to find most recent changeset
	for i := len(activities) - 1; i >= 0; i-- {
		for _, artifact := range activities[i].Artifacts {
			if artifact.ChangeSet != nil {
				return artifact.ChangeSet, nil
			}
		}
	}

	return nil, fmt.Errorf("no changeset found in session activities")
}

// SendMessage sends a user message to an active session
func (c *Client) SendMessage(ctx context.Context, sessionName, message string) error {
	body, err := json.Marshal(map[string]interface{}{
		"userMessage": map[string]string{
			"text": message,
		},
	})
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/v1alpha/"+sessionName+"/activities", bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
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

	log.WithField("session", sessionName).Info("Message sent to Jules session")
	return nil
}

// GetPRURL returns the PR URL from a full session (checks outputs)
func (s *FullSession) GetPRURL() string {
	// First check the direct field
	if s.PullRequestURL != "" {
		return s.PullRequestURL
	}
	// Check outputs
	for _, output := range s.Outputs {
		if output.PullRequest != nil && output.PullRequest.URL != "" {
			return output.PullRequest.URL
		}
	}
	return ""
}

// ListFullSessions lists all sessions with full output data
func (c *Client) ListFullSessions(ctx context.Context) ([]FullSession, error) {
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
		Sessions []FullSession `json:"sessions"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return result.Sessions, nil
}

// ========================================
// GitHub Actions Output Helpers
// ========================================

// GitHubActionsOutput formats session data for GitHub Actions
type GitHubActionsOutput struct {
	SessionID      string `json:"session_id"`
	SessionURL     string `json:"session_url"`
	State          string `json:"state"`
	HasPR          bool   `json:"has_pr"`
	PRURL          string `json:"pr_url,omitempty"`
	HasChangeSet   bool   `json:"has_changeset"`
	Patch          string `json:"patch,omitempty"`
	CommitMessage  string `json:"commit_message,omitempty"`
	BaseCommit     string `json:"base_commit,omitempty"`
	TargetRepo     string `json:"target_repo,omitempty"`
	TargetBranch   string `json:"target_branch,omitempty"`
}

// ToGitHubActionsOutput converts session data for workflow consumption
func (c *Client) ToGitHubActionsOutput(ctx context.Context, sessionName string) (*GitHubActionsOutput, error) {
	session, err := c.GetFullSession(ctx, sessionName)
	if err != nil {
		return nil, err
	}

	output := &GitHubActionsOutput{
		SessionID:    session.GetSessionID(),
		SessionURL:   session.GetJulesURL(),
		State:        session.State,
		HasPR:        session.GetPRURL() != "",
		PRURL:        session.GetPRURL(),
		TargetBranch: session.SourceContext.GitHubRepoContext.StartingBranch,
	}

	// Extract repo from source
	if len(session.SourceContext.Source) > 15 { // "sources/github/"
		output.TargetRepo = session.SourceContext.Source[15:]
	}

	// Try to get changeset
	changeSet, err := c.GetLatestChangeSet(ctx, sessionName)
	if err == nil && changeSet != nil {
		output.HasChangeSet = true
		output.Patch = changeSet.GitPatch.UnidiffPatch
		output.CommitMessage = changeSet.GitPatch.SuggestedCommitMessage
		output.BaseCommit = changeSet.GitPatch.BaseCommitID
	}

	return output, nil
}

// PrintGitHubActionsOutputs prints outputs in GitHub Actions format
func (o *GitHubActionsOutput) PrintGitHubActionsOutputs() {
	fmt.Printf("::set-output name=session_id::%s\n", o.SessionID)
	fmt.Printf("::set-output name=session_url::%s\n", o.SessionURL)
	fmt.Printf("::set-output name=state::%s\n", o.State)
	fmt.Printf("::set-output name=has_pr::%t\n", o.HasPR)
	if o.PRURL != "" {
		fmt.Printf("::set-output name=pr_url::%s\n", o.PRURL)
	}
	fmt.Printf("::set-output name=has_changeset::%t\n", o.HasChangeSet)
	if o.TargetRepo != "" {
		fmt.Printf("::set-output name=target_repo::%s\n", o.TargetRepo)
	}
	if o.TargetBranch != "" {
		fmt.Printf("::set-output name=target_branch::%s\n", o.TargetBranch)
	}
	if o.BaseCommit != "" {
		fmt.Printf("::set-output name=base_commit::%s\n", o.BaseCommit)
	}
}

// PrintGitHubEnvOutputs prints outputs using GITHUB_OUTPUT file format (new style)
func (o *GitHubActionsOutput) PrintGitHubEnvOutputs() {
	fmt.Printf("session_id=%s\n", o.SessionID)
	fmt.Printf("session_url=%s\n", o.SessionURL)
	fmt.Printf("state=%s\n", o.State)
	fmt.Printf("has_pr=%t\n", o.HasPR)
	if o.PRURL != "" {
		fmt.Printf("pr_url=%s\n", o.PRURL)
	}
	fmt.Printf("has_changeset=%t\n", o.HasChangeSet)
	if o.TargetRepo != "" {
		fmt.Printf("target_repo=%s\n", o.TargetRepo)
	}
	if o.TargetBranch != "" {
		fmt.Printf("target_branch=%s\n", o.TargetBranch)
	}
	if o.BaseCommit != "" {
		fmt.Printf("base_commit=%s\n", o.BaseCommit)
	}
}
