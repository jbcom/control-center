package imagen

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

func TestImageRequest_Defaults(t *testing.T) {
	req := &ImageRequest{
		Prompt: "a beautiful sunset",
	}

	if req.Prompt != "a beautiful sunset" {
		t.Errorf("expected prompt 'a beautiful sunset', got %s", req.Prompt)
	}
	if req.AspectRatio != "" {
		t.Errorf("expected empty AspectRatio, got %s", req.AspectRatio)
	}
	if req.NumberOfImages != 0 {
		t.Errorf("expected 0 NumberOfImages, got %d", req.NumberOfImages)
	}
}
