package ruleresolver

import (
	"fmt"
	"sync"
	"time"
)

// SourceType represents the source of rule data.
type SourceType string

const (
	SourceTypeDisk SourceType = "disk"
	SourceTypeURL  SourceType = "url"
)

var (
	ruleResolver *RuleResolver
	mu           sync.Mutex
)

// RuleResolver handles rule resolution and lookup.
type RuleResolver struct {
	Rules                     []RuleSpec
	LawsByService             map[string][]string
	DiscoverableLawsByService map[string]map[string][]string
}

type RuleResolverConfig struct {
	Provider RuleSpecProvider
	URL      *string
	DIR      *string
}

func New(cfg RuleResolverConfig) (*RuleResolver, error) {
	mu.Lock()
	defer mu.Unlock()

	if ruleResolver == nil {
		provider, err := ProviderFactory(cfg)
		if err != nil {
			return nil, fmt.Errorf("provider factory: %w", err)
		}

		rules, err := provider.Fetch()
		if err != nil {
			return nil, fmt.Errorf("failed to fetch YAML files: %w", err)
		}

		lawsByService, discoverableLawsByService := index(rules)

		ruleResolver = &RuleResolver{
			Rules:                     rules,
			LawsByService:             lawsByService,
			DiscoverableLawsByService: discoverableLawsByService,
		}
	}

	return ruleResolver, nil
}

func index(rules []RuleSpec) (map[string][]string, map[string]map[string][]string) {
	// clear current values
	lawsByService := make(map[string][]string)
	discoverableLawsByService := make(map[string]map[string][]string)

	for _, rule := range rules {
		// Index by service and law
		if rule.Service == "" {
			continue
		}

		if _, exists := lawsByService[rule.Service]; !exists {
			lawsByService[rule.Service] = make([]string, 0, 1)
		}

		lawsByService[rule.Service] = append(lawsByService[rule.Service], rule.Law)

		// Index discoverable laws
		if rule.Discoverable == nil {
			continue
		}

		if _, exists := discoverableLawsByService[*rule.Discoverable]; !exists {
			discoverableLawsByService[*rule.Discoverable] = make(map[string][]string)
		}

		if _, exists := discoverableLawsByService[*rule.Discoverable][rule.Service]; !exists {
			discoverableLawsByService[*rule.Discoverable][rule.Service] = make([]string, 1)
		}

		discoverableLawsByService[*rule.Discoverable][rule.Service] = append(discoverableLawsByService[*rule.Discoverable][rule.Service], rule.Law)
	}

	return lawsByService, discoverableLawsByService
}

// GetServiceLaws returns a map of services to their laws.
func (r *RuleResolver) GetServiceLaws() map[string][]string {
	return r.LawsByService
}

// GetDiscoverableServiceLaws returns a map of discoverable services to their laws.
func (r *RuleResolver) GetDiscoverableServiceLaws(discoverableBy string) map[string][]string {
	if serviceMap, ok := r.DiscoverableLawsByService[discoverableBy]; ok {
		return serviceMap
	}

	return nil
}

// findRule finds the applicable rule for a given law and reference date.
func (r *RuleResolver) findRule(law, referenceDate string, service string) (RuleSpec, error) {
	refDate, err := time.Parse("2006-01-02", referenceDate)
	if err != nil {
		return RuleSpec{}, fmt.Errorf("invalid reference date: %s", referenceDate)
	}

	// Filter rules for the given law
	var lawRules []RuleSpec
	for _, rule := range r.Rules {
		if rule.Law == law {
			if service == "" || rule.Service == service {
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
		if !rule.ValidFrom.After(refDate) {
			validRules = append(validRules, rule)
		}
	}

	if len(validRules) == 0 {
		return RuleSpec{}, fmt.Errorf("no valid rules found for law %s at date %s", law, referenceDate)
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

// GetRuleSpec gets the rule specification as a map.
func (r *RuleResolver) GetRuleSpec(law, referenceDate string, service string) (RuleSpec, error) {
	rule, err := r.findRule(law, referenceDate, service)
	if err != nil {
		return RuleSpec{}, err
	}

	return rule, nil
}

func deptr[T any](a *T, def T) T {
	if a == nil {
		return def
	}
	return *a
}

func ptr[T any](a T) *T {
	return &a
}

// RulesDataFrame returns a slice of maps representing all rules.
func (r *RuleResolver) RulesDataFrame() []map[string]any {
	result := make([]map[string]any, 0, len(r.Rules))

	for _, rule := range r.Rules {
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
