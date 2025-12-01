package main

import (
	"context"
	"fmt"
	"log"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
)

// SyncRequest represents the request payload for the sync function
type SyncRequest struct {
	OnboardUsers map[string]interface{} `json:"onboard_users,omitempty"`
}

// SyncResponse represents the response from the sync function
type SyncResponse struct {
	Success bool     `json:"success"`
	Message string   `json:"message"`
	Errors  []string `json:"errors,omitempty"`
}

func init() {
	functions.CloudEvent("SyncFlipsideCryptoUsersAndGroups", syncFlipsideCryptoUsersAndGroups)
}

// syncFlipsideCryptoUsersAndGroups is the main Cloud Event handler for the scheduled cloud function
func syncFlipsideCryptoUsersAndGroups(ctx context.Context, e event.Event) error {
	// Initialize logging
	logger, err := NewLogger(ctx)
	if err != nil {
		log.Printf("Failed to initialize logging: %v", err)
		return fmt.Errorf("failed to initialize logging: %v", err)
	}
	defer logger.Close()

	logger.Info("Starting scheduled FlipsideCrypto users and groups sync")

	// For scheduled functions, we typically don't need to parse complex request data
	// but we'll create an empty request to maintain compatibility with the sync service
	req := SyncRequest{
		OnboardUsers: make(map[string]interface{}),
	}

	// Initialize the sync service
	syncService, err := NewSyncService(ctx, logger)
	if err != nil {
		logger.Error(fmt.Sprintf("Failed to initialize sync service: %v", err))
		return fmt.Errorf("failed to initialize sync service: %v", err)
	}

	// Execute the sync
	response := syncService.SyncUsersAndGroups(ctx, req)

	// Log the response
	if response.Success {
		logger.Info(fmt.Sprintf("Sync completed successfully: %s", response.Message))
	} else {
		logger.Error(fmt.Sprintf("Sync failed: %s", response.Message))
		if len(response.Errors) > 0 {
			for _, err := range response.Errors {
				logger.Error(fmt.Sprintf("Sync error: %s", err))
			}
		}
		return fmt.Errorf("sync failed: %s", response.Message)
	}

	return nil
}
