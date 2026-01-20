package ruleresolver

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	// "github.com/goccy/go-yaml"
	"gopkg.in/yaml.v3"
)

const (
	LawBaseDir = "law"
)

var (
	loaded                    bool = false
	ruleSpec                  []RuleSpec
	lawsByService             map[string]map[string]struct{}
	discoverableLawsByService map[string]map[string]map[string]struct{}
	once                      sync.Once
	ruleSpecCache             sync.Map
)

// RuleResolve handles rule resolution and lookup
type RuleResolve struct {
	rulesDir                  string
	rules                     []RuleSpec
	lawsByService             map[string]map[string]struct{}
	discoverableLawsByService map[string]map[string]map[string]struct{}
	mu                        sync.RWMutex
}

type RuleResolver interface {
	RulesDataFrame() []map[string]any
	GetRules() []RuleSpec
	GetRuleSpec(law string, referenceDate time.Time, service string) (RuleSpec, error)
	GetServiceLaws() map[string][]string
	GetDiscoverableServiceLaws(discoverableBy string) map[string][]string
}

// New creates a new rule resolver
func New() (resolver *RuleResolve, err error) {
	once.Do(func() {
		ruleSpec, lawsByService, discoverableLawsByService, err = rulesLoad(LawBaseDir)
		if err != nil {
			return
		}

		loaded = true
	})

	if err != nil {
		return nil, fmt.Errorf("load rules: %w", err)
	}

	if !loaded {
		return nil, fmt.Errorf("rules not loaded yet")
	}

	return &RuleResolve{
		rulesDir:                  LawBaseDir,
		rules:                     ruleSpec,
		lawsByService:             lawsByService,
		discoverableLawsByService: discoverableLawsByService,
	}, nil
}

func rulesLoad(dir string) ([]RuleSpec, map[string]map[string]struct{}, map[string]map[string]map[string]struct{}, error) {
	// Clear existing data
	lawsByService := make(map[string]map[string]struct{})
	lawsByServiceWithDiscoverable := make(map[string]map[string]map[string]struct{})

	// Find all .yaml and .yml files recursively
	var yamlFiles []string

	err := func() error {
		// First, evaluate the symlink to get the actual path
		realPath, err := filepath.EvalSymlinks(dir)
		if err != nil {
			return fmt.Errorf("failed to evaluate symlink %s: %w", dir, err)
		}

		// Now walk the real path
		return filepath.Walk(realPath, func(path string, info os.FileInfo, err error) error {
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
		})
	}()

	if err != nil {
		return nil, nil, nil, err
	}

	rules := make([]RuleSpec, 0, len(yamlFiles))
	// Load each rule file
	for _, path := range yamlFiles {
		data, err := os.ReadFile(path)
		if err != nil {
			fmt.Printf("Error reading file %s: %v\n", path, err)
			continue
		}

		rule := RuleSpec{}
		if err := yaml.Unmarshal(data, &rule); err != nil {
			fmt.Printf("Error parsing YAML from %s: %v\n", path, err)
			continue
		}

		rule.Path = path

		rules = append(rules, rule)

		// Index by service and law
		if rule.Service != "" {
			if _, exists := lawsByService[rule.Service]; !exists {
				lawsByService[rule.Service] = make(map[string]struct{})
			}

			lawsByService[rule.Service][rule.Law] = struct{}{}

			// Index discoverable laws
			if rule.Discoverable != nil {
				if _, exists := lawsByServiceWithDiscoverable[*rule.Discoverable]; !exists {
					lawsByServiceWithDiscoverable[*rule.Discoverable] = make(map[string]map[string]struct{})
				}

				if _, exists := lawsByServiceWithDiscoverable[*rule.Discoverable][rule.Service]; !exists {
					lawsByServiceWithDiscoverable[*rule.Discoverable][rule.Service] = make(map[string]struct{})
				}

				lawsByServiceWithDiscoverable[*rule.Discoverable][rule.Service][rule.Law] = struct{}{}
			}
		}
	}

	return rules, lawsByService, lawsByServiceWithDiscoverable, nil
}

func (r *RuleResolve) GetRules() []RuleSpec {
	return r.rules
}

// GetServiceLaws returns a map of services to their laws
func (r *RuleResolve) GetServiceLaws() map[string][]string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]string, len(r.lawsByService))

	for service, laws := range r.lawsByService {
		lawsList := make([]string, 0, len(laws))
		for law := range laws {
			lawsList = append(lawsList, law)
		}
		result[service] = lawsList
	}

	return result
}

// GetDiscoverableServiceLaws returns a map of discoverable services to their laws
func (r *RuleResolve) GetDiscoverableServiceLaws(discoverableBy string) map[string][]string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]string, 0)

	if serviceMap, ok := r.discoverableLawsByService[discoverableBy]; ok {
		for service, laws := range serviceMap {
			lawsList := make([]string, 0, len(laws))
			for law := range laws {
				lawsList = append(lawsList, law)
			}
			result[service] = lawsList
		}
	}

	return result
}

// FindRule finds the applicable rule for a given law and reference date
func (r *RuleResolve) FindRule(law string, referenceDate time.Time, service string) (RuleSpec, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Filter rules for the given law
	var lawRules []RuleSpec
	for _, rule := range r.rules {
		if rule.Law == law {
			if service == "" || strings.EqualFold(strings.ToLower(rule.Service), strings.ToLower(service)) {
				lawRules = append(lawRules, rule)
			}
		}
	}

	if len(lawRules) == 0 {
		return RuleSpec{}, fmt.Errorf("no rules found for law: %s (and service: %s)", law, service)
	}

	// Find the most recent valid rule before the reference date
	var validRules []RuleSpec
	for _, rule := range lawRules {
		if !rule.ValidFrom.After(referenceDate) {
			validRules = append(validRules, rule)
		}
	}

	if len(validRules) == 0 {
		return RuleSpec{}, fmt.Errorf("no valid rules found for law %s at date %s", law, referenceDate.Format(time.RFC3339))
	}

	// Return the most recently valid rule
	result := validRules[0]
	for _, rule := range validRules[1:] {
		if rule.ValidFrom.After(result.ValidFrom) {
			result = rule
		}
	}

	return result, nil
}

// GetRuleSpec gets the rule specification as a map
func (r *RuleResolve) GetRuleSpec(law string, referenceDate time.Time, service string) (RuleSpec, error) {
	rule, err := r.FindRule(law, referenceDate, service)
	if err != nil {
		return RuleSpec{}, err
	}

	if data, ok := ruleSpecCache.Load(rule.Path); ok {
		return data.(RuleSpec), nil
	}

	// Read the rule spec
	data, err := os.ReadFile(rule.Path)
	if err != nil {
		return RuleSpec{}, fmt.Errorf("error reading rule file: %w", err)
	}

	// Parse to map
	var result RuleSpec
	if err := yaml.Unmarshal(data, &result); err != nil {
		return RuleSpec{}, fmt.Errorf("error parsing rule YAML: %w", err)
	}

	ruleSpecCache.Store(rule.Path, result)

	return result, nil
}

func deptr[T any](a *T, def T) T {
	if a == nil {
		return def
	}
	return *a
}

// RulesDataFrame returns a slice of maps representing all rules
func (r *RuleResolve) RulesDataFrame() []map[string]any {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]map[string]any, 0, len(r.rules))

	for _, rule := range r.rules {
		ruleData := map[string]any{
			"path":            rule.Path,
			"decision_type":   deptr(rule.DecisionType, ""),
			"legal_character": deptr(rule.LegalCharacter, ""),
			"law_type":        deptr(rule.LawType, ""),
			"uuid":            rule.UUID,
			"name":            rule.Name,
			"law":             rule.Law,
			"valid_from":      rule.ValidFrom,
			"service":         rule.Service,
			"discoverable":    deptr(rule.Discoverable, ""),
			// "prop_parameters":  render.Render(rule.Properties.Parameters),
			// "prop_sources":     render.Render(rule.Properties.Sources),
			// "prop_input":       render.Render(rule.Properties.Input),
			// "prop_output":      render.Render(rule.Properties.Output),
			// "prop_definitions": render.Render(rule.Properties.Definitions),
			// "prop_applies":     render.Render(rule.Properties.Applies),
		}

		result = append(result, ruleData)
	}

	return result
}
