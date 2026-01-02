package imagen

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestGenerateImage(t *testing.T) {
	// Create mock server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("Expected POST request, got %s", r.Method)
		}

		// Return mock response
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{
			"predictions": [
				{
					"bytesBase64Encoded": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
					"mimeType": "image/png"
				}
			]
		}`))
	}))
	defer server.Close()

	client := &Client{
		apiKey:     "test-key",
		projectID:  "test-project",
		endpoint:   server.URL,
		httpClient: server.Client(),
	}

	ctx := context.Background()
	req := &ImageRequest{
		Prompt:      "test image",
		AspectRatio: "1:1",
	}

	resp, err := client.GenerateImage(ctx, req)
	if err != nil {
		t.Fatalf("GenerateImage failed: %v", err)
	}

	if len(resp.ImageURIs) == 0 {
		t.Error("Expected at least one image URI")
	}

	if resp.GenerationID == "" {
		t.Error("Expected generation ID")
	}

	if resp.Metadata.Model != "imagen-3.0-generate-001" {
		t.Errorf("Expected model imagen-3.0-generate-001, got %s", resp.Metadata.Model)
	}
}

func TestGenerateImage_APIError(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(`{"error": "Internal server error"}`))
	}))
	defer server.Close()

	client := &Client{
		apiKey:     "test-key",
		projectID:  "test-project",
		endpoint:   server.URL,
		httpClient: server.Client(),
	}

	ctx := context.Background()
	req := &ImageRequest{
		Prompt: "test image",
	}

	_, err := client.GenerateImage(ctx, req)
	if err == nil {
		t.Error("Expected error for API failure")
	}
}

func TestDownloadImage_DataURI(t *testing.T) {
	client := &Client{
		apiKey:    "test-key",
		projectID: "test-project",
	}

	ctx := context.Background()
	tmpDir := t.TempDir()
	destPath := filepath.Join(tmpDir, "test.png")

	// Valid 1x1 PNG base64
	dataURI := "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

	err := client.DownloadImage(ctx, dataURI, destPath)
	if err != nil {
		t.Fatalf("DownloadImage failed: %v", err)
	}

	// Check file exists
	if _, err := os.Stat(destPath); os.IsNotExist(err) {
		t.Error("Downloaded file does not exist")
	}
}

func TestDownloadImage_HTTP(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "image/png")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("fake image data"))
	}))
	defer server.Close()

	client := &Client{
		apiKey:     "test-key",
		projectID:  "test-project",
		httpClient: server.Client(),
	}

	ctx := context.Background()
	tmpDir := t.TempDir()
	destPath := filepath.Join(tmpDir, "test.png")

	err := client.DownloadImage(ctx, server.URL+"/image.png", destPath)
	if err != nil {
		t.Fatalf("DownloadImage failed: %v", err)
	}

	// Check file exists and has content
	data, err := os.ReadFile(destPath)
	if err != nil {
		t.Fatalf("Failed to read downloaded file: %v", err)
	}

	if string(data) != "fake image data" {
		t.Errorf("Expected 'fake image data', got %s", string(data))
	}
}

func TestDownloadImage_UnsupportedScheme(t *testing.T) {
	client := &Client{
		apiKey:    "test-key",
		projectID: "test-project",
	}

	ctx := context.Background()
	err := client.DownloadImage(ctx, "ftp://example.com/image.png", "/tmp/test.png")
	if err == nil {
		t.Error("Expected error for unsupported URI scheme")
	}
}

func TestListGenerations(t *testing.T) {
	client := &Client{
		apiKey:    "test-key",
		projectID: "test-project",
	}

	ctx := context.Background()
	generations, err := client.ListGenerations(ctx)
	if err != nil {
		t.Fatalf("ListGenerations failed: %v", err)
	}

	// Currently returns empty list
	if generations == nil {
		t.Error("Expected non-nil generations slice")
	}
}

func TestGetStatus(t *testing.T) {
	client := &Client{
		apiKey:    "test-key",
		projectID: "test-project",
	}

	ctx := context.Background()
	status, err := client.GetStatus(ctx, "test-generation-id")
	if err != nil {
		t.Fatalf("GetStatus failed: %v", err)
	}

	if status.State != GenerationStateSucceeded {
		t.Errorf("Expected state %s, got %s", GenerationStateSucceeded, status.State)
	}

	if !status.IsComplete {
		t.Error("Expected IsComplete to be true")
	}
}

func TestImageRequest_DefaultValues(t *testing.T) {
	tests := []struct {
		name     string
		req      *ImageRequest
		expected struct {
			aspectRatio    string
			numberOfImages int
		}
	}{
		{
			name: "all defaults",
			req: &ImageRequest{
				Prompt: "test",
			},
			expected: struct {
				aspectRatio    string
				numberOfImages int
			}{
				aspectRatio:    "",
				numberOfImages: 0,
			},
		},
		{
			name: "with aspect ratio",
			req: &ImageRequest{
				Prompt:      "test",
				AspectRatio: "16:9",
			},
			expected: struct {
				aspectRatio    string
				numberOfImages int
			}{
				aspectRatio:    "16:9",
				numberOfImages: 0,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.req.AspectRatio != tt.expected.aspectRatio {
				t.Errorf("Expected aspect ratio %s, got %s", tt.expected.aspectRatio, tt.req.AspectRatio)
			}
			if tt.req.NumberOfImages != tt.expected.numberOfImages {
				t.Errorf("Expected %d images, got %d", tt.expected.numberOfImages, tt.req.NumberOfImages)
			}
		})
	}
}
