package serviceresolver

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/hashicorp/go-retryablehttp"
	"gopkg.in/yaml.v3"
)

// GitHubTreeItem represents an item in the GitHub API tree response
type GitHubTreeItem struct {
	Path string `json:"path"`
	Type string `json:"type"`
	URL  string `json:"url"`
}

// GitHubTreeResponse represents the GitHub API tree response
type GitHubTreeResponse struct {
	Tree []GitHubTreeItem `json:"tree"`
}

// GitHubBlobResponse represents a GitHub API blob response
type GitHubBlobResponse struct {
	Content  string `json:"content"`
	Encoding string `json:"encoding"`
}

type GithubProvider struct {
	url    string
	dir    *string
	client *http.Client
}

func NewGithubProvider(cfg ServiceResolverConfig) (*GithubProvider, error) {
	if cfg.URL == nil {
		return nil, fmt.Errorf("url not set")
	}

	url := *cfg.URL

	// Expected format: https://github.com/MinBZK/poc-machine-law/tree/main/law
	// Convert to: https://api.github.com/repos/MinBZK/poc-machine-law/git/trees/main?recursive=1
	if !strings.Contains(url, "github.com") {
		return nil, fmt.Errorf("not a GitHub URL: %s", url)
	}

	parts := strings.SplitN(url, "/", 8)
	if len(parts) < 7 {
		return nil, fmt.Errorf("invalid GitHub tree URL format: %s", url)
	}

	owner := parts[3]
	repo := parts[4]
	branch := parts[6]

	var dir *string
	if len(parts) > 7 {
		dir = &parts[7]
	}

	apiURL := fmt.Sprintf("https://api.github.com/repos/%s/%s/git/trees/%s?recursive=1", owner, repo, branch)

	client := retryablehttp.NewClient()
	client.RetryMax = 10

	return &GithubProvider{
		url:    apiURL,
		dir:    dir,
		client: client.StandardClient(),
	}, nil
}

// fetchGitHubYAMLFiles fetches all YAML file URLs from a GitHub tree
func (p *GithubProvider) Fetch() ([]ServiceSpec, error) {
	req, err := http.NewRequest(http.MethodGet, p.url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Add GitHub API headers
	req.Header.Set("Accept", "application/vnd.github.v3+json")

	resp, err := p.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch tree from GitHub API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("GitHub API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var treeResp GitHubTreeResponse
	if err := json.Unmarshal(body, &treeResp); err != nil {
		return nil, fmt.Errorf("failed to parse GitHub tree response: %w", err)
	}

	var yamlFiles []string
	for _, item := range treeResp.Tree {
		if p.dir != nil && !strings.HasPrefix(item.Path, *p.dir) {
			continue
		}

		if item.Type == "blob" && strings.HasSuffix(strings.ToLower(item.Path), ".yaml") || strings.HasSuffix(strings.ToLower(item.Path), ".yml") {
			yamlFiles = append(yamlFiles, item.URL)
		}
	}

	rules := make([]ServiceSpec, 0, len(yamlFiles))
	// Process each YAML file
	for _, fileURL := range yamlFiles {
		rule, err := p.parseYaml(fileURL)
		if err != nil {
			fmt.Printf("Error processing file %s: %v\n", fileURL, err)
			continue
		}

		rules = append(rules, rule)
	}

	return rules, nil
}

// parseYaml fetches and parses a single YAML rule from GitHub
func (p *GithubProvider) parseYaml(url string) (ServiceSpec, error) {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return ServiceSpec{}, fmt.Errorf("failed to create request: %w", err)
	}

	// Add GitHub API headers
	req.Header.Set("Accept", "application/vnd.github.v3+json")

	resp, err := p.client.Do(req)
	if err != nil {
		return ServiceSpec{}, fmt.Errorf("failed to fetch blob: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return ServiceSpec{}, fmt.Errorf("GitHub API returned status %d for blob", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return ServiceSpec{}, fmt.Errorf("failed to read blob response: %w", err)
	}

	var blobResp GitHubBlobResponse
	if err := json.Unmarshal(body, &blobResp); err != nil {
		return ServiceSpec{}, fmt.Errorf("failed to parse blob response: %w", err)
	}

	// Decode base64 content
	var content []byte
	if blobResp.Encoding == "base64" {
		content, err = base64.StdEncoding.DecodeString(blobResp.Content)
		if err != nil {
			return ServiceSpec{}, fmt.Errorf("failed to decode base64 content: %w", err)
		}
	} else {
		content = []byte(blobResp.Content)
	}

	// Parse YAML
	var rule ServiceSpec
	if err := yaml.Unmarshal(content, &rule); err != nil {
		return ServiceSpec{}, fmt.Errorf("failed to parse YAML: %w", err)
	}

	return rule, nil
}

type DiskProvider struct {
	dir string
}

func NewDiskProvider(cfg ServiceResolverConfig) (*DiskProvider, error) {
	if cfg.DIR == nil {
		return nil, fmt.Errorf("dir is not set")
	}

	return &DiskProvider{
		dir: *cfg.DIR,
	}, nil
}

// fetchGitHubYAMLFiles fetches all YAML file URLs from a GitHub tree
func (p *DiskProvider) Fetch() ([]ServiceSpec, error) {
	// First, evaluate the symlink to get the actual path
	realPath, err := filepath.EvalSymlinks(p.dir)
	if err != nil {
		return nil, fmt.Errorf("failed to evaluate symlink %s: %w", p.dir, err)
	}

	// Find all .yaml and .yml files recursively
	var yamlFiles []string

	if err := filepath.Walk(realPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			ext := strings.ToLower(filepath.Ext(path))
			if ext == ".yaml" || ext == ".yml" {
				yamlFiles = append(yamlFiles, path)
			}
		}

		return nil
	}); err != nil {
		return nil, fmt.Errorf("walk: %w", err)
	}

	rules := make([]ServiceSpec, 0, len(yamlFiles))
	// Load each rule file
	for _, path := range yamlFiles {
		data, err := os.ReadFile(path)
		if err != nil {
			fmt.Printf("Error reading file %s: %v\n", path, err)
			continue
		}

		rule := ServiceSpec{}
		if err := yaml.Unmarshal(data, &rule); err != nil {
			fmt.Printf("Error parsing YAML from %s: %v\n", path, err)
			continue
		}

		rules = append(rules, rule)
	}

	return rules, nil

}

type RuleSpecProvider string

const (
	RSGithubProvider RuleSpecProvider = "github"
	RSDiskProvider   RuleSpecProvider = "disk"
)

var DefaultServiceResolverCfg ServiceResolverConfig = ServiceResolverConfig{
	Provider: RSDiskProvider,
	DIR:      ptr("services"),
}

type Provider interface {
	Fetch() ([]ServiceSpec, error)
}

func ProviderFactory(cfg ServiceResolverConfig) (Provider, error) {
	var provider Provider
	var err error
	switch cfg.Provider {
	case RSGithubProvider:
		provider, err = NewGithubProvider(cfg)
		if err != nil {
			return nil, err
		}
	case RSDiskProvider:
		provider, err = NewDiskProvider(cfg)
		if err != nil {
			return nil, err
		}
	default:
		return nil, fmt.Errorf("unknown provider: %s", cfg.Provider)
	}

	return provider, nil
}
