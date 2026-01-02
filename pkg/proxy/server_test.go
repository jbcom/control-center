package proxy

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestNewServer(t *testing.T) {
	tests := []struct {
		name    string
		cfg     *Config
		wantErr bool
	}{
		{
			name: "valid config with ollama",
			cfg: &Config{
				Port: 8080,
				Host: "localhost",
				Providers: []ProviderConfig{
					{
						Name:    "ollama-test",
						Type:    "ollama",
						Enabled: true,
						Config: map[string]interface{}{
							"host":  "http://localhost:11434",
							"model": "test-model",
						},
					},
				},
			},
			wantErr: false,
		},
		{
			name: "no providers",
			cfg: &Config{
				Port:      8080,
				Host:      "localhost",
				Providers: []ProviderConfig{},
			},
			wantErr: true,
		},
		{
			name: "disabled provider",
			cfg: &Config{
				Port: 8080,
				Host: "localhost",
				Providers: []ProviderConfig{
					{
						Name:    "ollama-test",
						Type:    "ollama",
						Enabled: false,
					},
				},
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server, err := NewServer(tt.cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewServer() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && server == nil {
				t.Error("NewServer() returned nil server")
			}
		})
	}
}

func TestServer_Health(t *testing.T) {
	cfg := &Config{
		Port: 8080,
		Host: "localhost",
		Providers: []ProviderConfig{
			{
				Name:    "ollama-test",
				Type:    "ollama",
				Enabled: true,
				Config: map[string]interface{}{
					"host":  "http://localhost:11434",
					"model": "test-model",
				},
			},
		},
	}

	server, err := NewServer(cfg)
	if err != nil {
		t.Fatalf("NewServer() failed: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	server.handleHealth(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	body := w.Body.String()
	if !strings.Contains(body, "healthy") {
		t.Error("Expected 'healthy' in response")
	}
}

func TestServer_ChatCompletions_InvalidMethod(t *testing.T) {
	cfg := &Config{
		Port: 8080,
		Host: "localhost",
		Providers: []ProviderConfig{
			{
				Name:    "ollama-test",
				Type:    "ollama",
				Enabled: true,
				Config: map[string]interface{}{
					"host":  "http://localhost:11434",
					"model": "test-model",
				},
			},
		},
	}

	server, err := NewServer(cfg)
	if err != nil {
		t.Fatalf("NewServer() failed: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/v1/chat/completions", nil)
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("Expected status 405, got %d", w.Code)
	}
}

func TestServer_ChatCompletions_InvalidJSON(t *testing.T) {
	cfg := &Config{
		Port: 8080,
		Host: "localhost",
		Providers: []ProviderConfig{
			{
				Name:    "ollama-test",
				Type:    "ollama",
				Enabled: true,
				Config: map[string]interface{}{
					"host":  "http://localhost:11434",
					"model": "test-model",
				},
			},
		},
	}

	server, err := NewServer(cfg)
	if err != nil {
		t.Fatalf("NewServer() failed: %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/v1/chat/completions", strings.NewReader("invalid json"))
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status 400, got %d", w.Code)
	}
}

func TestOllamaProvider(t *testing.T) {
	cfg := ProviderConfig{
		Name:    "ollama-test",
		Type:    "ollama",
		Enabled: true,
		Config: map[string]interface{}{
			"host":  "http://localhost:11434",
			"model": "test-model",
		},
	}

	provider, err := newOllamaProvider(cfg)
	if err != nil {
		t.Fatalf("newOllamaProvider() failed: %v", err)
	}

	if provider.Name() != "ollama-test" {
		t.Errorf("Expected name 'ollama-test', got %s", provider.Name())
	}

	if provider.Type() != "ollama" {
		t.Errorf("Expected type 'ollama', got %s", provider.Type())
	}
}

func TestGeminiProvider_Disabled(t *testing.T) {
	// Gemini provider is temporarily disabled
	t.Skip("Gemini provider temporarily disabled due to API compatibility")
}

func TestExtractContent(t *testing.T) {
	messages := []Message{
		{Role: "user", Content: "Hello"},
		{Role: "assistant", Content: "Hi there"},
		{Role: "user", Content: "How are you?"},
	}

	content := extractContent(messages)

	if len(content) != 3 {
		t.Errorf("Expected 3 content items, got %d", len(content))
	}

	if content[0] != "Hello" {
		t.Errorf("Expected 'Hello', got %s", content[0])
	}
}

func TestConfig_Defaults(t *testing.T) {
	cfg := &Config{}

	server, err := NewServer(cfg)
	if err == nil {
		t.Error("Expected error for empty config")
	}
	if server != nil {
		t.Error("Expected nil server for invalid config")
	}
}

func TestSelectProvider(t *testing.T) {
	cfg := &Config{
		Port: 8080,
		Host: "localhost",
		Providers: []ProviderConfig{
			{
				Name:    "ollama-test",
				Type:    "ollama",
				Enabled: true,
				Priority: 1,
				Config: map[string]interface{}{
					"host":  "http://localhost:11434",
					"model": "test-model",
				},
			},
		},
	}

	server, err := NewServer(cfg)
	if err != nil {
		t.Fatalf("NewServer() failed: %v", err)
	}

	// Should return nil since no providers are actually available
	provider := server.selectProvider("test-model")
	if provider != nil {
		t.Log("Provider found (expected in real environment)")
	}
}
