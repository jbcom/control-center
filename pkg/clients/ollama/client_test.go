package ollama

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNewClient(t *testing.T) {
	client := NewClient(Config{APIKey: "test-key"})
	if client == nil {
		t.Fatal("expected non-nil client")
	}
	if client.apiKey != "test-key" {
		t.Errorf("expected apiKey 'test-key', got '%s'", client.apiKey)
	}
	if client.model != DefaultModel {
		t.Errorf("expected model '%s', got '%s'", DefaultModel, client.model)
	}
	if client.host != DefaultHost {
		t.Errorf("expected host '%s', got '%s'", DefaultHost, client.host)
	}
}

func TestNewClientCustomConfig(t *testing.T) {
	client := NewClient(Config{
		APIKey: "test-key",
		Model:  "custom-model",
		Host:   "https://custom.ollama.com",
	})
	if client.model != "custom-model" {
		t.Errorf("expected model 'custom-model', got '%s'", client.model)
	}
	if client.host != "https://custom.ollama.com" {
		t.Errorf("expected host 'https://custom.ollama.com', got '%s'", client.host)
	}
}

func TestChat(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.Header.Get("Authorization") != "Bearer test-key" {
			t.Errorf("expected Authorization header with Bearer token")
		}

		resp := ChatResponse{
			Model: DefaultModel,
			Message: Message{
				Role:    "assistant",
				Content: "Hello from test",
			},
			Done: true,
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := NewClient(Config{
		APIKey: "test-key",
		Host:   server.URL,
	})

	response, err := client.Chat(context.Background(), "Hello")
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
					Severity:   "medium",
					Category:   "style",
					Message:    "Test issue",
					Suggestion: "Fix it",
				},
			},
			Approval: "approve",
			Comments: "Looks good",
		}
		reviewJSON, _ := json.Marshal(review)
		resp := ChatResponse{
			Message: Message{
				Role:    "assistant",
				Content: string(reviewJSON),
			},
			Done: true,
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := NewClient(Config{
		APIKey: "test-key",
		Host:   server.URL,
	})

	review, err := client.ReviewCode(context.Background(), "diff content here")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if review.Summary != "Test review" {
		t.Errorf("expected summary 'Test review', got '%s'", review.Summary)
	}
	if len(review.Issues) != 1 {
		t.Errorf("expected 1 issue, got %d", len(review.Issues))
	}
	if review.Approval != "approve" {
		t.Errorf("expected approval 'approve', got '%s'", review.Approval)
	}
}

func TestTriageIssue(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		triage := IssueTriage{
			Complexity:      "moderate",
			Agent:           "jules",
			Reasoning:       "Multi-file change needed",
			Priority:        "medium",
			EstimatedEffort: "hours",
		}
		triageJSON, _ := json.Marshal(triage)
		resp := ChatResponse{
			Message: Message{
				Role:    "assistant",
				Content: string(triageJSON),
			},
			Done: true,
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := NewClient(Config{
		APIKey: "test-key",
		Host:   server.URL,
	})

	triage, err := client.TriageIssue(context.Background(), "Issue title", "Issue body", []string{"bug"})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if triage.Agent != "jules" {
		t.Errorf("expected agent 'jules', got '%s'", triage.Agent)
	}
	if triage.Complexity != "moderate" {
		t.Errorf("expected complexity 'moderate', got '%s'", triage.Complexity)
	}
}

func TestAnalyzeFailure(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		analysis := FailureAnalysis{
			RootCause:            "Missing dependency",
			FixSuggestion:        "Run npm install",
			VerificationCommands: []string{"npm test"},
			Confidence:           "high",
		}
		analysisJSON, _ := json.Marshal(analysis)
		resp := ChatResponse{
			Message: Message{
				Role:    "assistant",
				Content: string(analysisJSON),
			},
			Done: true,
		}
		if err := json.NewEncoder(w).Encode(resp); err != nil {
			t.Fatalf("failed to encode response: %v", err)
		}
	}))
	defer server.Close()

	client := NewClient(Config{
		APIKey: "test-key",
		Host:   server.URL,
	})

	analysis, err := client.AnalyzeFailure(context.Background(), "Error: module not found")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if analysis.RootCause != "Missing dependency" {
		t.Errorf("expected root cause 'Missing dependency', got '%s'", analysis.RootCause)
	}
	if analysis.Confidence != "high" {
		t.Errorf("expected confidence 'high', got '%s'", analysis.Confidence)
	}
}
