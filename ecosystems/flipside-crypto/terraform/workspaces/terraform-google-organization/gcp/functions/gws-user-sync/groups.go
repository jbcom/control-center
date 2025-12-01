package main

import (
	"context"
	"fmt"
	"strings"

	admin "google.golang.org/api/admin/directory/v1"
)

// GroupManager handles group-related operations
type GroupManager struct {
	service *admin.Service
	logger  *Logger
}

// NewGroupManager creates a new group manager
func NewGroupManager(service *admin.Service, logger *Logger) *GroupManager {
	return &GroupManager{
		service: service,
		logger:  logger,
	}
}

// GetAllGroups retrieves all groups from Google Workspace
func (gm *GroupManager) GetAllGroups(ctx context.Context) (map[string]interface{}, error) {
	groups := make(map[string]interface{})

	call := gm.service.Groups.List().Customer("my_customer").MaxResults(200)

	for {
		resp, err := call.Context(ctx).Do()
		if err != nil {
			return nil, fmt.Errorf("failed to list groups: %v", err)
		}

		for _, group := range resp.Groups {
			groupData := gm.groupToMap(group)

			// Get group members
			members, err := gm.getGroupMembers(ctx, group.Id)
			if err != nil {
				gm.logger.Warning(fmt.Sprintf("Failed to get members for group %s: %v", group.Email, err))
				groupData["members"] = make(map[string]interface{})
			} else {
				groupData["members"] = members
			}

			groups[group.Name] = groupData
		}

		if resp.NextPageToken == "" {
			break
		}
		call.PageToken(resp.NextPageToken)
	}

	gm.logger.Info(fmt.Sprintf("Retrieved %d groups from Google Workspace", len(groups)))
	return groups, nil
}

// getGroupMembers retrieves all members of a specific group
func (gm *GroupManager) getGroupMembers(ctx context.Context, groupId string) (map[string]interface{}, error) {
	members := make(map[string]interface{})

	call := gm.service.Members.List(groupId)

	for {
		resp, err := call.Context(ctx).Do()
		if err != nil {
			return nil, err
		}

		for _, member := range resp.Members {
			memberData := map[string]interface{}{
				"email": member.Email,
				"role":  member.Role,
				"type":  member.Type,
				"id":    member.Id,
			}
			members[member.Email] = memberData
		}

		if resp.NextPageToken == "" {
			break
		}
		call.PageToken(resp.NextPageToken)
	}

	return members, nil
}

// GetTeamGroupMembers extracts team group members from groups data
func (gm *GroupManager) GetTeamGroupMembers(groups map[string]interface{}) map[string]bool {
	members := make(map[string]bool)

	if teamGroup, exists := groups["Team"]; exists {
		if groupData, ok := teamGroup.(map[string]interface{}); ok {
			if groupMembers, exists := groupData["members"]; exists {
				if membersMap, ok := groupMembers.(map[string]interface{}); ok {
					for email := range membersMap {
						members[email] = true
					}
				}
			}
		}
	}

	return members
}

// AddUserToGroup adds a user to a Google Workspace group
func (gm *GroupManager) AddUserToGroup(ctx context.Context, userEmail, groupEmail, role string) error {
	member := &admin.Member{
		Email: userEmail,
		Role:  role,
	}

	_, err := gm.service.Members.Insert(groupEmail, member).Context(ctx).Do()
	if err != nil {
		if strings.Contains(err.Error(), "Member already exists") {
			gm.logger.Warning(fmt.Sprintf("%s already in %s", userEmail, groupEmail))
			return nil
		}
		return fmt.Errorf("failed to add user to group: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Added user %s to group %s with role %s", userEmail, groupEmail, role))
	return nil
}

// RemoveUserFromGroup removes a user from a Google Workspace group
func (gm *GroupManager) RemoveUserFromGroup(ctx context.Context, userEmail, groupEmail string) error {
	err := gm.service.Members.Delete(groupEmail, userEmail).Context(ctx).Do()
	if err != nil {
		if strings.Contains(err.Error(), "Member not found") {
			gm.logger.Warning(fmt.Sprintf("%s not found in %s", userEmail, groupEmail))
			return nil
		}
		return fmt.Errorf("failed to remove user from group: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Removed user %s from group %s", userEmail, groupEmail))
	return nil
}

// UpdateGroupMembership updates a user's role in a group
func (gm *GroupManager) UpdateGroupMembership(ctx context.Context, userEmail, groupEmail, newRole string) error {
	member := &admin.Member{
		Email: userEmail,
		Role:  newRole,
	}

	_, err := gm.service.Members.Update(groupEmail, userEmail, member).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to update group membership: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Updated user %s role to %s in group %s", userEmail, newRole, groupEmail))
	return nil
}

// SyncGroupMemberships synchronizes group memberships based on user status
func (gm *GroupManager) SyncGroupMemberships(ctx context.Context, groups map[string]interface{}, users map[string]interface{}) error {
	for groupName, groupData := range groups {
		gm.logger.Info(fmt.Sprintf("Syncing Google group %s", groupName))

		groupDataMap, ok := groupData.(map[string]interface{})
		if !ok {
			continue
		}

		groupEmail := gm.getString(groupDataMap, "email")
		if groupEmail == "" {
			continue
		}

		members, ok := groupDataMap["members"].(map[string]interface{})
		if !ok {
			continue
		}

		// Check each member
		for memberEmail := range members {
			if !strings.HasSuffix(memberEmail, "@"+Domain) {
				gm.logger.Warning(fmt.Sprintf("Ignoring external member %s", memberEmail))
				continue
			}

			// Check if user still exists and is active
			if userData, exists := users[memberEmail]; exists {
				userDataMap, ok := userData.(map[string]interface{})
				if !ok {
					continue
				}

				userParams := gm.getUserParams(userDataMap)
				if userParams.Suspended || userParams.Archived {
					gm.logger.Warning(fmt.Sprintf("Member %s is no longer active, removing from group %s", memberEmail, groupEmail))
					if err := gm.RemoveUserFromGroup(ctx, memberEmail, groupEmail); err != nil {
						gm.logger.Error(fmt.Sprintf("Failed to remove %s from %s: %v", memberEmail, groupEmail, err))
					}
				}
			} else {
				gm.logger.Warning(fmt.Sprintf("Member %s no longer exists, removing from group %s", memberEmail, groupEmail))
				if err := gm.RemoveUserFromGroup(ctx, memberEmail, groupEmail); err != nil {
					gm.logger.Error(fmt.Sprintf("Failed to remove %s from %s: %v", memberEmail, groupEmail, err))
				}
			}
		}
	}

	return nil
}

// CreateGroup creates a new Google Workspace group
func (gm *GroupManager) CreateGroup(ctx context.Context, groupEmail, groupName, description string) (*admin.Group, error) {
	group := &admin.Group{
		Email:       groupEmail,
		Name:        groupName,
		Description: description,
	}

	createdGroup, err := gm.service.Groups.Insert(group).Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to create group: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Created group %s (%s)", groupName, groupEmail))
	return createdGroup, nil
}

// DeleteGroup deletes a Google Workspace group
func (gm *GroupManager) DeleteGroup(ctx context.Context, groupEmail string) error {
	err := gm.service.Groups.Delete(groupEmail).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to delete group: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Deleted group %s", groupEmail))
	return nil
}

// UpdateGroup updates a Google Workspace group's properties
func (gm *GroupManager) UpdateGroup(ctx context.Context, groupEmail string, updates map[string]interface{}) error {
	group := &admin.Group{}

	if name, exists := updates["name"]; exists {
		if nameStr, ok := name.(string); ok {
			group.Name = nameStr
		}
	}

	if description, exists := updates["description"]; exists {
		if descStr, ok := description.(string); ok {
			group.Description = descStr
		}
	}

	_, err := gm.service.Groups.Update(groupEmail, group).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to update group: %v", err)
	}

	gm.logger.Info(fmt.Sprintf("Updated group %s", groupEmail))
	return nil
}

// Helper methods
func (gm *GroupManager) groupToMap(group *admin.Group) map[string]interface{} {
	return map[string]interface{}{
		"email":              group.Email,
		"name":               group.Name,
		"description":        group.Description,
		"id":                 group.Id,
		"directMembersCount": group.DirectMembersCount,
	}
}

func (gm *GroupManager) getUserParams(userData map[string]interface{}) UserParams {
	orgUnitPath := gm.getString(userData, "orgUnitPath")
	archived := gm.getBool(userData, "archived")
	suspended := gm.getBool(userData, "suspended")

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

func (gm *GroupManager) getString(data map[string]interface{}, key string) string {
	if val, exists := data[key]; exists {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func (gm *GroupManager) getBool(data map[string]interface{}, key string) bool {
	if val, exists := data[key]; exists {
		if b, ok := val.(bool); ok {
			return b
		}
	}
	return false
}
