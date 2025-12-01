package aws

import (
	"context"
	"fmt"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/identitystore"
	"github.com/aws/aws-sdk-go-v2/service/identitystore/types"
)

// Group represents an AWS Identity Center group
type Group struct {
	GroupID     string
	DisplayName string
	Description string
	Members     []string
}

// User represents an AWS Identity Center user
type User struct {
	UserID   string
	UserName string
	Email    string
}

// SyncGoogleGroupsToAWS synchronizes Google Workspace groups to AWS Identity Center
func (m *Manager) SyncGoogleGroupsToAWS(ctx context.Context, googleGroups map[string]interface{}, logger Logger) error {
	logger.Info("Starting Google Groups to AWS Identity Center synchronization")

	// Get existing AWS groups
	awsGroups, err := m.listAWSGroups(ctx)
	if err != nil {
		return fmt.Errorf("failed to list AWS groups: %v", err)
	}

	// Get existing AWS users
	awsUsers, err := m.listAWSUsers(ctx)
	if err != nil {
		return fmt.Errorf("failed to list AWS users: %v", err)
	}

	// Create a map of AWS users by email for quick lookup
	awsUsersByEmail := make(map[string]*User)
	for _, user := range awsUsers {
		awsUsersByEmail[user.Email] = user
	}

	// Process each Google group
	for groupName, groupData := range googleGroups {
		groupDataMap, ok := groupData.(map[string]interface{})
		if !ok {
			logger.Warning(fmt.Sprintf("Invalid group data for %s", groupName))
			continue
		}

		groupEmail := getString(groupDataMap, "email")
		if groupEmail == "" {
			logger.Warning(fmt.Sprintf("No email found for group %s", groupName))
			continue
		}

		// Skip external groups (not from the main domain)
		if !strings.HasSuffix(groupEmail, "@flipsidecrypto.com") {
			logger.Info(fmt.Sprintf("Skipping external group %s", groupEmail))
			continue
		}

		// Create or update the group in AWS
		awsGroupID, err := m.ensureAWSGroup(ctx, groupName, groupDataMap, awsGroups, logger)
		if err != nil {
			logger.Error(fmt.Sprintf("Failed to ensure AWS group for %s: %v", groupName, err))
			continue
		}

		// Sync group membership
		err = m.syncGroupMembership(ctx, awsGroupID, groupDataMap, awsUsersByEmail, logger)
		if err != nil {
			logger.Error(fmt.Sprintf("Failed to sync membership for group %s: %v", groupName, err))
			continue
		}

		logger.Info(fmt.Sprintf("Successfully synced group %s to AWS", groupName))
	}

	logger.Info("Completed Google Groups to AWS Identity Center synchronization")
	return nil
}

// listAWSGroups retrieves all groups from AWS Identity Center
func (m *Manager) listAWSGroups(ctx context.Context) (map[string]*Group, error) {
	groups := make(map[string]*Group)

	input := &identitystore.ListGroupsInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		MaxResults:      aws.Int32(50),
	}

	for {
		output, err := m.identityStoreClient.ListGroups(ctx, input)
		if err != nil {
			return nil, err
		}

		for _, group := range output.Groups {
			groups[*group.DisplayName] = &Group{
				GroupID:     *group.GroupId,
				DisplayName: *group.DisplayName,
				Description: getStringPtr(group.Description),
			}
		}

		if output.NextToken == nil {
			break
		}
		input.NextToken = output.NextToken
	}

	return groups, nil
}

// listAWSUsers retrieves all users from AWS Identity Center
func (m *Manager) listAWSUsers(ctx context.Context) ([]*User, error) {
	var users []*User

	input := &identitystore.ListUsersInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		MaxResults:      aws.Int32(50),
	}

	for {
		output, err := m.identityStoreClient.ListUsers(ctx, input)
		if err != nil {
			return nil, err
		}

		for _, user := range output.Users {
			var email string
			for _, emailAddr := range user.Emails {
				if emailAddr.Primary && emailAddr.Value != nil {
					email = *emailAddr.Value
					break
				}
			}
			if email == "" && len(user.Emails) > 0 && user.Emails[0].Value != nil {
				email = *user.Emails[0].Value
			}

			users = append(users, &User{
				UserID:   *user.UserId,
				UserName: *user.UserName,
				Email:    email,
			})
		}

		if output.NextToken == nil {
			break
		}
		input.NextToken = output.NextToken
	}

	return users, nil
}

// ensureAWSGroup creates a group in AWS Identity Center if it doesn't exist
func (m *Manager) ensureAWSGroup(ctx context.Context, groupName string, groupData map[string]interface{}, existingGroups map[string]*Group, logger Logger) (string, error) {
	description := getString(groupData, "description")
	if description == "" {
		description = fmt.Sprintf("Google Workspace group: %s", groupName)
	}

	// Check if group already exists
	if existingGroup, exists := existingGroups[groupName]; exists {
		logger.Info(fmt.Sprintf("AWS group %s already exists", groupName))
		return existingGroup.GroupID, nil
	}

	// Create new group
	createInput := &identitystore.CreateGroupInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		DisplayName:     aws.String(groupName),
		Description:     aws.String(description),
	}

	output, err := m.identityStoreClient.CreateGroup(ctx, createInput)
	if err != nil {
		return "", fmt.Errorf("failed to create group: %v", err)
	}

	logger.Info(fmt.Sprintf("Created AWS group %s", groupName))
	return *output.GroupId, nil
}

// syncGroupMembership synchronizes group membership between Google and AWS
func (m *Manager) syncGroupMembership(ctx context.Context, awsGroupID string, groupData map[string]interface{}, awsUsersByEmail map[string]*User, logger Logger) error {
	// Get current AWS group members
	currentMembers, err := m.getGroupMembers(ctx, awsGroupID)
	if err != nil {
		return fmt.Errorf("failed to get current group members: %v", err)
	}

	// Get Google group members
	googleMembers := make(map[string]bool)
	if membersData, exists := groupData["members"]; exists {
		if membersMap, ok := membersData.(map[string]interface{}); ok {
			for memberEmail := range membersMap {
				// Only include users from the main domain
				if strings.HasSuffix(memberEmail, "@flipsidecrypto.com") {
					googleMembers[memberEmail] = true
				}
			}
		}
	}

	// Add missing members to AWS group
	for email := range googleMembers {
		if awsUser, exists := awsUsersByEmail[email]; exists {
			if !contains(currentMembers, awsUser.UserID) {
				err := m.addUserToGroup(ctx, awsGroupID, awsUser.UserID)
				if err != nil {
					logger.Error(fmt.Sprintf("Failed to add user %s to group: %v", email, err))
				} else {
					logger.Info(fmt.Sprintf("Added user %s to AWS group", email))
				}
			}
		} else {
			logger.Warning(fmt.Sprintf("User %s not found in AWS Identity Center", email))
		}
	}

	// Remove users from AWS group who are no longer in Google group
	for _, memberUserID := range currentMembers {
		// Find the user email for this user ID
		var userEmail string
		for email, user := range awsUsersByEmail {
			if user.UserID == memberUserID {
				userEmail = email
				break
			}
		}

		if userEmail != "" && !googleMembers[userEmail] {
			err := m.removeUserFromGroup(ctx, awsGroupID, memberUserID)
			if err != nil {
				logger.Error(fmt.Sprintf("Failed to remove user %s from group: %v", userEmail, err))
			} else {
				logger.Info(fmt.Sprintf("Removed user %s from AWS group", userEmail))
			}
		}
	}

	return nil
}

// getGroupMembers retrieves all members of an AWS group
func (m *Manager) getGroupMembers(ctx context.Context, groupID string) ([]string, error) {
	var members []string

	input := &identitystore.ListGroupMembershipsInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		GroupId:         aws.String(groupID),
		MaxResults:      aws.Int32(50),
	}

	for {
		output, err := m.identityStoreClient.ListGroupMemberships(ctx, input)
		if err != nil {
			return nil, err
		}

		for _, membership := range output.GroupMemberships {
			// Extract user ID from MemberId interface
			if userMember, ok := membership.MemberId.(*types.MemberIdMemberUserId); ok {
				members = append(members, userMember.Value)
			}
		}

		if output.NextToken == nil {
			break
		}
		input.NextToken = output.NextToken
	}

	return members, nil
}

// addUserToGroup adds a user to an AWS group
func (m *Manager) addUserToGroup(ctx context.Context, groupID, userID string) error {
	input := &identitystore.CreateGroupMembershipInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		GroupId:         aws.String(groupID),
		MemberId: &types.MemberIdMemberUserId{
			Value: userID,
		},
	}

	_, err := m.identityStoreClient.CreateGroupMembership(ctx, input)
	return err
}

// removeUserFromGroup removes a user from an AWS group
func (m *Manager) removeUserFromGroup(ctx context.Context, groupID, userID string) error {
	// First, find the membership ID
	membershipID, err := m.findGroupMembershipID(ctx, groupID, userID)
	if err != nil {
		return err
	}

	input := &identitystore.DeleteGroupMembershipInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		MembershipId:    aws.String(membershipID),
	}

	_, err = m.identityStoreClient.DeleteGroupMembership(ctx, input)
	return err
}

// findGroupMembershipID finds the membership ID for a user in a group
func (m *Manager) findGroupMembershipID(ctx context.Context, groupID, userID string) (string, error) {
	input := &identitystore.ListGroupMembershipsInput{
		IdentityStoreId: aws.String(m.config.IdentityStoreID),
		GroupId:         aws.String(groupID),
		MaxResults:      aws.Int32(50),
	}

	for {
		output, err := m.identityStoreClient.ListGroupMemberships(ctx, input)
		if err != nil {
			return "", err
		}

		for _, membership := range output.GroupMemberships {
			// Extract user ID from MemberId interface
			if userMember, ok := membership.MemberId.(*types.MemberIdMemberUserId); ok {
				if userMember.Value == userID {
					return *membership.MembershipId, nil
				}
			}
		}

		if output.NextToken == nil {
			break
		}
		input.NextToken = output.NextToken
	}

	return "", fmt.Errorf("membership not found for user %s in group %s", userID, groupID)
}

// Helper functions
func getString(data map[string]interface{}, key string) string {
	if val, exists := data[key]; exists {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func getStringPtr(ptr *string) string {
	if ptr != nil {
		return *ptr
	}
	return ""
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
