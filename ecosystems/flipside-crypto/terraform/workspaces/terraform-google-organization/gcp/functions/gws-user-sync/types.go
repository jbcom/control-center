package main

// UserType represents the type of user
type UserType string

const (
	UserTypeBot      UserType = "bot"
	UserTypeInactive UserType = "inactive"
	UserTypeActive   UserType = "active"
)

// UserParams holds user parameters
type UserParams struct {
	OrgUnitPath string
	Archived    bool
	Suspended   bool
	UserType    UserType
}

// Constants for FlipsideCrypto configuration
const (
	TeamCalendarID = "flipsidecrypto.com_team@group.calendar.google.com"
	Domain         = "flipsidecrypto.com"
	TeamGroupEmail = "team@flipsidecrypto.com"
)
