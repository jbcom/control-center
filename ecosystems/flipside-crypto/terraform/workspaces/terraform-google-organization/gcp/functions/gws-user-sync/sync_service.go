package main

import (
	"context"
	"fmt"
	"os"

	"gws-user-sync/aws"

	admin "google.golang.org/api/admin/directory/v1"
	"google.golang.org/api/calendar/v3"
	"google.golang.org/api/option"
)

// SyncService handles Google Workspace synchronization
type SyncService struct {
	logger          *Logger
	userManager     *UserManager
	groupManager    *GroupManager
	calendarManager *CalendarManager
	schemaManager   *SchemaManager
	awsManager      *aws.Manager
	errors          []string
}

// NewSyncService creates a new sync service instance
func NewSyncService(ctx context.Context, logger *Logger) (*SyncService, error) {
	// Initialize Google Admin Directory service
	directoryService, err := admin.NewService(ctx, option.WithScopes(
		admin.AdminDirectoryUserScope,
		admin.AdminDirectoryGroupScope,
		admin.AdminDirectoryOrgunitScope,
		"https://www.googleapis.com/auth/admin.directory.user.schema",
	))
	if err != nil {
		return nil, fmt.Errorf("failed to create directory service: %v", err)
	}

	// Initialize Google Calendar service
	calendarService, err := calendar.NewService(ctx, option.WithScopes(
		calendar.CalendarScope,
	))
	if err != nil {
		return nil, fmt.Errorf("failed to create calendar service: %v", err)
	}

	// Create managers
	userManager := NewUserManager(directoryService, logger)
	groupManager := NewGroupManager(directoryService, logger)
	calendarManager := NewCalendarManager(calendarService, logger)
	schemaManager := NewSchemaManager(directoryService, logger)

	// Initialize AWS manager (optional - only if AWS credentials are available)
	var awsManager *aws.Manager
	if os.Getenv("AWS_ACCESS_KEY_ID") != "" || os.Getenv("AWS_PROFILE") != "" {
		awsManager, err = aws.NewManager()
		if err != nil {
			logger.Warning(fmt.Sprintf("Failed to initialize AWS manager: %v", err))
		} else {
			logger.Info("AWS Identity Center integration enabled")
		}
	}

	return &SyncService{
		logger:          logger,
		userManager:     userManager,
		groupManager:    groupManager,
		calendarManager: calendarManager,
		schemaManager:   schemaManager,
		awsManager:      awsManager,
		errors:          make([]string, 0),
	}, nil
}

// SyncUsersAndGroups performs the main synchronization logic
func (s *SyncService) SyncUsersAndGroups(ctx context.Context, req SyncRequest) SyncResponse {
	s.logger.Info("Starting user and group synchronization")

	// Ensure custom schemas exist
	if err := s.schemaManager.EnsureCustomSchemas(ctx); err != nil {
		s.addError(fmt.Sprintf("Failed to ensure custom schemas: %v", err))
		return s.errorResponse("Failed to ensure custom schemas")
	}

	// Onboard new users if provided
	if len(req.OnboardUsers) > 0 {
		s.logger.Info(fmt.Sprintf("Onboarding %d new users", len(req.OnboardUsers)))
		for email, userData := range req.OnboardUsers {
			userDataMap, ok := userData.(map[string]interface{})
			if !ok {
				s.addError(fmt.Sprintf("Invalid user data format for onboarding %s", email))
				continue
			}
			_, err := s.userManager.OnboardUser(ctx, email, userDataMap)
			if err != nil {
				s.addError(fmt.Sprintf("Failed to onboard user %s: %v", email, err))
			}
		}
	}

	// Get existing Google users
	existingUsers, err := s.userManager.GetAllUsers(ctx)
	if err != nil {
		s.addError(fmt.Sprintf("Failed to get Google users: %v", err))
		return s.errorResponse("Failed to get Google users")
	}

	// Get existing Google groups
	existingGroups, err := s.groupManager.GetAllGroups(ctx)
	if err != nil {
		s.addError(fmt.Sprintf("Failed to get Google groups: %v", err))
		return s.errorResponse("Failed to get Google groups")
	}

	// Get team group members
	teamGroupMembers := s.groupManager.GetTeamGroupMembers(existingGroups)

	// Track failed archive attempts
	var failedToArchive []string

	// Process each existing user
	for email, userData := range existingUsers {
		userDataMap, ok := userData.(map[string]interface{})
		if !ok {
			s.addError(fmt.Sprintf("Invalid user data format for %s", email))
			continue
		}

		userParams := s.userManager.GetUserParams(userDataMap)

		if userParams.UserType == UserTypeBot {
			s.logger.Warning(fmt.Sprintf("Skipping bot user %s", email))
			continue
		}

		if userParams.Suspended || userParams.Archived {
			if err := s.userManager.ProcessInactiveUser(ctx, email, userParams); err != nil {
				s.addError(fmt.Sprintf("Failed to process inactive user %s: %v", email, err))
				// Track users that failed to archive
				if userParams.Suspended && !userParams.Archived {
					failedToArchive = append(failedToArchive, email)
				}
			}
		} else {
			if err := s.userManager.ProcessActiveUser(ctx, email, userParams); err != nil {
				s.addError(fmt.Sprintf("Failed to process active user %s: %v", email, err))
			}

			// Handle team group membership for active users
			if userParams.OrgUnitPath == "/Consultants" {
				// Remove consultants from team group
				if teamGroupMembers[email] {
					if err := s.groupManager.RemoveUserFromGroup(ctx, email, TeamGroupEmail); err != nil {
						s.addError(fmt.Sprintf("Failed to remove consultant %s from team group: %v", email, err))
					}
				}
			} else {
				// Add regular users to team group
				if !teamGroupMembers[email] {
					if err := s.groupManager.AddUserToGroup(ctx, email, TeamGroupEmail, "MEMBER"); err != nil {
						s.addError(fmt.Sprintf("Failed to add user %s to team group: %v", email, err))
					}
				}

				// Handle AWS account assignment for group members if needed
				// Generate AWS username and populate custom schema
				awsUsername := s.schemaManager.GenerateAWSUsername(email)
				if awsUsername != "" {
					if err := s.schemaManager.PopulateCustomSchemaField(ctx, email, "VendorAttributes", "awsAccountName", awsUsername); err != nil {
						s.addError(fmt.Sprintf("Failed to assign AWS username to %s: %v", email, err))
					}
				}
			}
		}
	}

	// Sync group memberships
	if err := s.groupManager.SyncGroupMemberships(ctx, existingGroups, existingUsers); err != nil {
		s.addError(fmt.Sprintf("Failed to sync group memberships: %v", err))
	}

	// Sync calendar access
	if err := s.calendarManager.SyncCalendarAccess(ctx, existingUsers); err != nil {
		s.addError(fmt.Sprintf("Failed to sync calendar access: %v", err))
	}

	// Sync Google groups to AWS Identity Center if AWS manager is available
	if s.awsManager != nil {
		s.logger.Info("Starting AWS Identity Center group synchronization")
		if err := s.awsManager.SyncGoogleGroupsToAWS(ctx, existingGroups, s.logger); err != nil {
			s.addError(fmt.Sprintf("Failed to sync groups to AWS Identity Center: %v", err))
		} else {
			s.logger.Info("Successfully completed AWS Identity Center group synchronization")
		}
	}

	// Report failed archive attempts
	if len(failedToArchive) > 0 {
		s.addError(fmt.Sprintf("Users failed to archive: %v. Please purchase %d archive licenses and rerun.", failedToArchive, len(failedToArchive)))
	}

	// Determine final response
	success := len(s.errors) == 0
	message := "Synchronization completed successfully"
	if !success {
		message = "Synchronization completed with errors"
	}

	return SyncResponse{
		Success: success,
		Message: message,
		Errors:  s.errors,
	}
}

func (s *SyncService) errorResponse(message string) SyncResponse {
	return SyncResponse{
		Success: false,
		Message: message,
		Errors:  s.errors,
	}
}

func (s *SyncService) addError(err string) {
	s.errors = append(s.errors, err)
	s.logger.Error(err)
}
