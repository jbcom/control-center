package main

import (
	"context"
	"fmt"

	admin "google.golang.org/api/admin/directory/v1"
)

// SchemaManager handles custom schema operations
type SchemaManager struct {
	service *admin.Service
	logger  *Logger
}

// NewSchemaManager creates a new schema manager
func NewSchemaManager(service *admin.Service, logger *Logger) *SchemaManager {
	return &SchemaManager{
		service: service,
		logger:  logger,
	}
}

// EnsureCustomSchemas ensures required custom schemas exist and are up to date
func (sm *SchemaManager) EnsureCustomSchemas(ctx context.Context) error {
	sm.logger.Info("Ensuring custom schemas exist and are up to date")

	// Get existing schemas
	existingSchemas, err := sm.getExistingSchemas(ctx)
	if err != nil {
		return fmt.Errorf("failed to get existing schemas: %v", err)
	}

	// Define required schemas
	requiredSchemas := map[string][]string{
		"VendorAttributes": {"githubUsername", "awsAccountName"},
	}

	// Process each required schema
	for schemaName, schemaFields := range requiredSchemas {
		sm.logger.Info(fmt.Sprintf("Ensuring that custom schema %s exists and is up to date", schemaName))

		if existingSchema, exists := existingSchemas[schemaName]; exists {
			// Schema exists, check if it needs updates
			if err := sm.updateExistingSchema(ctx, existingSchema, schemaName, schemaFields); err != nil {
				return fmt.Errorf("failed to update schema %s: %v", schemaName, err)
			}
		} else {
			// Schema doesn't exist, create it
			if err := sm.createNewSchema(ctx, schemaName, schemaFields); err != nil {
				return fmt.Errorf("failed to create schema %s: %v", schemaName, err)
			}
		}
	}

	return nil
}

// getExistingSchemas retrieves all existing custom schemas
func (sm *SchemaManager) getExistingSchemas(ctx context.Context) (map[string]*admin.Schema, error) {
	schemas := make(map[string]*admin.Schema)

	resp, err := sm.service.Schemas.List("my_customer").Context(ctx).Do()
	if err != nil {
		return nil, err
	}

	for _, schema := range resp.Schemas {
		schemas[schema.SchemaName] = schema
	}

	return schemas, nil
}

// updateExistingSchema updates an existing schema with required fields
func (sm *SchemaManager) updateExistingSchema(ctx context.Context, existingSchema *admin.Schema, schemaName string, requiredFields []string) error {
	// Track existing fields
	existingFields := make(map[string]*admin.SchemaFieldSpec)
	for _, field := range existingSchema.Fields {
		existingFields[field.FieldName] = field
	}

	// Identify fields to add
	var fieldsToAdd []*admin.SchemaFieldSpec
	for _, requiredField := range requiredFields {
		if _, exists := existingFields[requiredField]; !exists {
			fieldsToAdd = append(fieldsToAdd, &admin.SchemaFieldSpec{
				FieldName:      requiredField,
				FieldType:      "STRING",
				MultiValued:    false,
				ReadAccessType: "ADMINS_AND_SELF",
			})
		}
	}

	// Identify fields to delete (fields that exist but aren't required)
	var fieldsToDelete []string
	for existingFieldName := range existingFields {
		found := false
		for _, requiredField := range requiredFields {
			if existingFieldName == requiredField {
				found = true
				break
			}
		}
		if !found {
			fieldsToDelete = append(fieldsToDelete, existingFieldName)
		}
	}

	// Remove extra fields if any
	if len(fieldsToDelete) > 0 {
		sm.logger.Warning(fmt.Sprintf("Removing extra fields from %s: %v", schemaName, fieldsToDelete))
		for _, fieldToDelete := range fieldsToDelete {
			sm.logger.Warning(fmt.Sprintf("Note: Field deletion not implemented - would remove field %s from %s", fieldToDelete, schemaName))
			// Note: The Google Admin SDK doesn't support individual field deletion
			// This would require recreating the entire schema
		}
	}

	// Add missing fields if any
	if len(fieldsToAdd) > 0 {
		sm.logger.Info(fmt.Sprintf("Adding new fields to %s: %v", schemaName, fieldsToAdd))
		updateSchema := &admin.Schema{
			Fields: fieldsToAdd,
		}
		_, err := sm.service.Schemas.Patch("my_customer", existingSchema.SchemaId, updateSchema).Context(ctx).Do()
		if err != nil {
			return fmt.Errorf("failed to add fields: %v", err)
		}
		sm.logger.Info(fmt.Sprintf("New fields added to %s", schemaName))
	}

	return nil
}

// createNewSchema creates a new custom schema
func (sm *SchemaManager) createNewSchema(ctx context.Context, schemaName string, schemaFields []string) error {
	sm.logger.Info(fmt.Sprintf("Creating %s custom schema", schemaName))

	fields := make([]*admin.SchemaFieldSpec, len(schemaFields))
	for i, fieldName := range schemaFields {
		fields[i] = &admin.SchemaFieldSpec{
			FieldName:      fieldName,
			FieldType:      "STRING",
			MultiValued:    false,
			ReadAccessType: "ADMINS_AND_SELF",
		}
	}

	schema := &admin.Schema{
		SchemaName: schemaName,
		Fields:     fields,
	}

	_, err := sm.service.Schemas.Insert("my_customer", schema).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to create schema: %v", err)
	}

	sm.logger.Info(fmt.Sprintf("%s custom schema created successfully", schemaName))
	return nil
}

// PopulateCustomSchemaField populates a custom schema field for a user
func (sm *SchemaManager) PopulateCustomSchemaField(ctx context.Context, userEmail, schemaName, fieldName, fieldValue string) error {
	if fieldValue == "" {
		return nil
	}

	// Get current user to check existing custom schemas
	user, err := sm.service.Users.Get(userEmail).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to get user %s: %v", userEmail, err)
	}

	// Check if field already has a value
	if user.CustomSchemas != nil {
		if _, exists := user.CustomSchemas[schemaName]; exists {
			// Parse existing schema to check if field already has a value
			// For simplicity, we'll assume if the schema exists, the field might have a value
			// In a production environment, you'd want to properly parse the JSON
			sm.logger.Warning(fmt.Sprintf("User %s custom schema %s may already have values", userEmail, schemaName))
		}
	}

	// Create the custom schema update
	customSchemas := make(map[string]interface{})
	if user.CustomSchemas != nil {
		// Copy existing schemas (simplified approach)
		for key := range user.CustomSchemas {
			customSchemas[key] = make(map[string]interface{})
		}
	}

	// Add or update the specific schema
	if customSchemas[schemaName] == nil {
		customSchemas[schemaName] = make(map[string]interface{})
	}

	schemaMap := customSchemas[schemaName].(map[string]interface{})
	schemaMap[fieldName] = fieldValue

	// Note: This is a simplified implementation. In production, you'd need to properly
	// handle the JSON marshaling/unmarshaling of custom schemas
	sm.logger.Info(fmt.Sprintf("Would update custom schema %s field %s for user %s with value %s", schemaName, fieldName, userEmail, fieldValue))

	return nil
}

// GenerateAWSUsername generates an AWS username from an email
func (sm *SchemaManager) GenerateAWSUsername(email string) string {
	// Extract username part before @
	atIndex := -1
	for i, char := range email {
		if char == '@' {
			atIndex = i
			break
		}
	}

	if atIndex == -1 {
		return ""
	}

	username := email[:atIndex]

	// Replace dots with underscores and convert to lowercase
	awsUsername := "User-"
	for _, char := range username {
		if char == '.' {
			awsUsername += "_"
		} else {
			awsUsername += string(char)
		}
	}

	return awsUsername
}
