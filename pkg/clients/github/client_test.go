package github

import (
	"testing"
)

func TestNewClient(t *testing.T) {
	client := NewClient("test-token")
	if client == nil {
		t.Fatal("expected non-nil client")
	}
	if client.token != "test-token" {
		t.Errorf("expected token 'test-token', got '%s'", client.token)
	}
	if client.baseURL != "https://api.github.com" {
		t.Errorf("expected baseURL 'https://api.github.com', got '%s'", client.baseURL)
	}
}

func TestOrganizationStruct(t *testing.T) {
	org := Organization{
		Org:           "jbcom",
		Domain:        "jonbogaty.com",
		ControlCenter: "jbcom/control-center",
		Type:          "enterprise",
	}
	if org.Org != "jbcom" {
		t.Errorf("unexpected org: %s", org.Org)
	}
	if org.Type != "enterprise" {
		t.Errorf("unexpected type: %s", org.Type)
	}
	if org.Domain != "jonbogaty.com" {
		t.Errorf("unexpected domain: %s", org.Domain)
	}
	if org.ControlCenter != "jbcom/control-center" {
		t.Errorf("unexpected control center: %s", org.ControlCenter)
	}
}

func TestRepositoryStruct(t *testing.T) {
	repo := Repository{
		Name:     "control-center",
		FullName: "jbcom/control-center",
		Owner:    "jbcom",
		Language: "Go",
		Archived: false,
	}
	if repo.FullName != "jbcom/control-center" {
		t.Errorf("unexpected full name: %s", repo.FullName)
	}
	if repo.Language != "Go" {
		t.Errorf("unexpected language: %s", repo.Language)
	}
	if repo.Name != "control-center" {
		t.Errorf("unexpected name: %s", repo.Name)
	}
	if repo.Owner != "jbcom" {
		t.Errorf("unexpected owner: %s", repo.Owner)
	}
	if repo.Archived {
		t.Error("expected Archived to be false")
	}
}

func TestPullRequestStruct(t *testing.T) {
	pr := PullRequest{
		Number: 123,
		Title:  "Test PR",
		State:  "open",
		Draft:  false,
		Author: "testuser",
	}
	if pr.Number != 123 {
		t.Errorf("expected PR number 123, got %d", pr.Number)
	}
	if pr.State != "open" {
		t.Errorf("expected state 'open', got '%s'", pr.State)
	}
	if pr.Draft {
		t.Error("expected Draft to be false")
	}
	if pr.Title != "Test PR" {
		t.Errorf("expected title 'Test PR', got '%s'", pr.Title)
	}
	if pr.Author != "testuser" {
		t.Errorf("expected author 'testuser', got '%s'", pr.Author)
	}
}

func TestIssueStruct(t *testing.T) {
	issue := Issue{
		Number:    456,
		Title:     "Test Issue",
		State:     "open",
		Labels:    []string{"bug", "help wanted"},
		Assignees: []string{"user1"},
	}
	if issue.Number != 456 {
		t.Errorf("expected issue number 456, got %d", issue.Number)
	}
	if len(issue.Labels) != 2 {
		t.Errorf("expected 2 labels, got %d", len(issue.Labels))
	}
	if len(issue.Assignees) != 1 {
		t.Errorf("expected 1 assignee, got %d", len(issue.Assignees))
	}
	if issue.Title != "Test Issue" {
		t.Errorf("expected title 'Test Issue', got '%s'", issue.Title)
	}
	if issue.State != "open" {
		t.Errorf("expected state 'open', got '%s'", issue.State)
	}
}
