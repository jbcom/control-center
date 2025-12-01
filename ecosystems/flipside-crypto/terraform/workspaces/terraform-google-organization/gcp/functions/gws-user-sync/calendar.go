package main

import (
	"context"
	"fmt"
	"strings"

	"google.golang.org/api/calendar/v3"
)

// CalendarManager handles calendar-related operations
type CalendarManager struct {
	service *calendar.Service
	logger  *Logger
}

// NewCalendarManager creates a new calendar manager
func NewCalendarManager(service *calendar.Service, logger *Logger) *CalendarManager {
	return &CalendarManager{
		service: service,
		logger:  logger,
	}
}

// GetTeamCalendarShares retrieves all ACL rules for the team calendar
func (cm *CalendarManager) GetTeamCalendarShares(ctx context.Context) (map[string]interface{}, error) {
	shares := make(map[string]interface{})

	call := cm.service.Acl.List(TeamCalendarID)

	resp, err := call.Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to list calendar ACL: %v", err)
	}

	for _, rule := range resp.Items {
		if rule.Scope != nil && rule.Scope.Type == "user" {
			shares[rule.Scope.Value] = map[string]interface{}{
				"id":   rule.Id,
				"role": rule.Role,
			}
		}
	}

	cm.logger.Info(fmt.Sprintf("Retrieved %d calendar shares for team calendar", len(shares)))
	return shares, nil
}

// AddUserToTeamCalendar adds a user to the team calendar with writer access
func (cm *CalendarManager) AddUserToTeamCalendar(ctx context.Context, userEmail string) (map[string]interface{}, error) {
	cm.logger.Info(fmt.Sprintf("Adding %s to team calendar", userEmail))

	rule := &calendar.AclRule{
		Scope: &calendar.AclRuleScope{
			Type:  "user",
			Value: userEmail,
		},
		Role: "writer",
	}

	createdRule, err := cm.service.Acl.Insert(TeamCalendarID, rule).Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to add user to team calendar: %v", err)
	}

	cm.logger.Info(fmt.Sprintf("Created new calendar rule: %s", createdRule.Id))

	return map[string]interface{}{
		"id":   createdRule.Id,
		"role": createdRule.Role,
	}, nil
}

// RemoveUserFromTeamCalendar removes a user from the team calendar
func (cm *CalendarManager) RemoveUserFromTeamCalendar(ctx context.Context, userEmail, ruleId string) error {
	cm.logger.Warning(fmt.Sprintf("Removing user %s from Team calendar", userEmail))

	err := cm.service.Acl.Delete(TeamCalendarID, ruleId).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to remove user from team calendar: %v", err)
	}

	cm.logger.Info(fmt.Sprintf("Removed user %s from team calendar", userEmail))
	return nil
}

// UpdateUserCalendarAccess updates a user's calendar access role
func (cm *CalendarManager) UpdateUserCalendarAccess(ctx context.Context, userEmail, ruleId, newRole string) error {
	rule := &calendar.AclRule{
		Role: newRole,
	}

	_, err := cm.service.Acl.Update(TeamCalendarID, ruleId, rule).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("failed to update calendar access: %v", err)
	}

	cm.logger.Info(fmt.Sprintf("Updated calendar access for %s to role %s", userEmail, newRole))
	return nil
}

// HandleCalendarAccess manages user access to team calendar based on user status
func (cm *CalendarManager) HandleCalendarAccess(ctx context.Context, userEmail string, existingShares map[string]interface{}, suspended, archived bool) error {
	if shareData, exists := existingShares[userEmail]; exists {
		shareMap, ok := shareData.(map[string]interface{})
		if !ok {
			return fmt.Errorf("invalid share data format for %s", userEmail)
		}

		ruleId := cm.getString(shareMap, "id")
		if ruleId == "" {
			return fmt.Errorf("missing rule ID for %s", userEmail)
		}

		if suspended || archived {
			cm.logger.Warning(fmt.Sprintf("Removing suspended/archived user %s from Team calendar", userEmail))
			return cm.RemoveUserFromTeamCalendar(ctx, userEmail, ruleId)
		} else {
			cm.logger.Info(fmt.Sprintf("%s is already in the Team calendar", userEmail))
		}
	} else if suspended || archived {
		cm.logger.Warning(fmt.Sprintf("Skipping adding suspended/archived user %s to Team calendar", userEmail))
	} else {
		cm.logger.Info(fmt.Sprintf("Adding %s to team calendar", userEmail))
		createdRule, err := cm.AddUserToTeamCalendar(ctx, userEmail)
		if err != nil {
			return err
		}
		// Update the existing shares map to reflect the new rule
		existingShares[userEmail] = createdRule
	}

	return nil
}

// SyncCalendarAccess synchronizes calendar access for all users
func (cm *CalendarManager) SyncCalendarAccess(ctx context.Context, users map[string]interface{}) error {
	// Get current calendar shares
	existingShares, err := cm.GetTeamCalendarShares(ctx)
	if err != nil {
		return fmt.Errorf("failed to get calendar shares: %v", err)
	}

	// Process each user
	for userEmail, userData := range users {
		userDataMap, ok := userData.(map[string]interface{})
		if !ok {
			continue
		}

		userParams := cm.getUserParams(userDataMap)

		// Skip bot users
		if userParams.UserType == UserTypeBot {
			cm.logger.Warning(fmt.Sprintf("Skipping bot user %s for calendar access", userEmail))
			continue
		}

		// Handle consultants differently
		if userParams.OrgUnitPath == "/Consultants" {
			if shareData, exists := existingShares[userEmail]; exists {
				shareMap, ok := shareData.(map[string]interface{})
				if ok {
					ruleId := cm.getString(shareMap, "id")
					if ruleId != "" {
						cm.logger.Warning(fmt.Sprintf("Removing consultant %s from Team calendar", userEmail))
						if err := cm.RemoveUserFromTeamCalendar(ctx, userEmail, ruleId); err != nil {
							cm.logger.Error(fmt.Sprintf("Failed to remove consultant %s from calendar: %v", userEmail, err))
						}
					}
				}
			}
			continue
		}

		// Handle calendar access based on user status
		if err := cm.HandleCalendarAccess(ctx, userEmail, existingShares, userParams.Suspended, userParams.Archived); err != nil {
			cm.logger.Error(fmt.Sprintf("Failed to handle calendar access for %s: %v", userEmail, err))
		}
	}

	return nil
}

// GetCalendarInfo retrieves basic information about the team calendar
func (cm *CalendarManager) GetCalendarInfo(ctx context.Context) (map[string]interface{}, error) {
	cal, err := cm.service.Calendars.Get(TeamCalendarID).Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to get calendar info: %v", err)
	}

	return map[string]interface{}{
		"id":          cal.Id,
		"summary":     cal.Summary,
		"description": cal.Description,
		"timeZone":    cal.TimeZone,
	}, nil
}

// CreateCalendarEvent creates a new event in the team calendar
func (cm *CalendarManager) CreateCalendarEvent(ctx context.Context, event *calendar.Event) (*calendar.Event, error) {
	createdEvent, err := cm.service.Events.Insert(TeamCalendarID, event).Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to create calendar event: %v", err)
	}

	cm.logger.Info(fmt.Sprintf("Created calendar event: %s", createdEvent.Summary))
	return createdEvent, nil
}

// ListCalendarEvents lists events from the team calendar
func (cm *CalendarManager) ListCalendarEvents(ctx context.Context, maxResults int64) ([]*calendar.Event, error) {
	call := cm.service.Events.List(TeamCalendarID).MaxResults(maxResults)

	resp, err := call.Context(ctx).Do()
	if err != nil {
		return nil, fmt.Errorf("failed to list calendar events: %v", err)
	}

	return resp.Items, nil
}

// Helper methods
func (cm *CalendarManager) getUserParams(userData map[string]interface{}) UserParams {
	orgUnitPath := cm.getString(userData, "orgUnitPath")
	archived := cm.getBool(userData, "archived")
	suspended := cm.getBool(userData, "suspended")

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

func (cm *CalendarManager) getString(data map[string]interface{}, key string) string {
	if val, exists := data[key]; exists {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return ""
}

func (cm *CalendarManager) getBool(data map[string]interface{}, key string) bool {
	if val, exists := data[key]; exists {
		if b, ok := val.(bool); ok {
			return b
		}
	}
	return false
}
