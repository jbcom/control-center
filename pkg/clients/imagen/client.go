package imagen

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
)

const (
	// DefaultEndpoint is the default Vertex AI Imagen endpoint
	DefaultEndpoint = "https://us-central1-aiplatform.googleapis.com/v1"
	
	// GenerationStatePending means generation is queued
	GenerationStatePending = "PENDING"
	// GenerationStateRunning means generation is in progress
	GenerationStateRunning = "RUNNING"
	// GenerationStateSucceeded means generation completed successfully
	GenerationStateSucceeded = "SUCCEEDED"
	// GenerationStateFailed means generation failed
	GenerationStateFailed = "FAILED"
)

// Client provides access to Google Imagen 3 API
type Client struct {
	apiKey     string
	projectID  string
	endpoint   string
	httpClient *http.Client
}

// Config holds Imagen client configuration
type Config struct {
	APIKey    string
	ProjectID string
	Endpoint  string
}

// ImageRequest represents a request to generate an image
type ImageRequest struct {
	Prompt         string   `json:"prompt"`
	AspectRatio    string   `json:"aspectRatio,omitempty"` // "1:1", "16:9", "9:16", "4:3", "3:4"
	NegativePrompt string   `json:"negativePrompt,omitempty"`
	NumberOfImages int      `json:"numberOfImages,omitempty"` // Default: 1, Max: 4
	SafetySettings []string `json:"safetySettings,omitempty"`
}

// ImageResponse represents the response from image generation
type ImageResponse struct {
	GenerationID   string          `json:"generationId"`
	ImageURIs      []string        `json:"imageUris"`
	SafetyRatings  []SafetyRating  `json:"safetyRatings,omitempty"`
	Metadata       Metadata        `json:"metadata,omitempty"`
}

// SafetyRating represents safety assessment of generated content
type SafetyRating struct {
	Category string  `json:"category"`
	Blocked  bool    `json:"blocked"`
	Score    float64 `json:"score"`
}

// Metadata contains additional information about the generation
type Metadata struct {
	Prompt      string    `json:"prompt"`
	AspectRatio string    `json:"aspectRatio"`
	GeneratedAt time.Time `json:"generatedAt"`
	Model       string    `json:"model"`
}

// Generation represents a generation job
type Generation struct {
	ID          string     `json:"id"`
	Status      string     `json:"status"`
	Prompt      string     `json:"prompt"`
	CreatedAt   time.Time  `json:"createdAt"`
	CompletedAt *time.Time `json:"completedAt,omitempty"`
	ImageURIs   []string   `json:"imageUris,omitempty"`
	Error       string     `json:"error,omitempty"`
}

// GenerationStatus represents the status of a generation job
type GenerationStatus struct {
	State      string `json:"state"` // PENDING, RUNNING, SUCCEEDED, FAILED
	Progress   int    `json:"progress"` // 0-100
	Error      string `json:"error,omitempty"`
	IsComplete bool   `json:"isComplete"`
}

// NewClient creates a new Imagen client
func NewClient(ctx context.Context, cfg Config) (*Client, error) {
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is required")
	}

	if cfg.ProjectID == "" {
		return nil, fmt.Errorf("project ID is required")
	}

	if cfg.Endpoint == "" {
		cfg.Endpoint = DefaultEndpoint
	}

	return &Client{
		apiKey:    cfg.APIKey,
		projectID: cfg.ProjectID,
		endpoint:  cfg.Endpoint,
		httpClient: &http.Client{
			Timeout: 120 * time.Second,
		},
	}, nil
}

// GenerateImage generates images from a text prompt
func (c *Client) GenerateImage(ctx context.Context, req *ImageRequest) (*ImageResponse, error) {
	log.WithFields(log.Fields{
		"prompt":         req.Prompt,
		"aspectRatio":    req.AspectRatio,
		"numberOfImages": req.NumberOfImages,
	}).Debug("Generating image with Imagen 3")

	// Set defaults
	if req.NumberOfImages == 0 {
		req.NumberOfImages = 1
	}
	if req.AspectRatio == "" {
		req.AspectRatio = "1:1"
	}

	// Build request
	url := fmt.Sprintf("%s/projects/%s/locations/us-central1/publishers/google/models/imagen-3.0-generate-001:predict",
		c.endpoint, c.projectID)

	payload := map[string]interface{}{
		"instances": []map[string]interface{}{
			{
				"prompt": req.Prompt,
			},
		},
		"parameters": map[string]interface{}{
			"sampleCount": req.NumberOfImages,
			"aspectRatio": req.AspectRatio,
		},
	}

	if req.NegativePrompt != "" {
		payload["parameters"].(map[string]interface{})["negativePrompt"] = req.NegativePrompt
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, strings.NewReader(string(body)))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)

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
		return nil, fmt.Errorf("Imagen API error %d: %s", resp.StatusCode, string(respBody))
	}

	// Parse response
	var apiResp struct {
		Predictions []struct {
			BytesBase64Encoded string `json:"bytesBase64Encoded"`
			MimeType           string `json:"mimeType"`
		} `json:"predictions"`
		Metadata struct {
			TokenMetadata struct {
				OutputImageTokenCount int `json:"outputImageTokenCount"`
			} `json:"tokenMetadata"`
		} `json:"metadata"`
	}

	if err := json.Unmarshal(respBody, &apiResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	// Convert base64 images to URIs (in real implementation, would save to GCS or similar)
	imageURIs := make([]string, len(apiResp.Predictions))
	for i, pred := range apiResp.Predictions {
		// For now, return data URIs (in production, upload to storage)
		imageURIs[i] = fmt.Sprintf("data:%s;base64,%s", pred.MimeType, pred.BytesBase64Encoded)
	}

	result := &ImageResponse{
		GenerationID: fmt.Sprintf("gen-%d", time.Now().Unix()),
		ImageURIs:    imageURIs,
		Metadata: Metadata{
			Prompt:      req.Prompt,
			AspectRatio: req.AspectRatio,
			GeneratedAt: time.Now(),
			Model:       "imagen-3.0-generate-001",
		},
	}

	log.WithField("imageCount", len(imageURIs)).Debug("Image generation complete")

	return result, nil
}

// DownloadImage downloads an image from a URI to a local path
func (c *Client) DownloadImage(ctx context.Context, imageURI, destPath string) error {
	log.WithFields(log.Fields{
		"uri":      imageURI,
		"destPath": destPath,
	}).Debug("Downloading image")

	// Handle data URIs (base64 encoded)
	if strings.HasPrefix(imageURI, "data:") {
		return c.downloadDataURI(imageURI, destPath)
	}

	// Handle HTTP(S) URIs
	if strings.HasPrefix(imageURI, "http://") || strings.HasPrefix(imageURI, "https://") {
		return c.downloadHTTPURI(ctx, imageURI, destPath)
	}

	// Handle GCS URIs
	if strings.HasPrefix(imageURI, "gs://") {
		return fmt.Errorf("GCS URI download not yet implemented: %s", imageURI)
	}

	return fmt.Errorf("unsupported URI scheme: %s", imageURI)
}

func (c *Client) downloadDataURI(dataURI, destPath string) error {
	// Parse data URI: data:[<mediatype>][;base64],<data>
	parts := strings.SplitN(dataURI, ",", 2)
	if len(parts) != 2 {
		return fmt.Errorf("invalid data URI format")
	}

	// Decode base64
	data, err := base64.StdEncoding.DecodeString(parts[1])
	if err != nil {
		return fmt.Errorf("failed to decode base64: %w", err)
	}

	// Create parent directory if it doesn't exist
	dir := filepath.Dir(destPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Write to file
	if err := os.WriteFile(destPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	log.WithField("path", destPath).Info("Image saved")
	return nil
}

func (c *Client) downloadHTTPURI(ctx context.Context, uri, destPath string) error {
	req, err := http.NewRequestWithContext(ctx, "GET", uri, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to download: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("download failed with status %d", resp.StatusCode)
	}

	// Create parent directory
	dir := filepath.Dir(destPath)
	if mkdirErr := os.MkdirAll(dir, 0755); mkdirErr != nil {
		return fmt.Errorf("failed to create directory: %w", mkdirErr)
	}

	// Create file
	file, err := os.Create(destPath)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	// Copy content
	if _, err := io.Copy(file, resp.Body); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	log.WithField("path", destPath).Info("Image downloaded")
	return nil
}

// ListGenerations lists recent image generations
// Note: This is a minimal implementation that returns an empty list.
// In a production system, this would query a persistence layer (database, Cloud Storage)
// or the Vertex AI API to retrieve historical generation jobs.
func (c *Client) ListGenerations(ctx context.Context) ([]*Generation, error) {
	log.Debug("Listing image generations")

	// Return empty list as this requires persistence layer integration
	// Callers should track generations locally or implement persistence
	return []*Generation{}, nil
}

// GetStatus gets the status of a generation job
// Note: This is a minimal implementation that assumes immediate completion.
// In a production system with async generation, this would query the actual job status
// from the Vertex AI API using the Long Running Operations API.
func (c *Client) GetStatus(ctx context.Context, generationID string) (*GenerationStatus, error) {
	log.WithField("generationID", generationID).Debug("Getting generation status")

	// Since Imagen 3 typically completes synchronously, assume success
	// For async operations, implement LRO (Long Running Operations) API polling
	return &GenerationStatus{
		State:      GenerationStateSucceeded,
		Progress:   100,
		IsComplete: true,
	}, nil
}
