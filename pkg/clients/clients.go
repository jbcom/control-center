package clients

import (
	"context"

	"github.com/jbcom/control-center/pkg/clients/jules"
)

// JulesClient defines the interface for the Jules client.
type JulesClient interface {
	CreateSession(ctx context.Context, repo, branch, prompt string) (*jules.Session, error)
}

// GitHubClient defines the interface for the GitHub client.
type GitHubClient interface {
	PostComment(ctx context.Context, repo string, number int, body string) error
}
