package veo

import (
	"context"
	"testing"
)

func TestNewClient(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name    string
		cfg     Config
		wantErr bool
	}{
		{
			name: "valid config",
			cfg: Config{
				APIKey:    "test-api-key",
				ProjectID: "test-project",
			},
			wantErr: false,
		},
		{
			name: "missing API key",
			cfg: Config{
				ProjectID: "test-project",
			},
			wantErr: true,
		},
		{
			name: "missing project ID",
			cfg: Config{
				APIKey: "test-api-key",
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			client, err := NewClient(ctx, tt.cfg)
			if (err != nil) != tt.wantErr {
				t.Errorf("NewClient() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && client == nil {
				t.Error("NewClient() returned nil client")
			}
		})
	}
}

func TestVideoRequest_Defaults(t *testing.T) {
	req := &VideoRequest{
		Prompt: "a beautiful cinematic scene",
	}

	if req.Prompt != "a beautiful cinematic scene" {
		t.Errorf("expected prompt 'a beautiful cinematic scene', got %s", req.Prompt)
	}
	if req.Duration != 0 {
		t.Errorf("expected 0 Duration, got %d", req.Duration)
	}
	if req.AspectRatio != "" {
		t.Errorf("expected empty AspectRatio, got %s", req.AspectRatio)
	}
}
