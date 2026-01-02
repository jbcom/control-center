// Package cmd provides the command-line interface for control-center.
package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"

	"github.com/jbcom/control-center/pkg/clients/veo"
)

var (
	veoPrompt       string
	veoDuration     int
	veoAspectRatio  string
	veoResolution   string
	veoFPS          int
	veoOutputDir    string
	veoOutputFormat string
	veoPoll         bool
	veoPollInterval int
)

// veoCmd represents the veo command
var veoCmd = &cobra.Command{
	Use:   "veo",
	Short: "Generate videos with Google Veo 3.1",
	Long: `Generate videos using Google's Veo 3.1 text-to-video model.

Veo 3.1 is Google's advanced video generation model that creates high-quality
videos from text prompts. It supports various resolutions, frame rates, and
aspect ratios.

Examples:
  # Basic video generation
  control-center veo generate "ocean waves crashing on beach"

  # Generate with custom parameters
  control-center veo generate "sunset timelapse" \
    --duration 10 \
    --resolution 1080p \
    --fps 30 \
    --aspect-ratio 16:9

  # Generate and wait for completion
  control-center veo generate "product demo" \
    --poll \
    --output-dir ./videos

  # GitHub Actions integration (JSON output)
  control-center veo generate "tutorial video" --output json`,
}

// veoGenerateCmd represents the veo generate command
var veoGenerateCmd = &cobra.Command{
	Use:   "generate [prompt]",
	Short: "Generate a video from a text prompt",
	Long: `Generate a video from a text prompt using Google Veo 3.1.

The command sends the prompt to the Veo API and returns the generation details.
Use --poll to wait for the generation to complete and auto-download the video.

Supported configurations:
  - Duration: 2-120 seconds (default: 5)
  - Aspect ratios: 16:9, 9:16, 1:1 (default: 16:9)
  - Resolution: 720p, 1080p (default: 1080p)
  - FPS: 24, 30 (default: 30)

Environment variables required:
  - GOOGLE_API_KEY or GOOGLE_CLOUD_API_KEY
  - GOOGLE_PROJECT_ID

Examples:
  # Basic generation
  control-center veo generate "ocean waves"

  # Generate with polling
  control-center veo generate "sunset" --poll --output-dir ./videos

  # Advanced parameters
  control-center veo generate "city timelapse" \
    --duration 10 \
    --resolution 1080p \
    --fps 30 \
    --aspect-ratio 16:9

  # JSON output for CI/CD
  control-center veo generate "demo video" --output json`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		veoPrompt = args[0]

		// Get API credentials from environment
		apiKey := os.Getenv("GOOGLE_API_KEY")
		if apiKey == "" {
			apiKey = os.Getenv("GOOGLE_CLOUD_API_KEY")
		}
		projectID := os.Getenv("GOOGLE_PROJECT_ID")

		if apiKey == "" {
			return fmt.Errorf("GOOGLE_API_KEY or GOOGLE_CLOUD_API_KEY environment variable required")
		}
		if projectID == "" {
			return fmt.Errorf("GOOGLE_PROJECT_ID environment variable required")
		}

		// Create Veo client
		ctx := context.Background()
		client, err := veo.NewClient(ctx, veo.Config{
			APIKey:    apiKey,
			ProjectID: projectID,
		})
		if err != nil {
			return fmt.Errorf("failed to create Veo client: %w", err)
		}

		log.WithFields(log.Fields{
			"prompt":       veoPrompt,
			"duration":     veoDuration,
			"aspect_ratio": veoAspectRatio,
			"resolution":   veoResolution,
			"fps":          veoFPS,
		}).Info("Generating video")

		// Prepare request
		req := &veo.VideoRequest{
			Prompt:      veoPrompt,
			Duration:    veoDuration,
			AspectRatio: veoAspectRatio,
			Resolution:  veoResolution,
			FPS:         veoFPS,
		}

		// Generate video
		resp, err := client.GenerateVideo(ctx, req)
		if err != nil {
			return fmt.Errorf("failed to generate video: %w", err)
		}

		// If polling enabled, wait for completion
		if veoPoll {
			log.Info("Polling for video generation completion...")
			pollInterval := time.Duration(veoPollInterval) * time.Second
			resp, err = client.PollUntilComplete(ctx, resp.GenerationID, pollInterval)
			if err != nil {
				return fmt.Errorf("failed to poll video generation: %w", err)
			}
		}

		// Download videos if output directory specified
		if veoOutputDir != "" && len(resp.VideoURIs) > 0 {
			if err := os.MkdirAll(veoOutputDir, 0755); err != nil {
				return fmt.Errorf("failed to create output directory: %w", err)
			}

			localPaths := []string{}

			for i, uri := range resp.VideoURIs {
				filename := filepath.Join(veoOutputDir, fmt.Sprintf("video_%s_%d.mp4", resp.GenerationID, i))
				log.WithField("uri", uri).Info("Downloading video")
				
				if err := client.DownloadVideo(ctx, uri, filename); err != nil {
					log.WithError(err).Warn("Failed to download video")
					continue
				}
				
				log.WithField("path", filename).Info("Video downloaded")
				localPaths = append(localPaths, filename)
			}

			// Download thumbnails if available
			for i, uri := range resp.ThumbnailURIs {
				filename := filepath.Join(veoOutputDir, fmt.Sprintf("thumbnail_%s_%d.jpg", resp.GenerationID, i))
				log.WithField("uri", uri).Info("Downloading thumbnail")
				
				if err := client.DownloadVideo(ctx, uri, filename); err != nil {
					log.WithError(err).Warn("Failed to download thumbnail")
					continue
				}
				
				log.WithField("path", filename).Info("Thumbnail downloaded")
			}

			// Store local paths in response for JSON output
			if len(localPaths) > 0 {
				resp.Metadata.Model = fmt.Sprintf("local_paths: %v", localPaths)
			}
		}

		// Output response
		if veoOutputFormat == "json" {
			data, err := json.MarshalIndent(resp, "", "  ")
			if err != nil {
				return fmt.Errorf("failed to marshal response: %w", err)
			}
			fmt.Println(string(data))
		} else {
			fmt.Printf("\n✅ Video generation started\n")
			fmt.Printf("Generation ID: %s\n", resp.GenerationID)
			
			if len(resp.VideoURIs) > 0 {
				fmt.Printf("\nVideo URIs (%d):\n", len(resp.VideoURIs))
				for i, uri := range resp.VideoURIs {
					fmt.Printf("  %d. %s\n", i+1, uri)
				}
			}
			
			if resp.Metadata.Prompt != "" {
				fmt.Printf("\nMetadata:\n")
				if data, err := json.MarshalIndent(resp.Metadata, "  ", "  "); err == nil {
					fmt.Printf("  %s\n", string(data))
				}
			}
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(veoCmd)
	veoCmd.AddCommand(veoGenerateCmd)

	// Generate command flags
	veoGenerateCmd.Flags().IntVar(&veoDuration, "duration", 5, "Video duration in seconds (2-120)")
	veoGenerateCmd.Flags().StringVar(&veoAspectRatio, "aspect-ratio", "16:9", "Aspect ratio (16:9, 9:16, 1:1)")
	veoGenerateCmd.Flags().StringVar(&veoResolution, "resolution", "1080p", "Video resolution (720p, 1080p)")
	veoGenerateCmd.Flags().IntVar(&veoFPS, "fps", 30, "Frames per second (24, 30)")
	veoGenerateCmd.Flags().StringVar(&veoOutputDir, "output-dir", "", "Directory to save generated videos")
	veoGenerateCmd.Flags().StringVar(&veoOutputFormat, "output", "text", "Output format (text, json)")
	veoGenerateCmd.Flags().BoolVar(&veoPoll, "poll", false, "Poll until video generation completes")
	veoGenerateCmd.Flags().IntVar(&veoPollInterval, "poll-interval", 5, "Polling interval in seconds")
}
