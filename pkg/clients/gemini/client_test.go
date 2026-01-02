package gemini

import (
	"context"
	"testing"
)

func TestNewClient(t *testing.T) {
	tests := []struct {
		name    string
		config  Config
		wantErr bool
	}{
		{
			name: "valid config",
			config: Config{
				APIKey: "test-key",
				Model:  ModelGemini20Flash,
			},
			wantErr: false,
		},
		{
			name: "missing api key",
			config: Config{
				Model: ModelGemini20Flash,
			},
			wantErr: true,
		},
		{
			name: "default model",
			config: Config{
				APIKey: "test-key",
			},
			wantErr: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ctx := context.Background()
			client, err := NewClient(ctx, tt.config)
			
			if (err != nil) != tt.wantErr {
				t.Errorf("NewClient() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			
			if !tt.wantErr {
				if client == nil {
					t.Error("NewClient() returned nil client")
					return
				}
				
				// Verify default model is set
				if tt.config.Model == "" && client.model != DefaultModel {
					t.Errorf("Expected default model %s, got %s", DefaultModel, client.model)
				}
				
				// Clean up
				if err := client.Close(); err != nil {
					t.Errorf("Failed to close client: %v", err)
				}
			}
		})
	}
}

func TestMessage(t *testing.T) {
	msg := Message{
		Role:    "user",
		Content: "Hello, Gemini!",
	}

	if msg.Role != "user" {
		t.Errorf("Expected role 'user', got '%s'", msg.Role)
	}

	if msg.Content != "Hello, Gemini!" {
		t.Errorf("Expected content 'Hello, Gemini!', got '%s'", msg.Content)
	}
}
