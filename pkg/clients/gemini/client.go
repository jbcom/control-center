package gemini

import (
	"context"
	"fmt"
	"strings"

	"google.golang.org/genai"
	log "github.com/sirupsen/logrus"
)

const (
	// DefaultModel is the default Gemini model
	DefaultModel = "gemini-2.0-flash"
	
	// Other available models
	ModelGemini15Pro     = "gemini-1.5-pro"
	ModelGemini15Flash   = "gemini-1.5-flash"
	ModelGemini20Flash   = "gemini-2.0-flash"
)

// Client provides access to Google Gemini API
type Client struct {
	apiKey string
	model  string
	client *genai.Client
}

// Config holds Gemini client configuration
type Config struct {
	APIKey string
	Model  string
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

	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	// Create genai client
	client, err := genai.NewClient(ctx, &genai.ClientConfig{
		APIKey: cfg.APIKey,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create genai client: %w", err)
	}

	return &Client{
		apiKey: cfg.APIKey,
		model:  cfg.Model,
		client: client,
	}, nil
}

// Close closes the Gemini client
func (c *Client) Close() error {
	if c.client != nil {
		return c.client.Close()
	}
	return nil
}

// Chat sends a simple chat request with a user prompt
func (c *Client) Chat(ctx context.Context, prompt string) (string, error) {
	return c.ChatWithSystem(ctx, "", prompt)
}

// ChatWithSystem sends a chat request with a system prompt
func (c *Client) ChatWithSystem(ctx context.Context, system, prompt string) (string, error) {
	messages := []Message{}
	
	// Note: Gemini doesn't have explicit system messages in the same way as OpenAI
	// If a system prompt is provided, we'll prepend it to the user message
	if system != "" {
		prompt = fmt.Sprintf("%s\n\n%s", system, prompt)
	}

	messages = append(messages, Message{
		Role:    "user",
		Content: prompt,
	})

	return c.ChatMessages(ctx, messages)
}

// ChatMessages sends a chat request with multiple messages
func (c *Client) ChatMessages(ctx context.Context, messages []Message) (string, error) {
	log.WithFields(log.Fields{
		"model":    c.model,
		"messages": len(messages),
	}).Debug("Sending chat request to Gemini")

	// Convert messages to genai format
	var parts []genai.Part
	for _, msg := range messages {
		parts = append(parts, genai.Text(msg.Content))
	}

	// Get the model
	model := c.client.GenerativeModel(c.model)
	
	// Generate content
	resp, err := model.GenerateContent(ctx, parts...)
	if err != nil {
		return "", fmt.Errorf("failed to generate content: %w", err)
	}

	// Extract text from response
	if len(resp.Candidates) == 0 {
		return "", fmt.Errorf("no candidates in response")
	}

	candidate := resp.Candidates[0]
	if candidate.Content == nil || len(candidate.Content.Parts) == 0 {
		return "", fmt.Errorf("no content in response")
	}

	// Combine all text parts
	var result strings.Builder
	for _, part := range candidate.Content.Parts {
		if text, ok := part.(genai.Text); ok {
			result.WriteString(string(text))
		}
	}

	responseText := result.String()
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

		// Get the model
		model := c.client.GenerativeModel(c.model)
		
		// Generate content stream
		iter := model.GenerateContentStream(ctx, genai.Text(prompt))
		
		for {
			resp, err := iter.Next()
			if err != nil {
				if err.Error() == "iterator done" {
					// Normal completion
					return
				}
				errChan <- fmt.Errorf("stream error: %w", err)
				return
			}

			// Extract text from response chunk
			if len(resp.Candidates) > 0 {
				candidate := resp.Candidates[0]
				if candidate.Content != nil {
					for _, part := range candidate.Content.Parts {
						if text, ok := part.(genai.Text); ok {
							textChan <- string(text)
						}
					}
				}
			}
		}
	}()

	return textChan, errChan
}

// ListModels returns a list of available models
func (c *Client) ListModels(ctx context.Context) ([]string, error) {
	log.Debug("Listing available Gemini models")
	
	// List models using the genai client
	iter := c.client.ListModels(ctx)
	
	var models []string
	for {
		model, err := iter.Next()
		if err != nil {
			if err.Error() == "iterator done" {
				break
			}
			return nil, fmt.Errorf("failed to list models: %w", err)
		}
		models = append(models, model.Name)
	}

	log.WithField("count", len(models)).Debug("Listed Gemini models")
	return models, nil
}
