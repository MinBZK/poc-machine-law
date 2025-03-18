package utils

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"gopkg.in/yaml.v3"
)

const (
	// BaseDir is the base directory for rule specs
	BaseDir = "law"
)

// RuleSpec defines a rule specification
type RuleSpec struct {
	Path           string         `json:"path"`
	DecisionType   string         `json:"decision_type"`
	LawType        string         `json:"law_type"`
	LegalCharacter string         `json:"legal_character"`
	UUID           string         `json:"uuid"`
	Name           string         `json:"name"`
	Law            string         `json:"law"`
	ValidFrom      time.Time      `json:"valid_from"`
	Service        string         `json:"service"`
	Discoverable   string         `json:"discoverable"`
	Properties     map[string]any `json:"properties"`
}

// FromYAML creates a RuleSpec from YAML file contents
func (r *RuleSpec) FromYAML(data []byte, path string) error {
	var rawData map[string]any
	if err := yaml.Unmarshal(data, &rawData); err != nil {
		return err
	}

	r.Path = path
	r.DecisionType = getString(rawData, "decision_type")
	r.LawType = getString(rawData, "law_type")
	r.LegalCharacter = getString(rawData, "legal_character")
	r.UUID = getString(rawData, "uuid")
	r.Name = getString(rawData, "name")
	r.Law = getString(rawData, "law")
	r.Discoverable = getString(rawData, "discoverable")
	r.Service = getString(rawData, "service")

	// Handle valid_from date
	if validFrom, ok := rawData["valid_from"]; ok {
		if t, ok := validFrom.(time.Time); ok {
			r.ValidFrom = t
		} else if dateStr, ok := validFrom.(string); ok {
			// Try to parse as ISO date
			t, err := time.Parse("2006-01-02", dateStr)
			if err == nil {
				r.ValidFrom = t
			}

		}
	}

	// Get properties
	if props, ok := rawData["properties"].(map[string]any); ok {
		r.Properties = props
	} else {
		r.Properties = make(map[string]any)
	}

	return nil
}

// Helper function to safely get string value from map
func getString(data map[string]any, key string) string {
	if val, ok := data[key]; ok {
		if strVal, ok := val.(string); ok {
			return strVal
		}
	}
	return ""
}

// RuleResolver handles rule resolution and lookup
type RuleResolver struct {
	RulesDir                  string
	Rules                     []*RuleSpec
	LawsByService             map[string]map[string]struct{}
	DiscoverableLawsByService map[string]map[string]map[string]struct{}
	mu                        sync.RWMutex
}

// NewRuleResolver creates a new rule resolver
func NewRuleResolver() *RuleResolver {
	resolver := &RuleResolver{
		RulesDir:                  BaseDir,
		Rules:                     make([]*RuleSpec, 0),
		LawsByService:             make(map[string]map[string]struct{}),
		DiscoverableLawsByService: make(map[string]map[string]map[string]struct{}),
	}

	err := resolver.LoadRules()
	if err != nil {
		fmt.Printf("Error loading rules: %v\n", err)
	}

	return resolver
}

// LoadRules loads all rule specifications from the rules directory
func (r *RuleResolver) LoadRules() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Clear existing data
	r.Rules = make([]*RuleSpec, 0)
	r.LawsByService = make(map[string]map[string]struct{})
	r.DiscoverableLawsByService = make(map[string]map[string]map[string]struct{})

	// Find all .yaml and .yml files recursively
	var yamlFiles []string

	err := func() error {
		// First, evaluate the symlink to get the actual path
		realPath, err := filepath.EvalSymlinks(r.RulesDir)
		if err != nil {
			return fmt.Errorf("failed to evaluate symlink %s: %w", r.RulesDir, err)
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
		return err
	}

	// Load each rule file
	for _, path := range yamlFiles {
		data, err := os.ReadFile(path)
		if err != nil {
			fmt.Printf("Error reading file %s: %v\n", path, err)
			continue
		}

		rule := &RuleSpec{}
		err = rule.FromYAML(data, path)
		if err != nil {
			fmt.Printf("Error parsing YAML from %s: %v\n", path, err)
			continue
		}

		r.Rules = append(r.Rules, rule)

		// Index by service and law
		if rule.Service != "" {
			if _, exists := r.LawsByService[rule.Service]; !exists {
				r.LawsByService[rule.Service] = make(map[string]struct{})
			}
			r.LawsByService[rule.Service][rule.Law] = struct{}{}

			// Index discoverable laws
			if rule.Discoverable != "" {
				if _, exists := r.DiscoverableLawsByService[rule.Discoverable]; !exists {
					r.DiscoverableLawsByService[rule.Discoverable] = make(map[string]map[string]struct{})
				}

				if _, exists := r.DiscoverableLawsByService[rule.Discoverable][rule.Service]; !exists {
					r.DiscoverableLawsByService[rule.Discoverable][rule.Service] = make(map[string]struct{})
				}

				r.DiscoverableLawsByService[rule.Discoverable][rule.Service][rule.Law] = struct{}{}
			}
		}
	}

	return nil
}

// GetServiceLaws returns a map of services to their laws
func (r *RuleResolver) GetServiceLaws() map[string][]string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]string)

	for service, laws := range r.LawsByService {
		lawsList := make([]string, 0, len(laws))
		for law := range laws {
			lawsList = append(lawsList, law)
		}
		result[service] = lawsList
	}

	return result
}

// GetDiscoverableServiceLaws returns a map of discoverable services to their laws
func (r *RuleResolver) GetDiscoverableServiceLaws(discoverableBy string) map[string][]string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]string)

	if serviceMap, ok := r.DiscoverableLawsByService[discoverableBy]; ok {
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
func (r *RuleResolver) FindRule(law, referenceDate string, service string) (*RuleSpec, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	refDate, err := time.Parse("2006-01-02", referenceDate)
	if err != nil {
		return nil, fmt.Errorf("invalid reference date: %s", referenceDate)
	}

	// Filter rules for the given law
	var lawRules []*RuleSpec
	for _, rule := range r.Rules {
		if rule.Law == law {
			if service == "" || rule.Service == service {
				lawRules = append(lawRules, rule)
			}
		}
	}

	if len(lawRules) == 0 {
		return nil, fmt.Errorf("no rules found for law: %s (and service: %s)", law, service)
	}

	// Find the most recent valid rule before the reference date
	var validRules []*RuleSpec
	for _, rule := range lawRules {
		if !rule.ValidFrom.After(refDate) {
			validRules = append(validRules, rule)
		}
	}

	if len(validRules) == 0 {
		return nil, fmt.Errorf("no valid rules found for law %s at date %s", law, referenceDate)
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
func (r *RuleResolver) GetRuleSpec(law, referenceDate string, service string) (map[string]any, error) {
	rule, err := r.FindRule(law, referenceDate, service)
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(rule.Path)
	if err != nil {
		return nil, fmt.Errorf("error reading rule file: %v", err)
	}

	var result map[string]any
	err = yaml.Unmarshal(data, &result)
	if err != nil {
		return nil, fmt.Errorf("error parsing rule YAML: %v", err)
	}

	return result, nil
}

// RulesDataFrame returns a slice of maps representing all rules
func (r *RuleResolver) RulesDataFrame() []map[string]any {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]map[string]any, 0, len(r.Rules))

	for _, rule := range r.Rules {
		ruleData := map[string]any{
			"path":            rule.Path,
			"decision_type":   rule.DecisionType,
			"legal_character": rule.LegalCharacter,
			"law_type":        rule.LawType,
			"uuid":            rule.UUID,
			"name":            rule.Name,
			"law":             rule.Law,
			"valid_from":      rule.ValidFrom,
			"service":         rule.Service,
			"discoverable":    rule.Discoverable,
		}

		// Add properties with prop_ prefix
		for k, v := range rule.Properties {
			ruleData["prop_"+k] = v
		}

		result = append(result, ruleData)
	}

	return result
}
