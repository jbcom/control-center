package ollama

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
	// DefaultModel is the default Ollama model for cloud
	DefaultModel = "glm-4.6:cloud"

	// DefaultHost is the Ollama cloud API endpoint
	DefaultHost = "https://ollama.com"
)

// Client provides access to Ollama API
type Client struct {
	apiKey     string
	model      string
	host       string
	httpClient *http.Client
}

// Config holds Ollama client configuration
type Config struct {
	APIKey string
	Model  string
	Host   string
}

// NewClient creates a new Ollama client
func NewClient(cfg Config) *Client {
	if cfg.Model == "" {
		cfg.Model = DefaultModel
	}
	if cfg.Host == "" {
		cfg.Host = DefaultHost
	}

	return &Client{
		apiKey: cfg.APIKey,
		model:  cfg.Model,
		host:   cfg.Host,
		httpClient: &http.Client{
			Timeout: 120 * time.Second, // Longer timeout for AI responses
		},
	}
}

// Message represents a chat message
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest represents an Ollama chat request
type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
	Stream   bool      `json:"stream"`
}

// ChatResponse represents an Ollama chat response
type ChatResponse struct {
	Model   string  `json:"model"`
	Message Message `json:"message"`
	Done    bool    `json:"done"`
}

// Chat sends a chat request to Ollama
func (c *Client) Chat(ctx context.Context, prompt string) (string, error) {
	return c.ChatWithSystem(ctx, "", prompt)
}

// ChatWithSystem sends a chat request with a system prompt
func (c *Client) ChatWithSystem(ctx context.Context, system, prompt string) (string, error) {
	messages := []Message{}

	if system != "" {
		messages = append(messages, Message{
			Role:    "system",
			Content: system,
		})
	}

	messages = append(messages, Message{
		Role:    "user",
		Content: prompt,
	})

	return c.ChatMessages(ctx, messages)
}

// ChatMessages sends a chat request with multiple messages
func (c *Client) ChatMessages(ctx context.Context, messages []Message) (string, error) {
	req := ChatRequest{
		Model:    c.model,
		Messages: messages,
		Stream:   false,
	}

	log.WithFields(log.Fields{
		"model":    c.model,
		"messages": len(messages),
	}).Debug("Sending chat request to Ollama")

	body, err := json.Marshal(req)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", c.host+"/api/chat", bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("Ollama API error %d: %s", resp.StatusCode, string(respBody))
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(respBody, &chatResp); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	log.WithField("response_length", len(chatResp.Message.Content)).Debug("Received Ollama response")

	return chatResp.Message.Content, nil
}

// ReviewCode reviews code and returns structured feedback
func (c *Client) ReviewCode(ctx context.Context, diff string) (*CodeReview, error) {
	system := `You are a code reviewer. Analyze the provided diff and return a JSON response with the following structure:
{
  "summary": "Brief 1-2 sentence summary of changes",
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|performance|bug|style|maintainability",
      "message": "Description of the issue",
      "suggestion": "How to fix it"
    }
  ],
  "approval": "approve|request_changes|comment",
  "comments": "Any additional comments"
}

Focus on real issues, not stylistic preferences. Be concise.`

	prompt := fmt.Sprintf("Review this code diff:\n\n```diff\n%s\n```", diff)

	response, err := c.ChatWithSystem(ctx, system, prompt)
	if err != nil {
		return nil, err
	}

	// Parse JSON from response
	var review CodeReview
	if err := json.Unmarshal([]byte(response), &review); err != nil {
		// If JSON parsing fails, return raw response as comment
		return &CodeReview{
			Summary:  "Review completed",
			Approval: "comment",
			Comments: response,
		}, nil
	}

	return &review, nil
}

// CodeReview represents a structured code review
type CodeReview struct {
	Summary  string        `json:"summary"`
	Issues   []ReviewIssue `json:"issues"`
	Approval string        `json:"approval"`
	Comments string        `json:"comments"`
}

// ReviewIssue represents a single issue found during review
type ReviewIssue struct {
	Severity   string `json:"severity"`
	Category   string `json:"category"`
	Message    string `json:"message"`
	Suggestion string `json:"suggestion"`
}

// AnalyzeFailure analyzes a CI failure and suggests fixes
func (c *Client) AnalyzeFailure(ctx context.Context, logContent string) (*FailureAnalysis, error) {
	system := `You are a CI failure analyzer. Analyze the provided failure log and return a JSON response:
{
  "root_cause": "Brief description of the root cause",
  "fix_suggestion": "Specific code or config changes to fix it",
  "verification_commands": ["command1", "command2"],
  "confidence": "high|medium|low"
}

Focus on the actual error, not warnings. Be specific about file paths and line numbers when possible.`

	prompt := fmt.Sprintf("Analyze this CI failure log:\n\n```\n%s\n```", logContent)

	response, err := c.ChatWithSystem(ctx, system, prompt)
	if err != nil {
		return nil, err
	}

	var analysis FailureAnalysis
	if err := json.Unmarshal([]byte(response), &analysis); err != nil {
		return &FailureAnalysis{
			RootCause:     "Analysis completed",
			FixSuggestion: response,
			Confidence:    "medium",
		}, nil
	}

	return &analysis, nil
}

// FailureAnalysis represents analysis of a CI failure
type FailureAnalysis struct {
	RootCause            string   `json:"root_cause"`
	FixSuggestion        string   `json:"fix_suggestion"`
	VerificationCommands []string `json:"verification_commands"`
	Confidence           string   `json:"confidence"`
}

// TriageIssue triages an issue and suggests routing
func (c *Client) TriageIssue(ctx context.Context, title, body string, labels []string) (*IssueTriage, error) {
	system := `You are an issue triage system. Analyze the issue and return a JSON response:
{
  "complexity": "simple|moderate|complex",
  "agent": "ollama|jules|cursor|human",
  "reasoning": "Why this agent was chosen",
  "priority": "critical|high|medium|low",
  "estimated_effort": "minutes|hours|days"
}

Routing guidelines:
- ollama: Quick fixes, single file changes, questions
- jules: Multi-file refactoring, documentation updates
- cursor: Complex debugging, large features, long-running tasks
- human: Product decisions, ambiguous requirements, sensitive changes`

	prompt := fmt.Sprintf("Triage this issue:\n\nTitle: %s\n\nBody:\n%s\n\nLabels: %v", title, body, labels)

	response, err := c.ChatWithSystem(ctx, system, prompt)
	if err != nil {
		return nil, err
	}

	var triage IssueTriage
	if err := json.Unmarshal([]byte(response), &triage); err != nil {
		return &IssueTriage{
			Complexity: "moderate",
			Agent:      "human",
			Reasoning:  response,
			Priority:   "medium",
		}, nil
	}

	return &triage, nil
}

// IssueTriage represents triage decision for an issue
type IssueTriage struct {
	Complexity      string `json:"complexity"`
	Agent           string `json:"agent"`
	Reasoning       string `json:"reasoning"`
	Priority        string `json:"priority"`
	EstimatedEffort string `json:"estimated_effort"`
}
