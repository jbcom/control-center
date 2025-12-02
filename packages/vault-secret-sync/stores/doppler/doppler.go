package doppler

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"

	"github.com/robertlestak/vault-secret-sync/pkg/driver"
	log "github.com/sirupsen/logrus"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

const (
	defaultBaseURL = "https://api.doppler.com/v3"
)

// DopplerClient implements the secret store interface for Doppler
type DopplerClient struct {
	// Project is the Doppler project name
	Project string `yaml:"project,omitempty" json:"project,omitempty"`
	// Config is the Doppler config/environment name
	Config string `yaml:"config,omitempty" json:"config,omitempty"`
	// Token is the Doppler service token for authentication
	Token string `yaml:"token,omitempty" json:"token,omitempty"`
	// BaseURL allows overriding the API endpoint (for testing)
	BaseURL string `yaml:"baseUrl,omitempty" json:"baseUrl,omitempty"`
	// Merge determines whether to merge with existing secrets or replace
	Merge *bool `yaml:"merge,omitempty" json:"merge,omitempty"`
	// NameTransform transforms secret names (upper, lower, none)
	NameTransform string `yaml:"nameTransform,omitempty" json:"nameTransform,omitempty"`

	httpClient *http.Client `yaml:"-" json:"-"`
}

// DeepCopyInto copies the receiver into out
func (in *DopplerClient) DeepCopyInto(out *DopplerClient) {
	*out = *in
	if in.Merge != nil {
		in, out := &in.Merge, &out.Merge
		*out = new(bool)
		**out = **in
	}
}

// DeepCopy creates a deep copy of the client
func (in *DopplerClient) DeepCopy() *DopplerClient {
	if in == nil {
		return nil
	}
	out := new(DopplerClient)
	in.DeepCopyInto(out)
	return out
}

// Validate ensures required fields are set
func (c *DopplerClient) Validate() error {
	l := log.WithFields(log.Fields{
		"action": "Validate",
		"driver": "doppler",
	})
	l.Trace("start")

	if c.Project == "" {
		return errors.New("project is required")
	}
	if c.Config == "" {
		return errors.New("config is required")
	}
	if c.Token == "" {
		return errors.New("token is required")
	}
	return nil
}

// NewClient creates a new Doppler client from configuration
func NewClient(cfg *DopplerClient) (*DopplerClient, error) {
	l := log.WithFields(log.Fields{
		"action": "NewClient",
		"driver": "doppler",
	})
	l.Trace("start")

	if cfg == nil {
		return nil, errors.New("config is nil")
	}

	vc := cfg.DeepCopy()

	// Log without exposing sensitive token
	l.Debugf("client created for project=%s config=%s", vc.Project, vc.Config)
	l.Trace("end")
	return vc, nil
}

// Init initializes the Doppler client
func (c *DopplerClient) Init(ctx context.Context) error {
	l := log.WithFields(log.Fields{
		"action": "Init",
		"driver": "doppler",
	})
	l.Trace("start")

	if err := c.Validate(); err != nil {
		return err
	}

	if c.BaseURL == "" {
		c.BaseURL = defaultBaseURL
	}

	c.httpClient = &http.Client{
		Timeout: 30 * time.Second,
	}

	l.Trace("end")
	return nil
}

// Driver returns the driver name
func (c *DopplerClient) Driver() driver.DriverName {
	return driver.DriverNameDoppler
}

// GetPath returns the path identifier for this store
func (c *DopplerClient) GetPath() string {
	return fmt.Sprintf("%s/%s", c.Project, c.Config)
}

// Meta returns metadata about the client configuration
func (c *DopplerClient) Meta() map[string]any {
	md := make(map[string]any)
	jd, err := json.Marshal(c)
	if err != nil {
		return md
	}
	err = json.Unmarshal(jd, &md)
	if err != nil {
		return md
	}
	// Remove sensitive data
	delete(md, "token")
	return md
}

// transformName applies name transformation rules
func (c *DopplerClient) transformName(name string) string {
	switch strings.ToLower(c.NameTransform) {
	case "upper":
		return strings.ToUpper(name)
	case "lower":
		return strings.ToLower(name)
	case "none":
		return name
	default:
		return strings.ToUpper(name) // Doppler convention is UPPER_SNAKE_CASE
	}
}

// doRequest performs an HTTP request to the Doppler API
func (c *DopplerClient) doRequest(ctx context.Context, method, path string, body interface{}) ([]byte, error) {
	l := log.WithFields(log.Fields{
		"action": "doRequest",
		"method": method,
		"path":   path,
	})

	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonBody)
	}

	url := fmt.Sprintf("%s%s", c.BaseURL, path)
	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.Token))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		// Log detailed error for debugging but don't expose in error message
		// as response body may contain sensitive information
		l.Debugf("API error: status=%d", resp.StatusCode)
		return nil, fmt.Errorf("API error: status=%d", resp.StatusCode)
	}

	return respBody, nil
}

// GetSecret retrieves a secret from Doppler (not typically used for sync targets)
func (c *DopplerClient) GetSecret(ctx context.Context, name string) ([]byte, error) {
	l := log.WithFields(log.Fields{
		"action": "GetSecret",
		"driver": "doppler",
		"name":   name,
	})
	l.Trace("start")

	path := fmt.Sprintf("/configs/config/secret?project=%s&config=%s&name=%s",
		url.QueryEscape(c.Project), url.QueryEscape(c.Config), url.QueryEscape(c.transformName(name)))

	respBody, err := c.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}

	var result struct {
		Name  string `json:"name"`
		Value struct {
			Raw string `json:"raw"`
		} `json:"value"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return []byte(result.Value.Raw), nil
}

// WriteSecret writes secrets to Doppler
func (c *DopplerClient) WriteSecret(ctx context.Context, meta metav1.ObjectMeta, path string, bSecrets []byte) ([]byte, error) {
	l := log.WithFields(log.Fields{
		"action": "WriteSecret",
		"path":   path,
		"driver": "doppler",
	})
	l.Trace("start")
	defer l.Trace("end")

	if c == nil {
		return nil, errors.New("nil client")
	}

	// Parse the secrets
	secrets := make(map[string]interface{})
	if err := json.Unmarshal(bSecrets, &secrets); err != nil {
		return nil, fmt.Errorf("failed to unmarshal secrets: %w", err)
	}

	// Transform secrets to Doppler format
	dopplerSecrets := make(map[string]string)
	for k, v := range secrets {
		// Skip empty values
		if v == nil || v == "" {
			l.Debugf("skipping empty secret: %s", k)
			continue
		}

		name := c.transformName(k)
		switch val := v.(type) {
		case string:
			dopplerSecrets[name] = val
		case map[string]interface{}, []interface{}:
			// JSON encode complex types
			jsonVal, err := json.Marshal(val)
			if err != nil {
				l.Warnf("failed to marshal complex secret %s: %v", k, err)
				continue
			}
			dopplerSecrets[name] = string(jsonVal)
		default:
			dopplerSecrets[name] = fmt.Sprintf("%v", val)
		}
	}

	if len(dopplerSecrets) == 0 {
		l.Debug("no secrets to write")
		return nil, nil
	}

	// Use the secrets update endpoint
	// If merge is true, add ?merge=true to merge with existing secrets
	// If merge is false (or nil), Doppler replaces all secrets by default
	apiPath := "/configs/config/secrets"
	if c.Merge != nil && *c.Merge {
		apiPath += "?merge=true"
	}

	reqBody := map[string]interface{}{
		"project": c.Project,
		"config":  c.Config,
		"secrets": dopplerSecrets,
	}

	_, err := c.doRequest(ctx, http.MethodPost, apiPath, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to write secrets: %w", err)
	}

	l.Infof("successfully wrote %d secrets to Doppler project=%s config=%s",
		len(dopplerSecrets), c.Project, c.Config)
	return nil, nil
}

// DeleteSecret deletes secrets from Doppler
func (c *DopplerClient) DeleteSecret(ctx context.Context, name string) error {
	l := log.WithFields(log.Fields{
		"action": "DeleteSecret",
		"driver": "doppler",
		"name":   name,
	})
	l.Trace("start")
	defer l.Trace("end")

	// If name is empty, delete all secrets (for merge=false mode)
	if name == "" {
		// List all secrets first
		secrets, err := c.ListSecrets(ctx, "")
		if err != nil {
			return fmt.Errorf("failed to list secrets: %w", err)
		}

		// Delete each secret - names from ListSecrets are already in Doppler format
		// so we use deleteSingleSecretRaw to avoid double transformation
		for _, secretName := range secrets {
			if err := c.deleteSingleSecretRaw(ctx, secretName); err != nil {
				l.Warnf("failed to delete secret %s: %v", secretName, err)
			}
		}
		return nil
	}

	// For explicit name, apply transformation
	return c.deleteSingleSecretRaw(ctx, c.transformName(name))
}

// deleteSingleSecretRaw deletes a single secret from Doppler using the exact name provided
// (no transformation applied - caller is responsible for providing the correct name)
func (c *DopplerClient) deleteSingleSecretRaw(ctx context.Context, name string) error {
	apiPath := "/configs/config/secret"
	reqBody := map[string]interface{}{
		"project": c.Project,
		"config":  c.Config,
		"name":    name,
	}

	_, err := c.doRequest(ctx, http.MethodDelete, apiPath, reqBody)
	return err
}

// ListSecrets lists all secrets in the Doppler config
func (c *DopplerClient) ListSecrets(ctx context.Context, path string) ([]string, error) {
	l := log.WithFields(log.Fields{
		"action": "ListSecrets",
		"driver": "doppler",
	})
	l.Trace("start")
	defer l.Trace("end")

	apiPath := fmt.Sprintf("/configs/config/secrets?project=%s&config=%s",
		url.QueryEscape(c.Project), url.QueryEscape(c.Config))

	respBody, err := c.doRequest(ctx, http.MethodGet, apiPath, nil)
	if err != nil {
		return nil, err
	}

	var result struct {
		Secrets map[string]struct {
			Raw string `json:"raw"`
		} `json:"secrets"`
	}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	secrets := make([]string, 0, len(result.Secrets))
	for name := range result.Secrets {
		secrets = append(secrets, name)
	}

	return secrets, nil
}

// Close cleans up the client
func (c *DopplerClient) Close() error {
	c.httpClient = nil
	return nil
}

// SetDefaults applies default values from configuration
func (c *DopplerClient) SetDefaults(cfg any) error {
	jd, err := json.Marshal(cfg)
	if err != nil {
		return err
	}
	nc := &DopplerClient{}
	err = json.Unmarshal(jd, &nc)
	if err != nil {
		return err
	}

	if c.Project == "" && nc.Project != "" {
		c.Project = nc.Project
	}
	if c.Config == "" && nc.Config != "" {
		c.Config = nc.Config
	}
	if c.Token == "" && nc.Token != "" {
		c.Token = nc.Token
	}
	if c.BaseURL == "" && nc.BaseURL != "" {
		c.BaseURL = nc.BaseURL
	}
	if c.NameTransform == "" && nc.NameTransform != "" {
		c.NameTransform = nc.NameTransform
	}
	// Default to merge mode
	if c.Merge == nil {
		c.Merge = nc.Merge
	}

	return nil
}
