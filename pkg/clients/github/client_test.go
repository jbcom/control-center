package github

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
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

func TestClosePR(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check method and path
		if r.Method != http.MethodPatch {
			t.Errorf("Expected method PATCH, got %s", r.Method)
		}
		expectedPath := "/repos/jbcom/control-center/pulls/123"
		if r.URL.Path != expectedPath {
			t.Errorf("Expected path %s, got %s", expectedPath, r.URL.Path)
		}

		// Check headers
		if r.Header.Get("Authorization") != "token test-token" {
			t.Errorf("Missing or incorrect Authorization header")
		}
		if r.Header.Get("Accept") != "application/vnd.github.v3+json" {
			t.Errorf("Missing or incorrect Accept header")
		}

		// Check body
		var body map[string]string
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Fatalf("Failed to decode request body: %v", err)
		}
		if state, ok := body["state"]; !ok || state != "closed" {
			t.Errorf("Expected state 'closed', got '%s'", state)
		}

		// Send response
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"state": "closed"}`))
	}))
	defer server.Close()

	client := NewClient("test-token")
	client.baseURL = server.URL // Point client to the test server

	err := client.ClosePR(context.Background(), "jbcom/control-center", 123)
	if err != nil {
		t.Errorf("ClosePR failed: %v", err)
	}
}

func TestClosePR_Error(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte(`{"message": "Not Found"}`))
	}))
	defer server.Close()

	client := NewClient("test-token")
	client.baseURL = server.URL

	err := client.ClosePR(context.Background(), "jbcom/control-center", 456)
	if err == nil {
		t.Error("Expected an error for non-200 status code, but got nil")
	}
}
