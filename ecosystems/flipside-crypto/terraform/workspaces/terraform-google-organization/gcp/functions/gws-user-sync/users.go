package main

import (
	"context"
	"crypto/rand"
	"fmt"
	"math/big"
	"strings"

	admin "google.golang.org/api/admin/directory/v1"
)

// UserManager handles user-related operations
type UserManager struct {
	service *admin.Service
	logger  *Logger
}

// NewUserManager creates a new user manager
func NewUserManager(service *admin.Service, logger *Logger) *UserManager {
	return &UserManager{
		service: service,
		logger:  logger,
	}
}

// GetAllUsers retrieves all users from Google Workspace
func (um *UserManager) GetAllUsers(ctx context.Context) (map[string]interface{}, error) {
	users := make(map[string]interface{})

	call := um.service.Users.List().Customer("my_customer").MaxResults(500)

	for {
		resp, err := call.Context(ctx).Do()
		if err != nil {
			return nil, fmt.Errorf("failed to list users: %v", err)
		}

		for _, user := range resp.Users {
			users[user.PrimaryEmail] = um.userToMap(user)
		}

		if resp.NextPageToken == "" {
			break
		}
		call.PageToken(resp.NextPageToken)
	}

	um.logger.Info(fmt.Sprintf("Retrieved %d users from Google Workspace", len(users)))
	return users, nil
}

// OnboardUser creates a new user in Google Workspace
func (um *UserManager) OnboardUser(ctx context.Context, email string, userData map[string]interface{}) (*admin.User, error) {
	um.logger.Info(fmt.Sprintf("Onboarding new user: %s", email))

	// Generate initial password
	initialPassword, err := um.generatePassword(12)
	if err != nil {
		return nil, fmt.Errorf("failed to generate password: %v", err)
	}

	// Create user object
	user := &admin.User{
		PrimaryEmail:               email,
		Suspended:                  false,
		Password:                   initialPassword,
		ChangePasswordAtNextLogin:  true,
		OrgUnitPath:                "/Users",
		IncludeInGlobalAddressList: true,
	}

	// Apply name if provided
	if name, exists := userData["name"]; exists {
		if nameMap, ok := name.(map[string]interface{}); ok {
			user.Name = &admin.UserName{
				GivenName:  um.getString(nameMap, "givenName"),
				FamilyName: um.getString(nameMap, "familyName"),
			}
		}
	}

	// Apply org unit if provided
	if orgUnit, exists := userData["orgUnitPath"]; exists {
		if orgUnitStr, ok := orgUnit.(string); ok {
			user.OrgUnitPath = orgUnitStr
		}
	}

	// Create the user
	createdUser, err := um.service.Users.Insert(user).Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to create user: %v", err)
	}

	um.logger.Info(fmt.Sprintf("Successfully onboarded user %s with initial password", email))
	return createdUser, nil
}

// MoveUserToLimitedAccess moves a user to the LimitedAccess organizational unit
func (um *UserManager) MoveUserToLimitedAccess(ctx context.Context, email string) error {
	user := &admin.User{
		OrgUnitPath: "/LimitedAccess",
	}

	_, err := um.service.Users.Update(email, user).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to move user to LimitedAccess: %v", err)
	}

	um.logger.Info(fmt.Sprintf("Moved user %s to LimitedAccess", email))
	return nil
}

// ArchiveUser archives a user account
func (um *UserManager) ArchiveUser(ctx context.Context, email string) error {
	user := &admin.User{
		Archived:  true,
		Suspended: false,
	}

	_, err := um.service.Users.Update(email, user).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to archive user: %v", err)
	}

	um.logger.Info(fmt.Sprintf("Archived user: %s", email))
	return nil
}

// SuspendUser suspends a user account
func (um *UserManager) SuspendUser(ctx context.Context, email string) error {
	user := &admin.User{
		Suspended: true,
	}

	_, err := um.service.Users.Update(email, user).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to suspend user: %v", err)
	}

	um.logger.Info(fmt.Sprintf("Suspended user: %s", email))
	return nil
}

// UnsuspendUser unsuspends a user account
func (um *UserManager) UnsuspendUser(ctx context.Context, email string) error {
	user := &admin.User{
		Suspended: false,
	}

	_, err := um.service.Users.Update(email, user).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to unsuspend user: %v", err)
	}

	um.logger.Info(fmt.Sprintf("Unsuspended user: %s", email))
	return nil
}

// GetUserParams extracts user parameters from user data
func (um *UserManager) GetUserParams(userData map[string]interface{}) UserParams {
	orgUnitPath := um.getString(userData, "orgUnitPath")
	archived := um.getBool(userData, "archived")
	suspended := um.getBool(userData, "suspended")

	var userType UserType
	if strings.HasPrefix(orgUnitPath, "/Automation") {
		userType = UserTypeBot
	} else if archived || suspended {
		userType = UserTypeInactive
	} else {
		userType = UserTypeActive
	}

	return UserParams{
		OrgUnitPath: orgUnitPath,
		Archived:    archived,
		Suspended:   suspended,
		UserType:    userType,
	}
}

// ProcessInactiveUser handles inactive (suspended/archived) users
func (um *UserManager) ProcessInactiveUser(ctx context.Context, email string, userParams UserParams) error {
	um.logger.Info(fmt.Sprintf("Processing inactive user: %s", email))

	// Move to LimitedAccess if not already there
	if !strings.HasSuffix(userParams.OrgUnitPath, "LimitedAccess") {
		if err := um.MoveUserToLimitedAccess(ctx, email); err != nil {
			return fmt.Errorf("failed to move user to LimitedAccess: %v", err)
		}
		userParams.OrgUnitPath = "/LimitedAccess"
	}

	// Archive user if in LimitedAccess and not already archived
	if strings.HasSuffix(userParams.OrgUnitPath, "LimitedAccess") && !userParams.Archived {
		if err := um.ArchiveUser(ctx, email); err != nil {
			return fmt.Errorf("failed to archive user: %v", err)
		}
	}

	return nil
}

// ProcessActiveUser handles active users
func (um *UserManager) ProcessActiveUser(ctx context.Context, email string, userParams UserParams) error {
	um.logger.Info(fmt.Sprintf("Processing active user: %s", email))

	// Handle consultants differently
	if userParams.OrgUnitPath == "/Consultants" {
		um.logger.Info(fmt.Sprintf("User %s is a consultant - special handling required", email))
		return nil
	}

	// Regular active user processing
	um.logger.Info(fmt.Sprintf("User %s is a regular active user", email))
	return nil
}

// Helper methods
func (um *UserManager) userToMap(user *admin.User) map[string]interface{} {
	userMap := map[string]interface{}{
		"primaryEmail": user.PrimaryEmail,
		"orgUnitPath":  user.OrgUnitPath,
		"archived":     user.Archived,
		"suspended":    user.Suspended,
		"id":           user.Id,
	}

	if user.Name != nil {
		userMap["name"] = map[string]interface{}{
			"givenName":  user.Name.GivenName,
			"familyName": user.Name.FamilyName,
			"fullName":   user.Name.FullName,
		}
	}

	return userMap
}

func (um *UserManager) generatePassword(length int) (string, error) {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
	password := make([]byte, length)

	for i := range password {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(charset))))
		if err != nil {
			return "", err
		}
		password[i] = charset[num.Int64()]
	}

	return string(password), nil
}

func (um *UserManager) getString(data map[string]interface{}, key string) string {
	if val, exists := data[key]; exists {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func (um *UserManager) getBool(data map[string]interface{}, key string) bool {
	if val, exists := data[key]; exists {
		if b, ok := val.(bool); ok {
			return b
		}
	}
	return false
}
