package veo

import (
	"context"
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
	// DefaultEndpoint is the default Vertex AI Veo endpoint
	DefaultEndpoint = "https://us-central1-aiplatform.googleapis.com/v1"

	// GenerationStatePending means generation is queued
	GenerationStatePending = "PENDING"
	// GenerationStateRunning means generation is in progress
	GenerationStateRunning = "RUNNING"
	// GenerationStateSucceeded means generation completed successfully
	GenerationStateSucceeded = "SUCCEEDED"
	// GenerationStateFailed means generation failed
	GenerationStateFailed = "FAILED"

	// DefaultPollInterval is the default interval for polling job status
	DefaultPollInterval = 10 * time.Second
)

// Client provides access to Google Veo 3.1 API
type Client struct {
	apiKey     string
	projectID  string
	endpoint   string
	httpClient *http.Client
}

// Config holds Veo client configuration
type Config struct {
	APIKey    string
	ProjectID string
	Endpoint  string
}

// VideoRequest represents a request to generate a video
type VideoRequest struct {
	Prompt      string `json:"prompt"`
	Duration    int    `json:"duration,omitempty"`    // Duration in seconds (2-120)
	AspectRatio string `json:"aspectRatio,omitempty"` // "16:9", "9:16", "1:1"
	Resolution  string `json:"resolution,omitempty"`  // "720p", "1080p"
	FPS         int    `json:"fps,omitempty"`         // Frames per second (24, 30)
}

// VideoResponse represents the response from video generation
type VideoResponse struct {
	GenerationID  string        `json:"generationId"`
	VideoURIs     []string      `json:"videoUris"`
	ThumbnailURIs []string      `json:"thumbnailUris,omitempty"`
	Metadata      VideoMetadata `json:"metadata,omitempty"`
}

// VideoMetadata contains additional information about the generation
type VideoMetadata struct {
	Prompt      string    `json:"prompt"`
	Duration    int       `json:"duration"`
	AspectRatio string    `json:"aspectRatio"`
	Resolution  string    `json:"resolution"`
	FPS         int       `json:"fps"`
	GeneratedAt time.Time `json:"generatedAt"`
	Model       string    `json:"model"`
}

// Generation represents a video generation job
type Generation struct {
	ID                  string     `json:"id"`
	Status              string     `json:"status"`
	Prompt              string     `json:"prompt"`
	CreatedAt           time.Time  `json:"createdAt"`
	EstimatedCompletion *time.Time `json:"estimatedCompletion,omitempty"`
	CompletedAt         *time.Time `json:"completedAt,omitempty"`
	VideoURIs           []string   `json:"videoUris,omitempty"`
	Error               string     `json:"error,omitempty"`
}

// GenerationStatus represents the status of a generation job
type GenerationStatus struct {
	State                  string `json:"state"` // PENDING, RUNNING, SUCCEEDED, FAILED
	Progress               int    `json:"progress"` // 0-100
	Error                  string `json:"error,omitempty"`
	Retryable              bool   `json:"retryable"`
	EstimatedTimeRemaining string `json:"estimatedTimeRemaining,omitempty"`
	IsComplete             bool   `json:"isComplete"`
}

// NewClient creates a new Veo client
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
			Timeout: 300 * time.Second, // 5 minutes for video generation
		},
	}, nil
}

// GenerateVideo generates a video from a text prompt
func (c *Client) GenerateVideo(ctx context.Context, req *VideoRequest) (*VideoResponse, error) {
	log.WithFields(log.Fields{
		"prompt":      req.Prompt,
		"duration":    req.Duration,
		"aspectRatio": req.AspectRatio,
		"resolution":  req.Resolution,
	}).Debug("Generating video with Veo 3.1")

	// Set defaults
	if req.Duration == 0 {
		req.Duration = 5 // Default 5 seconds
	}
	if req.AspectRatio == "" {
		req.AspectRatio = "16:9"
	}
	if req.Resolution == "" {
		req.Resolution = "1080p"
	}
	if req.FPS == 0 {
		req.FPS = 30
	}

	// Build request
	url := fmt.Sprintf("%s/projects/%s/locations/us-central1/publishers/google/models/veo-3.1:predict",
		c.endpoint, c.projectID)

	payload := map[string]interface{}{
		"instances": []map[string]interface{}{
			{
				"prompt": req.Prompt,
			},
		},
		"parameters": map[string]interface{}{
			"duration":    req.Duration,
			"aspectRatio": req.AspectRatio,
			"resolution":  req.Resolution,
			"fps":         req.FPS,
		},
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
		return nil, fmt.Errorf("Veo API error %d: %s", resp.StatusCode, string(respBody))
	}

	// Parse response
	var apiResp struct {
		Predictions []struct {
			VideoURI     string `json:"videoUri"`
			ThumbnailURI string `json:"thumbnailUri"`
		} `json:"predictions"`
		Metadata struct {
			GenerationTime float64 `json:"generationTime"`
		} `json:"metadata"`
	}

	if err := json.Unmarshal(respBody, &apiResp); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	// Extract video URIs
	videoURIs := make([]string, len(apiResp.Predictions))
	thumbnailURIs := make([]string, len(apiResp.Predictions))
	for i, pred := range apiResp.Predictions {
		videoURIs[i] = pred.VideoURI
		thumbnailURIs[i] = pred.ThumbnailURI
	}

	result := &VideoResponse{
		GenerationID:  fmt.Sprintf("veo-%d", time.Now().Unix()),
		VideoURIs:     videoURIs,
		ThumbnailURIs: thumbnailURIs,
		Metadata: VideoMetadata{
			Prompt:      req.Prompt,
			Duration:    req.Duration,
			AspectRatio: req.AspectRatio,
			Resolution:  req.Resolution,
			FPS:         req.FPS,
			GeneratedAt: time.Now(),
			Model:       "veo-3.1",
		},
	}

	log.WithField("videoCount", len(videoURIs)).Debug("Video generation complete")

	return result, nil
}

// DownloadVideo downloads a video from a URI to a local path
func (c *Client) DownloadVideo(ctx context.Context, videoURI, destPath string) error {
	log.WithFields(log.Fields{
		"uri":      videoURI,
		"destPath": destPath,
	}).Debug("Downloading video")

	// Handle HTTP(S) URIs
	if strings.HasPrefix(videoURI, "http://") || strings.HasPrefix(videoURI, "https://") {
		return c.downloadHTTPURI(ctx, videoURI, destPath)
	}

	// Handle GCS URIs
	if strings.HasPrefix(videoURI, "gs://") {
		return fmt.Errorf("GCS URI download not yet implemented: %s", videoURI)
	}

	return fmt.Errorf("unsupported URI scheme: %s", videoURI)
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

	// Copy content with progress
	written, err := io.Copy(file, resp.Body)
	if err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	log.WithFields(log.Fields{
		"path": destPath,
		"size": written,
	}).Info("Video downloaded")

	return nil
}

// ListGenerations lists recent video generations
// Note: This is a minimal implementation that returns an empty list.
// In a production system, this would query a persistence layer (database, Cloud Storage)
// or the Vertex AI API to retrieve historical generation jobs.
func (c *Client) ListGenerations(ctx context.Context) ([]*Generation, error) {
	log.Debug("Listing video generations")

	// Return empty list as this requires persistence layer integration
	// Callers should track generations locally or implement persistence
	return []*Generation{}, nil
}

// GetStatus gets the status of a generation job
// Note: This is a minimal implementation that assumes immediate completion.
// In a production system, this would query the actual job status from the
// Vertex AI API using the Long Running Operations API or similar async job tracking.
func (c *Client) GetStatus(ctx context.Context, generationID string) (*GenerationStatus, error) {
	log.WithField("generationID", generationID).Debug("Getting generation status")

	// For async video generation, implement LRO (Long Running Operations) API polling
	// This minimal implementation assumes synchronous completion for testing purposes
	return &GenerationStatus{
		State:      GenerationStateSucceeded,
		Progress:   100,
		IsComplete: true,
		Retryable:  false,
	}, nil
}

// PollUntilComplete polls the generation job until it completes or fails
func (c *Client) PollUntilComplete(ctx context.Context, generationID string, pollInterval time.Duration) (*VideoResponse, error) {
	if pollInterval == 0 {
		pollInterval = DefaultPollInterval
	}

	log.WithFields(log.Fields{
		"generationID": generationID,
		"interval":     pollInterval,
	}).Debug("Starting to poll generation status")

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-ticker.C:
			status, err := c.GetStatus(ctx, generationID)
			if err != nil {
				return nil, fmt.Errorf("failed to get status: %w", err)
			}

			log.WithFields(log.Fields{
				"state":    status.State,
				"progress": status.Progress,
			}).Debug("Generation status update")

			if status.IsComplete {
				if status.State == GenerationStateSucceeded {
					// In a real implementation, fetch the actual result
					// For now, return a placeholder
					return &VideoResponse{
						GenerationID: generationID,
						VideoURIs:    []string{},
					}, nil
				}
				return nil, fmt.Errorf("generation failed: %s", status.Error)
			}
		}
	}
}
