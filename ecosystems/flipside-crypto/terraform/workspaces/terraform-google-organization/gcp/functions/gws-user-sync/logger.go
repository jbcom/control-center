package main

import (
	"context"
	"fmt"
	"os"

	"cloud.google.com/go/logging"
)

// Logger wraps Cloud Logging functionality
type Logger struct {
	client *logging.Client
	logger *logging.Logger
}

// NewLogger creates a new logger instance
func NewLogger(ctx context.Context) (*Logger, error) {
	projectID := os.Getenv("GOOGLE_CLOUD_PROJECT")
	if projectID == "" {
		projectID = "flipsidecrypto"
	}

	client, err := logging.NewClient(ctx, projectID)
	if err != nil {
		return nil, fmt.Errorf("failed to create logging client: %v", err)
	}

	logger := client.Logger("gws-user-sync")

	return &Logger{
		client: client,
		logger: logger,
	}, nil
}

// Info logs an info message
func (l *Logger) Info(message string) {
	l.logger.Log(logging.Entry{
		Severity: logging.Info,
		Payload:  message,
	})
}

// Warning logs a warning message
func (l *Logger) Warning(message string) {
	l.logger.Log(logging.Entry{
		Severity: logging.Warning,
		Payload:  message,
	})
}

// Error logs an error message
func (l *Logger) Error(message string) {
	l.logger.Log(logging.Entry{
		Severity: logging.Error,
		Payload:  message,
	})
}

// Close closes the logging client
func (l *Logger) Close() error {
	return l.client.Close()
}
