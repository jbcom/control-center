package jules

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCreateSession_EmptyPrompt(t *testing.T) {
	client := NewClient(Config{})

	_, err := client.CreateSession(context.Background(), "owner/repo", "main", "")
	assert.Error(t, err)
	assert.Equal(t, "prompt cannot be empty", err.Error())

	_, err = client.CreateSession(context.Background(), "owner/repo", "main", "   ")
	assert.Error(t, err)
	assert.Equal(t, "prompt cannot be empty", err.Error())
}

func TestCreateSession_Success(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		assert.Equal(t, "/v1alpha/sessions", r.URL.Path)
		assert.Equal(t, "POST", r.Method)

		var req CreateSessionRequest
		err := json.NewDecoder(r.Body).Decode(&req)
		require.NoError(t, err)
		assert.Equal(t, "test prompt", req.Prompt)
		assert.Equal(t, "sources/github/owner/repo", req.SourceContext.Source)
		assert.Equal(t, "main", req.SourceContext.GitHubRepoContext.StartingBranch)

		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(Session{
			Name:   "sessions/123",
			State:  "CREATING",
			Prompt: "test prompt",
		})
	}))
	defer server.Close()

	client := NewClient(Config{Host: server.URL})

	session, err := client.CreateSession(context.Background(), "owner/repo", "main", "test prompt")
	require.NoError(t, err)
	assert.NotNil(t, session)
	assert.Equal(t, "sessions/123", session.Name)
}
