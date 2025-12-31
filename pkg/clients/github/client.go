package github

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os/exec"
	"strings"
	"time"

	log "github.com/sirupsen/logrus"
)

// Client provides access to GitHub API and gh CLI
type Client struct {
	token      string
	httpClient *http.Client
	baseURL    string
}

// NewClient creates a new GitHub client
func NewClient(token string) *Client {
	return &Client{
		token: token,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		baseURL: "https://api.github.com",
	}
}

// Organization represents a GitHub organization
type Organization struct {
	Org           string `json:"org"`
	Domain        string `json:"domain"`
	ControlCenter string `json:"control_center"`
	Type          string `json:"type"`
}

// Repository represents a GitHub repository
type Repository struct {
	Owner    string `json:"owner"`
	Name     string `json:"name"`
	FullName string `json:"full_name"`
	Language string `json:"language"`
	Archived bool   `json:"archived"`
}

// PullRequest represents a GitHub pull request
type PullRequest struct {
	Number    int       `json:"number"`
	Title     string    `json:"title"`
	State     string    `json:"state"`
	Draft     bool      `json:"draft"`
	UpdatedAt time.Time `json:"updatedAt"`
	Author    string    `json:"author"`
}

// Issue represents a GitHub issue
type Issue struct {
	Number    int      `json:"number"`
	Title     string   `json:"title"`
	State     string   `json:"state"`
	Labels    []string `json:"labels"`
	Assignees []string `json:"assignees"`
}

// ListOrganizations lists organizations from the org-registry.json
func (c *Client) ListOrganizations(ctx context.Context, registryPath string) ([]Organization, error) {
	// Use gh CLI to read the registry
	out, err := c.runGH(ctx, "api", "repos/jbcom/control-center/contents/.github/org-registry.json",
		"--jq", ".content", "-H", "Accept: application/vnd.github.v3+json")
	if err != nil {
		return nil, fmt.Errorf("failed to fetch org-registry: %w", err)
	}

	log.WithField("size", len(out)).Debug("Fetched org-registry from GitHub")

	// Parse the registry (simplified - in real impl would decode base64)
	var orgs []Organization
	// This would be populated from the registry
	return orgs, nil
}

// ListRepositories lists repositories for an organization
func (c *Client) ListRepositories(ctx context.Context, org string) ([]Repository, error) {
	out, err := c.runGH(ctx, "repo", "list", org,
		"--json", "owner,name,language,isArchived",
		"--limit", "100",
		"--no-archived")
	if err != nil {
		return nil, fmt.Errorf("failed to list repos for %s: %w", org, err)
	}

	var repos []Repository
	if err := json.Unmarshal([]byte(out), &repos); err != nil {
		return nil, fmt.Errorf("failed to parse repos: %w", err)
	}

	return repos, nil
}

// ListOpenPRs lists open pull requests for a repository
func (c *Client) ListOpenPRs(ctx context.Context, repo string) ([]PullRequest, error) {
	out, err := c.runGH(ctx, "pr", "list", "--repo", repo,
		"--state", "open",
		"--json", "number,title,state,isDraft,updatedAt,author")
	if err != nil {
		return nil, fmt.Errorf("failed to list PRs for %s: %w", repo, err)
	}

	var prs []PullRequest
	if err := json.Unmarshal([]byte(out), &prs); err != nil {
		return nil, fmt.Errorf("failed to parse PRs: %w", err)
	}

	return prs, nil
}

// ListOpenIssues lists open issues for a repository
func (c *Client) ListOpenIssues(ctx context.Context, repo string) ([]Issue, error) {
	out, err := c.runGH(ctx, "issue", "list", "--repo", repo,
		"--state", "open",
		"--json", "number,title,state,labels,assignees")
	if err != nil {
		return nil, fmt.Errorf("failed to list issues for %s: %w", repo, err)
	}

	var issues []Issue
	if err := json.Unmarshal([]byte(out), &issues); err != nil {
		return nil, fmt.Errorf("failed to parse issues: %w", err)
	}

	return issues, nil
}

// AddLabel adds a label to a PR or issue
func (c *Client) AddLabel(ctx context.Context, repo string, number int, label string) error {
	_, err := c.runGH(ctx, "pr", "edit", fmt.Sprintf("%d", number),
		"--repo", repo, "--add-label", label)
	return err
}

// PostComment posts a comment on a PR or issue
func (c *Client) PostComment(ctx context.Context, repo string, number int, body string) error {
	_, err := c.runGH(ctx, "pr", "comment", fmt.Sprintf("%d", number),
		"--repo", repo, "--body", body)
	return err
}

// TriggerWorkflow triggers a workflow dispatch
func (c *Client) TriggerWorkflow(ctx context.Context, repo, workflow string, inputs map[string]string) error {
	args := []string{"workflow", "run", workflow, "--repo", repo}
	for k, v := range inputs {
		args = append(args, "-f", fmt.Sprintf("%s=%s", k, v))
	}
	_, err := c.runGH(ctx, args...)
	return err
}

// runGH runs the gh CLI command
func (c *Client) runGH(ctx context.Context, args ...string) (string, error) {
	cmd := exec.CommandContext(ctx, "gh", args...)
	cmd.Env = append(cmd.Environ(), fmt.Sprintf("GH_TOKEN=%s", c.token))

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	log.WithField("args", strings.Join(args, " ")).Debug("Running gh command")

	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("gh %s failed: %w: %s", strings.Join(args, " "), err, stderr.String())
	}

	return stdout.String(), nil
}

// doRequest performs an HTTP request to the GitHub API
func (c *Client) doRequest(ctx context.Context, method, path string, body interface{}) ([]byte, error) {
	var bodyReader io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		bodyReader = bytes.NewReader(jsonBody)
	}

	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, bodyReader)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("GitHub API error %d: %s", resp.StatusCode, string(respBody))
	}

	return respBody, nil
}
