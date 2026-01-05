package gemini

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
)

const (
	// DefaultModel is the default Gemini model
	DefaultModel = "gemini-2.0-flash"
	// DefaultEndpoint is the Gemini API endpoint
	DefaultEndpoint = "https://generativelanguage.googleapis.com/v1beta"

	// Other available models
	ModelGemini15Pro   = "gemini-1.5-pro"
	ModelGemini15Flash = "gemini-1.5-flash"
	ModelGemini20Flash = "gemini-2.0-flash"
)

// Client provides access to Google Gemini API
type Client struct {
	apiKey     string
	model      string
	endpoint   string
	httpClient *http.Client
}

// Config holds Gemini client configuration
type Config struct {
	APIKey   string
	Model    string
	Endpoint string
}

// Message represents a chat message
type Message struct {
	Role    string // "user" or "model"
	Content string
}

// NewClient creates a new Gemini client
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	if cfg.Model == "" {
		cfg.Model = DefaultModel
	}
	if cfg.Endpoint == "" {
		cfg.Endpoint = DefaultEndpoint
	}

	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	return &Client{
		apiKey:   cfg.APIKey,
		model:    cfg.Model,
		endpoint: cfg.Endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second,
		},
	}, nil
}

// Close closes the Gemini client
func (c *Client) Close() error {
	// No-op for HTTP client
	return nil
}

// Chat sends a simple chat request with a user prompt
func (c *Client) Chat(ctx context.Context, prompt string) (string, error) {
	return c.ChatWithSystem(ctx, "", prompt)
}

// ChatWithSystem sends a chat request with a system prompt
func (c *Client) ChatWithSystem(ctx context.Context, system, prompt string) (string, error) {
	// Note: Gemini doesn't have explicit system messages in the same way as OpenAI
	// If a system prompt is provided, we'll prepend it to the user message
	if system != "" {
		prompt = fmt.Sprintf("%s\n\n%s", system, prompt)
	}

	messages := []Message{{
		Role:    "user",
		Content: prompt,
	}}

	return c.ChatMessages(ctx, messages)
}

// generateContentRequest represents the API request format
type generateContentRequest struct {
	Contents         []contentPart      `json:"contents"`
	GenerationConfig *generationConfig  `json:"generationConfig,omitempty"`
	SafetySettings   []safetySetting    `json:"safetySettings,omitempty"`
}

type contentPart struct {
	Role  string `json:"role,omitempty"`
	Parts []part `json:"parts"`
}

type part struct {
	Text string `json:"text"`
}

type generationConfig struct {
	Temperature     float64 `json:"temperature,omitempty"`
	TopK            int     `json:"topK,omitempty"`
	TopP            float64 `json:"topP,omitempty"`
	MaxOutputTokens int     `json:"maxOutputTokens,omitempty"`
}

type safetySetting struct {
	Category  string `json:"category"`
	Threshold string `json:"threshold"`
}

// generateContentResponse represents the API response format
type generateContentResponse struct {
	Candidates []candidate `json:"candidates"`
	Error      *apiError   `json:"error,omitempty"`
}

type candidate struct {
	Content       *contentPart   `json:"content"`
	FinishReason  string         `json:"finishReason"`
	SafetyRatings []safetyRating `json:"safetyRatings"`
}

type safetyRating struct {
	Category    string `json:"category"`
	Probability string `json:"probability"`
}

type apiError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Status  string `json:"status"`
}

// ChatMessages sends a chat request with multiple messages
func (c *Client) ChatMessages(ctx context.Context, messages []Message) (string, error) {
	log.WithFields(log.Fields{
		"model":    c.model,
		"messages": len(messages),
	}).Debug("Sending chat request to Gemini")

	// Convert messages to API format
	var contents []contentPart
	for _, msg := range messages {
		role := msg.Role
		if role == "assistant" {
			role = "model"
		}
		contents = append(contents, contentPart{
			Role:  role,
			Parts: []part{{Text: msg.Content}},
		})
	}

	req := generateContentRequest{
		Contents: contents,
		GenerationConfig: &generationConfig{
			MaxOutputTokens: 8192,
		},
	}

	body, err := json.Marshal(req)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	url := fmt.Sprintf("%s/models/%s:generateContent?key=%s", c.endpoint, c.model, c.apiKey)
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(body))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

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
		return "", fmt.Errorf("API error %d: %s", resp.StatusCode, string(respBody))
	}

	var result generateContentResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	if result.Error != nil {
		return "", fmt.Errorf("API error: %s", result.Error.Message)
	}

	// Extract text from response
	if len(result.Candidates) == 0 {
		return "", fmt.Errorf("no candidates in response")
	}

	candidate := result.Candidates[0]
	if candidate.Content == nil || len(candidate.Content.Parts) == 0 {
		return "", fmt.Errorf("no content in response")
	}

	// Combine all text parts
	var response strings.Builder
	for _, p := range candidate.Content.Parts {
		response.WriteString(p.Text)
	}

	responseText := response.String()
	log.WithField("response_length", len(responseText)).Debug("Received Gemini response")

	return responseText, nil
}

// ChatStream sends a chat request and streams the response
func (c *Client) ChatStream(ctx context.Context, prompt string) (<-chan string, <-chan error) {
	textChan := make(chan string, 10)
	errChan := make(chan error, 1)

	go func() {
		defer close(textChan)
		defer close(errChan)

		log.WithFields(log.Fields{
			"model":  c.model,
			"prompt": len(prompt),
		}).Debug("Starting streaming chat with Gemini")

		// For now, use non-streaming and emit all at once
		// Full streaming would require SSE parsing
		response, err := c.Chat(ctx, prompt)
		if err != nil {
			errChan <- err
			return
		}

		textChan <- response
	}()

	return textChan, errChan
}

// ListModels returns a list of available models
func (c *Client) ListModels(ctx context.Context) ([]string, error) {
	log.Debug("Listing available Gemini models")

	url := fmt.Sprintf("%s/models?key=%s", c.endpoint, c.apiKey)
	httpReq, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

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
		return nil, fmt.Errorf("API error %d: %s", resp.StatusCode, string(respBody))
	}

	var result struct {
		Models []struct {
			Name string `json:"name"`
		} `json:"models"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	var models []string
	for _, m := range result.Models {
		models = append(models, m.Name)
	}

	log.WithField("count", len(models)).Debug("Listed Gemini models")
	return models, nil
}
