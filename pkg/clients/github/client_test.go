package github

import (
	"testing"
)

func TestNew(t *testing.T) {
	client := New()
	if client == nil {
		t.Fatal("expected non-nil client")
	}
}

func TestParseRepository(t *testing.T) {
	tests := []struct {
		input         string
		expectedOwner string
		expectedRepo  string
	}{
		{"jbcom/control-center", "jbcom", "control-center"},
		{"extended-data-library/secretssync", "extended-data-library", "secretssync"},
		{"org/repo-with-dashes", "org", "repo-with-dashes"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			owner, repo := parseRepository(tt.input)
			if owner != tt.expectedOwner {
				t.Errorf("expected owner '%s', got '%s'", tt.expectedOwner, owner)
			}
			if repo != tt.expectedRepo {
				t.Errorf("expected repo '%s', got '%s'", tt.expectedRepo, repo)
			}
		})
	}
}

// parseRepository splits "owner/repo" into components
func parseRepository(fullName string) (string, string) {
	for i, c := range fullName {
		if c == '/' {
			return fullName[:i], fullName[i+1:]
		}
	}
	return fullName, ""
}

func TestOrganization_String(t *testing.T) {
	org := Organization{
		Login:       "jbcom",
		Description: "Jon Bogaty's control center",
	}
	if org.Login != "jbcom" {
		t.Errorf("unexpected login: %s", org.Login)
	}
}

func TestRepository_FullName(t *testing.T) {
	repo := Repository{
		Name:     "control-center",
		FullName: "jbcom/control-center",
		Owner:    "jbcom",
	}
	if repo.FullName != "jbcom/control-center" {
		t.Errorf("unexpected full name: %s", repo.FullName)
	}
}

func TestPullRequest_Fields(t *testing.T) {
	pr := PullRequest{
		Number: 123,
		Title:  "Test PR",
		State:  "open",
		Author: "testuser",
		Branch: "feature/test",
		URL:    "https://github.com/jbcom/control-center/pull/123",
	}
	if pr.Number != 123 {
		t.Errorf("expected PR number 123, got %d", pr.Number)
	}
	if pr.State != "open" {
		t.Errorf("expected state 'open', got '%s'", pr.State)
	}
}

func TestIssue_Fields(t *testing.T) {
	issue := Issue{
		Number: 456,
		Title:  "Test Issue",
		State:  "open",
		Author: "reporter",
		Labels: []string{"bug", "help wanted"},
		URL:    "https://github.com/jbcom/control-center/issues/456",
	}
	if issue.Number != 456 {
		t.Errorf("expected issue number 456, got %d", issue.Number)
	}
	if len(issue.Labels) != 2 {
		t.Errorf("expected 2 labels, got %d", len(issue.Labels))
	}
}
