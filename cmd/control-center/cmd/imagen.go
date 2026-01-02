package cmd

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/jbcom/control-center/pkg/clients/imagen"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	imagenProjectID      string
	imagenAspectRatio    string
	imagenNegativePrompt string
	imagenNumberOfImages int
	imagenOutputDir      string
	imagenOutputJSON     bool
)

// imagenCmd represents the imagen command
var imagenCmd = &cobra.Command{
	Use:   "imagen",
	Short: "Generate images with Google Imagen 3",
	Long: `Generate high-quality images using Google Imagen 3 API.

The imagen command provides subcommands for:
  - generate: Generate images from text prompts
  - download: Download generated images
  - list: List recent generations
  - status: Check generation status

Examples:
  # Generate a single image
  control-center imagen generate "a beautiful sunset over mountains"

  # Generate multiple images with specific aspect ratio
  control-center imagen generate "cyberpunk city" --aspect-ratio 16:9 --count 4

  # Generate with negative prompt
  control-center imagen generate "a cat" --negative "blurry, low quality"

  # Output as JSON for GitHub Actions
  control-center imagen generate "logo design" --output json

Configuration:
  Set GOOGLE_API_KEY or GOOGLE_CLOUD_API_KEY environment variable with your API key.
  Set GOOGLE_PROJECT_ID environment variable with your GCP project ID.
  Get an API key from https://console.cloud.google.com/apis/credentials`,
}

// imagenGenerateCmd represents the imagen generate command
var imagenGenerateCmd = &cobra.Command{
	Use:   "generate [prompt]",
	Short: "Generate images from a text prompt",
	Long: `Generate one or more images from a text prompt using Imagen 3.

Examples:
  # Single image, 1:1 aspect ratio
  control-center imagen generate "a serene lake at dawn"

  # Widescreen images
  control-center imagen generate "cinematic landscape" --aspect-ratio 16:9

  # Multiple images with negative prompt
  control-center imagen generate "fantasy castle" --count 3 --negative "modern, urban"

  # Save to specific directory
  control-center imagen generate "abstract art" --output-dir ./images

  # JSON output for workflows
  control-center imagen generate "logo" --output json`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ctx := context.Background()
		prompt := args[0]

		// Get API key from environment
		apiKey := viper.GetString("GOOGLE_API_KEY")
		if apiKey == "" {
			apiKey = viper.GetString("GOOGLE_CLOUD_API_KEY")
		}
		if apiKey == "" {
			apiKey = os.Getenv("GOOGLE_API_KEY")
		}
		if apiKey == "" {
			apiKey = os.Getenv("GOOGLE_CLOUD_API_KEY")
		}

		if apiKey == "" {
			return fmt.Errorf("GOOGLE_API_KEY or GOOGLE_CLOUD_API_KEY environment variable is required")
		}

		// Get project ID
		projectID := imagenProjectID
		if projectID == "" {
			projectID = viper.GetString("GOOGLE_PROJECT_ID")
		}
		if projectID == "" {
			projectID = os.Getenv("GOOGLE_PROJECT_ID")
		}

		if projectID == "" {
			return fmt.Errorf("GOOGLE_PROJECT_ID environment variable or --project-id flag is required")
		}

		// Create Imagen client
		client, err := imagen.NewClient(ctx, imagen.Config{
			APIKey:    apiKey,
			ProjectID: projectID,
		})
		if err != nil {
			return fmt.Errorf("failed to create Imagen client: %w", err)
		}

		// Prepare request
		req := &imagen.ImageRequest{
			Prompt:         prompt,
			AspectRatio:    imagenAspectRatio,
			NegativePrompt: imagenNegativePrompt,
			NumberOfImages: imagenNumberOfImages,
		}

		log.WithFields(log.Fields{
			"prompt":      prompt,
			"aspectRatio": req.AspectRatio,
			"count":       req.NumberOfImages,
		}).Info("Generating images")

		// Generate images
		resp, err := client.GenerateImage(ctx, req)
		if err != nil {
			return fmt.Errorf("failed to generate images: %w", err)
		}

		// Handle output
		if imagenOutputJSON {
			return outputJSON(resp)
		}

		return outputHuman(ctx, client, resp)
	},
}

func outputJSON(resp *imagen.ImageResponse) error {
	output := map[string]interface{}{
		"generation_id": resp.GenerationID,
		"image_uris":    resp.ImageURIs,
		"image_count":   len(resp.ImageURIs),
		"metadata": map[string]interface{}{
			"prompt":       resp.Metadata.Prompt,
			"aspect_ratio": resp.Metadata.AspectRatio,
			"generated_at": resp.Metadata.GeneratedAt,
			"model":        resp.Metadata.Model,
		},
	}

	data, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	fmt.Println(string(data))
	return nil
}

func outputHuman(ctx context.Context, client *imagen.Client, resp *imagen.ImageResponse) error {
	fmt.Printf("✅ Generated %d image(s)\n", len(resp.ImageURIs))
	fmt.Printf("Generation ID: %s\n", resp.GenerationID)
	fmt.Printf("Model: %s\n", resp.Metadata.Model)
	fmt.Printf("Aspect Ratio: %s\n", resp.Metadata.AspectRatio)
	fmt.Println()

	// Download images if output directory specified
	if imagenOutputDir != "" {
		if err := os.MkdirAll(imagenOutputDir, 0755); err != nil {
			return fmt.Errorf("failed to create output directory: %w", err)
		}

		for i, uri := range resp.ImageURIs {
			filename := fmt.Sprintf("imagen-%s-%d.png", resp.GenerationID, i+1)
			destPath := filepath.Join(imagenOutputDir, filename)

			fmt.Printf("📥 Downloading image %d/%d to %s...\n", i+1, len(resp.ImageURIs), destPath)

			if err := client.DownloadImage(ctx, uri, destPath); err != nil {
				log.WithError(err).Warnf("Failed to download image %d", i+1)
				fmt.Printf("⚠️  Failed to download image %d: %v\n", i+1, err)
				continue
			}

			fmt.Printf("✅ Saved: %s\n", destPath)
		}
	} else {
		fmt.Println("Image URIs:")
		for i, uri := range resp.ImageURIs {
			// Truncate long data URIs for display
			displayURI := uri
			if len(displayURI) > 100 {
				displayURI = displayURI[:100] + "..."
			}
			fmt.Printf("  %d. %s\n", i+1, displayURI)
		}
		fmt.Println()
		fmt.Println("💡 Tip: Use --output-dir to automatically download images")
	}

	return nil
}

func init() {
	rootCmd.AddCommand(imagenCmd)
	imagenCmd.AddCommand(imagenGenerateCmd)

	// Flags for generate command
	imagenGenerateCmd.Flags().StringVar(&imagenProjectID, "project-id", "", "Google Cloud project ID")
	imagenGenerateCmd.Flags().StringVar(&imagenAspectRatio, "aspect-ratio", "1:1", "Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)")
	imagenGenerateCmd.Flags().StringVar(&imagenNegativePrompt, "negative", "", "Negative prompt (what to avoid)")
	imagenGenerateCmd.Flags().IntVar(&imagenNumberOfImages, "count", 1, "Number of images to generate (1-4)")
	imagenGenerateCmd.Flags().StringVar(&imagenOutputDir, "output-dir", "", "Directory to save generated images")
	imagenGenerateCmd.Flags().BoolVar(&imagenOutputJSON, "output", false, "Output as JSON (use 'json' for GitHub Actions)")
}
