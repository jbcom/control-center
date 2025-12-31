package ollama

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNew(t *testing.T) {
	client := New("test-key")
	if client == nil {
		t.Fatal("expected non-nil client")
	}
	if client.apiKey != "test-key" {
		t.Errorf("expected apiKey 'test-key', got '%s'", client.apiKey)
	}
}

func TestChat(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.Header.Get("Authorization") != "Bearer test-key" {
			t.Errorf("expected Authorization header")
		}

		resp := ChatResponse{
			Model: "glm-4.6:cloud",
			Message: Message{
				Role:    "assistant",
				Content: "Hello from test",
			},
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := &Client{
		baseURL:    server.URL,
		apiKey:     "test-key",
		httpClient: server.Client(),
	}

	response, err := client.Chat("Hello")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if response != "Hello from test" {
		t.Errorf("expected 'Hello from test', got '%s'", response)
	}
}

func TestReviewCode(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Return a valid JSON review
		review := CodeReview{
			Summary: "Test review",
			Issues: []ReviewIssue{
				{
					Severity:    "medium",
					Category:    "style",
					File:        "test.go",
					Line:        10,
					Description: "Test issue",
					Suggestion:  "Fix it",
				},
			},
			Approved: true,
		}
		reviewJSON, _ := json.Marshal(review)
		resp := ChatResponse{
			Message: Message{
				Role:    "assistant",
				Content: string(reviewJSON),
			},
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := &Client{
		baseURL:    server.URL,
		apiKey:     "test-key",
		httpClient: server.Client(),
	}

	review, err := client.ReviewCode("diff content here")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if review.Summary != "Test review" {
		t.Errorf("expected summary 'Test review', got '%s'", review.Summary)
	}
	if len(review.Issues) != 1 {
		t.Errorf("expected 1 issue, got %d", len(review.Issues))
	}
}

func TestTriageIssue(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		triage := IssueTriage{
			Agent:      "jules",
			Confidence: 0.9,
			Reasoning:  "Multi-file change needed",
			Prompt:     "Implement feature X",
		}
		triageJSON, _ := json.Marshal(triage)
		resp := ChatResponse{
			Message: Message{
				Role:    "assistant",
				Content: string(triageJSON),
			},
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := &Client{
		baseURL:    server.URL,
		apiKey:     "test-key",
		httpClient: server.Client(),
	}

	triage, err := client.TriageIssue("Issue title", "Issue body")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if triage.Agent != "jules" {
		t.Errorf("expected agent 'jules', got '%s'", triage.Agent)
	}
}
