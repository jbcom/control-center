package aws

import (
	"context"
	"fmt"
	"os"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/identitystore"
	"github.com/aws/aws-sdk-go-v2/service/ssoadmin"
)

// Config holds AWS configuration
type Config struct {
	Region          string
	IdentityStoreID string
	SSOInstanceArn  string
}

// Manager handles AWS Identity Center operations
type Manager struct {
	identityStoreClient *identitystore.Client
	ssoAdminClient      *ssoadmin.Client
	config              *Config
}

// Logger interface for dependency injection
type Logger interface {
	Info(msg string)
	Warning(msg string)
	Error(msg string)
}

// NewManager creates a new AWS manager
func NewManager() (*Manager, error) {
	// Load AWS SDK configuration
	region := getEnvOrDefault("AWS_REGION", "us-east-1")
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion(region),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %v", err)
	}

	// Create AWS service clients
	identityStoreClient := identitystore.NewFromConfig(cfg)
	ssoAdminClient := ssoadmin.NewFromConfig(cfg)

	// Create manager with basic config
	manager := &Manager{
		identityStoreClient: identityStoreClient,
		ssoAdminClient:      ssoAdminClient,
		config: &Config{
			Region: region,
		},
	}

	// Dynamically discover SSO configuration
	err = manager.discoverSSOConfiguration(context.TODO())
	if err != nil {
		return nil, fmt.Errorf("failed to discover SSO configuration: %v", err)
	}

	return manager, nil
}

// discoverSSOConfiguration dynamically discovers the SSO Instance and Identity Store
func (m *Manager) discoverSSOConfiguration(ctx context.Context) error {
	// List SSO instances
	listInstancesInput := &ssoadmin.ListInstancesInput{}
	listInstancesOutput, err := m.ssoAdminClient.ListInstances(ctx, listInstancesInput)
	if err != nil {
		return fmt.Errorf("failed to list SSO instances: %v", err)
	}

	if len(listInstancesOutput.Instances) == 0 {
		return fmt.Errorf("no SSO instances found")
	}

	// Use the first SSO instance (typically there's only one)
	instance := listInstancesOutput.Instances[0]
	m.config.SSOInstanceArn = *instance.InstanceArn
	m.config.IdentityStoreID = *instance.IdentityStoreId

	return nil
}

// GetConfig returns the AWS configuration
func (m *Manager) GetConfig() *Config {
	return m.config
}

// getEnvOrDefault returns environment variable value or default
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
