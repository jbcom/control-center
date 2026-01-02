package proxy

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/jbcom/control-center/pkg/clients/ollama"
	log "github.com/sirupsen/logrus"
)

// Server represents an LLM proxy server
type Server struct {
	config     *Config
	providers  map[string]Provider
	mu         sync.RWMutex
	httpServer *http.Server
}

// Config holds proxy server configuration
type Config struct {
	Port      int               `json:"port"`
	Host      string            `json:"host"`
	Providers []ProviderConfig  `json:"providers"`
	Routing   RoutingConfig     `json:"routing"`
}

// ProviderConfig defines a backend provider
type ProviderConfig struct {
	Name     string                 `json:"name"`
	Type     string                 `json:"type"` // "ollama", "gemini"
	Enabled  bool                   `json:"enabled"`
	Priority int                    `json:"priority"` // Higher = preferred
	Config   map[string]interface{} `json:"config"`
}

// RoutingConfig defines routing strategy
type RoutingConfig struct {
	Strategy string `json:"strategy"` // "priority", "round-robin", "least-load"
	Fallback bool   `json:"fallback"` // Fallback to next provider on error
}

// Provider interface for backend LLM providers
type Provider interface {
	Name() string
	Type() string
	Chat(ctx context.Context, messages []Message) (string, error)
	IsAvailable(ctx context.Context) bool
}

// Message represents a chat message
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest represents an OpenAI-compatible chat request
type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
	Stream   bool      `json:"stream"`
}

// ChatResponse represents an OpenAI-compatible chat response
type ChatResponse struct {
	ID      string   `json:"id"`
	Object  string   `json:"object"`
	Created int64    `json:"created"`
	Model   string   `json:"model"`
	Choices []Choice `json:"choices"`
	Usage   Usage    `json:"usage"`
}

// Choice represents a completion choice
type Choice struct {
	Index        int     `json:"index"`
	Message      Message `json:"message"`
	FinishReason string  `json:"finish_reason"`
}

// Usage represents token usage
type Usage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// NewServer creates a new proxy server
func NewServer(cfg *Config) (*Server, error) {
	if cfg.Port == 0 {
		cfg.Port = 8080
	}
	if cfg.Host == "" {
		cfg.Host = "0.0.0.0"
	}

	s := &Server{
		config:    cfg,
		providers: make(map[string]Provider),
	}

	// Initialize providers
	for _, providerCfg := range cfg.Providers {
		if !providerCfg.Enabled {
			continue
		}

		provider, err := s.createProvider(providerCfg)
		if err != nil {
			log.WithError(err).Warnf("Failed to create provider %s", providerCfg.Name)
			continue
		}

		s.providers[providerCfg.Name] = provider
		log.WithField("provider", providerCfg.Name).Info("Provider initialized")
	}

	if len(s.providers) == 0 {
		return nil, fmt.Errorf("no providers configured")
	}

	return s, nil
}

func (s *Server) createProvider(cfg ProviderConfig) (Provider, error) {
	switch cfg.Type {
	case "ollama":
		return newOllamaProvider(cfg)
	case "gemini":
		// Gemini provider temporarily disabled due to API compatibility
		log.Warn("Gemini provider is temporarily disabled")
		return nil, fmt.Errorf("gemini provider temporarily disabled")
	default:
		return nil, fmt.Errorf("unknown provider type: %s", cfg.Type)
	}
}

// Start starts the HTTP server
func (s *Server) Start(ctx context.Context) error {
	mux := http.NewServeMux()

	// OpenAI-compatible endpoints
	mux.HandleFunc("/v1/chat/completions", s.handleChatCompletions)
	mux.HandleFunc("/v1/completions", s.handleCompletions)
	mux.HandleFunc("/health", s.handleHealth)

	addr := fmt.Sprintf("%s:%d", s.config.Host, s.config.Port)
	s.httpServer = &http.Server{
		Addr:    addr,
		Handler: mux,
	}

	log.WithField("addr", addr).Info("Starting LLM proxy server")

	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := s.httpServer.Shutdown(shutdownCtx); err != nil {
			log.WithError(err).Error("Server shutdown error")
		}
	}()

	if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return fmt.Errorf("server error: %w", err)
	}

	return nil
}

func (s *Server) handleChatCompletions(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	log.WithFields(log.Fields{
		"model":    req.Model,
		"messages": len(req.Messages),
	}).Debug("Handling chat completion request")

	// Route to provider
	provider := s.selectProvider(req.Model)
	if provider == nil {
		http.Error(w, "No available provider", http.StatusServiceUnavailable)
		return
	}

	// Execute chat
	content, err := provider.Chat(r.Context(), req.Messages)
	if err != nil {
		log.WithError(err).Error("Provider chat failed")
		http.Error(w, fmt.Sprintf("Chat failed: %v", err), http.StatusInternalServerError)
		return
	}

	// Build OpenAI-compatible response
	resp := ChatResponse{
		ID:      fmt.Sprintf("chatcmpl-%d", time.Now().Unix()),
		Object:  "chat.completion",
		Created: time.Now().Unix(),
		Model:   req.Model,
		Choices: []Choice{
			{
				Index: 0,
				Message: Message{
					Role:    "assistant",
					Content: content,
				},
				FinishReason: "stop",
			},
		},
		Usage: Usage{
			PromptTokens:     len(strings.Join(extractContent(req.Messages), " ")) / 4,
			CompletionTokens: len(content) / 4,
			TotalTokens:      (len(strings.Join(extractContent(req.Messages), " ")) + len(content)) / 4,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) handleCompletions(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Use /v1/chat/completions instead", http.StatusNotImplemented)
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	health := map[string]interface{}{
		"status":    "healthy",
		"providers": len(s.providers),
		"timestamp": time.Now().Unix(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

func (s *Server) selectProvider(model string) Provider {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var best Provider
	for _, provider := range s.providers {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		if provider.IsAvailable(ctx) {
			cancel()
			if best == nil {
				best = provider
			}
		} else {
			cancel()
		}
	}

	return best
}

func extractContent(messages []Message) []string {
	content := make([]string, len(messages))
	for i, msg := range messages {
		content[i] = msg.Content
	}
	return content
}

// OllamaProvider wraps Ollama client as a Provider
type OllamaProvider struct {
	name   string
	client *ollama.Client
}

func newOllamaProvider(cfg ProviderConfig) (Provider, error) {
	apiKey := ""
	host := ollama.DefaultHost
	model := ollama.DefaultModel

	if v, ok := cfg.Config["api_key"].(string); ok {
		apiKey = v
	}
	if v, ok := cfg.Config["host"].(string); ok {
		host = v
	}
	if v, ok := cfg.Config["model"].(string); ok {
		model = v
	}

	client := ollama.NewClient(ollama.Config{
		APIKey: apiKey,
		Host:   host,
		Model:  model,
	})

	return &OllamaProvider{
		name:   cfg.Name,
		client: client,
	}, nil
}

func (p *OllamaProvider) Name() string {
	return p.name
}

func (p *OllamaProvider) Type() string {
	return "ollama"
}

func (p *OllamaProvider) Chat(ctx context.Context, messages []Message) (string, error) {
	ollamaMessages := make([]ollama.Message, len(messages))
	for i, msg := range messages {
		ollamaMessages[i] = ollama.Message{
			Role:    msg.Role,
			Content: msg.Content,
		}
	}
	return p.client.ChatMessages(ctx, ollamaMessages)
}

func (p *OllamaProvider) IsAvailable(ctx context.Context) bool {
	_, err := p.client.Chat(ctx, "ping")
	return err == nil
}

// GeminiProvider wraps Gemini client as a Provider
// Temporarily disabled due to API compatibility issues
/*
type GeminiProvider struct {
	name   string
	client *gemini.Client
}

func newGeminiProvider(cfg ProviderConfig) (Provider, error) {
	apiKey := ""
	model := gemini.DefaultModel

	if v, ok := cfg.Config["api_key"].(string); ok {
		apiKey = v
	}
	if v, ok := cfg.Config["model"].(string); ok {
		model = v
	}

	if apiKey == "" {
		return nil, fmt.Errorf("api_key required for gemini provider")
	}

	client, err := gemini.NewClient(context.Background(), gemini.Config{
		APIKey: apiKey,
		Model:  model,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create gemini client: %w", err)
	}

	return &GeminiProvider{
		name:   cfg.Name,
		client: client,
	}, nil
}

func (p *GeminiProvider) Name() string {
	return p.name
}

func (p *GeminiProvider) Type() string {
	return "gemini"
}

func (p *GeminiProvider) Chat(ctx context.Context, messages []Message) (string, error) {
	geminiMessages := make([]gemini.Message, len(messages))
	for i, msg := range messages {
		role := msg.Role
		if role == "system" {
			role = "user"
		}
		geminiMessages[i] = gemini.Message{
			Role:    role,
			Content: msg.Content,
		}
	}
	return p.client.ChatMessages(ctx, geminiMessages)
}

func (p *GeminiProvider) IsAvailable(ctx context.Context) bool {
	_, err := p.client.Chat(ctx, "test")
	return err == nil
}
*/

// LoadConfig loads proxy configuration from a file
func LoadConfig(path string) (*Config, error) {
	file, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var cfg Config
	if err := json.Unmarshal(file, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config: %w", err)
	}

	return &cfg, nil
}
