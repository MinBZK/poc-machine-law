package ruleresolver

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	// "github.com/goccy/go-yaml"
	"github.com/looplab/eventhorizon/uuid"
	"gopkg.in/yaml.v3"
)

const (
	LawBaseDir = "laws"
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
		// Try to find the laws directory by walking up from current directory
		// This handles cases where tests run from nested directories
		lawDir := ""
		currentDir, _ := os.Getwd()

		// Try up to 5 levels up to find laws directory
		for i := 0; i < 5; i++ {
			checkPath := LawBaseDir
			if i > 0 {
				checkPath = filepath.Join(strings.Repeat("../", i), LawBaseDir)
			}

			if _, statErr := os.Stat(checkPath); statErr == nil {
				lawDir = checkPath
				break
			}
		}

		if lawDir == "" {
			err = fmt.Errorf("laws directory not found (searched up to 5 levels from %s)", currentDir)
			return
		}

		ruleSpec, lawsByService, discoverableLawsByService, err = rulesLoad(lawDir)
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

// isV050Format detects whether raw YAML data is in v0.5.0 article-based format
func isV050Format(data map[string]interface{}) bool {
	_, hasArticles := data["articles"]
	_, hasSchema := data["$schema"]
	return hasArticles || hasSchema
}

// unwrapDefinitionValue extracts the raw value from a v0.5.0 definition.
// Definitions in v0.5.0 can be wrapped as {value: X}; this unwraps them.
func unwrapDefinitionValue(v interface{}) interface{} {
	if m, ok := v.(map[string]interface{}); ok {
		if val, hasValue := m["value"]; hasValue {
			return val
		}
	}
	return v
}

// convertV050SourceToServiceReference converts a v0.5.0 source block to a ServiceReference
func convertV050SourceToServiceReference(src *V050Source) ServiceReference {
	if src == nil {
		return ServiceReference{}
	}
	sr := ServiceReference{
		Service: src.Service,
		Field:   src.Output,
		Law:     src.Regulation,
	}
	if len(src.Parameters) > 0 {
		params := make([]Parameter, 0, len(src.Parameters))
		for name, ref := range src.Parameters {
			params = append(params, Parameter{
				Name:      name,
				Reference: ref,
			})
		}
		sr.Parameters = params
	}
	return sr
}

// convertV050InputToFlat converts v0.5.0 input fields to the flat RuleSpec format.
// Input fields with a source block become InputField entries with ServiceReference populated.
// Input fields with a source_reference block become SourceField entries.
func convertV050InputToFlat(inputs []InputField) ([]InputField, []SourceField) {
	var flatInputs []InputField
	var flatSources []SourceField

	for _, inp := range inputs {
		if inp.Source != nil {
			// Convert v0.5.0 source to ServiceReference
			flatInp := InputField{
				BaseField:       inp.BaseField,
				ServiceReference: convertV050SourceToServiceReference(inp.Source),
			}
			flatInputs = append(flatInputs, flatInp)
		} else if inp.SourceReference != nil {
			// Convert to SourceField
			flatSrc := SourceField{
				BaseField:       inp.BaseField,
				SourceReference: inp.SourceReference,
			}
			flatSources = append(flatSources, flatSrc)
		} else if inp.ServiceReference.Service != "" || inp.ServiceReference.Law != "" {
			// Already has a v0.4.x style ServiceReference
			flatInputs = append(flatInputs, inp)
		} else {
			// No source info; keep as input
			flatInputs = append(flatInputs, inp)
		}
	}

	return flatInputs, flatSources
}

// flattenV050 converts an ArticleBasedSpec to a flat RuleSpec by merging all articles
func flattenV050(spec ArticleBasedSpec) (RuleSpec, error) {
	validFrom, err := time.Parse("2006-01-02", spec.ValidFrom)
	if err != nil {
		return RuleSpec{}, fmt.Errorf("invalid valid_from date %q: %w", spec.ValidFrom, err)
	}

	uuidVal, err := parseUUID(spec.UUID)
	if err != nil {
		return RuleSpec{}, fmt.Errorf("invalid uuid %q: %w", spec.UUID, err)
	}

	rule := RuleSpec{
		UUID:      uuidVal,
		Name:      spec.Name,
		Law:       spec.ID,
		LawType:   strPtr(spec.RegulatoryLayer),
		ValidFrom: validFrom,
		Service:   spec.Service,
	}

	if spec.Discoverable != "" {
		rule.Discoverable = &spec.Discoverable
	}

	// Merge definitions, parameters, inputs, outputs, actions, requirements from all articles
	allDefinitions := make(map[string]any)
	var allParameters []ParameterField
	var allInputs []InputField
	var allOutputs []OutputField
	var allActions []Action
	var allRequirements []Requirement

	paramsSeen := make(map[string]bool)
	inputsSeen := make(map[string]bool)
	outputsSeen := make(map[string]bool)

	for _, article := range spec.Articles {
		if article.MachineReadable == nil {
			continue
		}

		mr := article.MachineReadable

		// Merge definitions (unwrap {value: X} format)
		for k, v := range mr.Definitions {
			allDefinitions[k] = unwrapDefinitionValue(v)
		}

		if mr.Execution == nil {
			continue
		}

		exec := mr.Execution

		// Extract legal_character and decision_type from first article that has them
		if exec.Produces != nil {
			if rule.LegalCharacter == nil && exec.Produces.LegalCharacter != "" {
				rule.LegalCharacter = strPtr(exec.Produces.LegalCharacter)
			}
			if rule.DecisionType == nil && exec.Produces.DecisionType != "" {
				rule.DecisionType = strPtr(exec.Produces.DecisionType)
			}
		}

		// Merge parameters (deduplicate by name)
		for _, p := range exec.Parameters {
			if !paramsSeen[p.Name] {
				paramsSeen[p.Name] = true
				allParameters = append(allParameters, p)
			}
		}

		// Merge inputs (deduplicate by name)
		for _, inp := range exec.Input {
			if !inputsSeen[inp.Name] {
				inputsSeen[inp.Name] = true
				allInputs = append(allInputs, inp)
			}
		}

		// Merge outputs (deduplicate by name)
		for _, out := range exec.Output {
			if !outputsSeen[out.Name] {
				outputsSeen[out.Name] = true
				allOutputs = append(allOutputs, out)
			}
		}

		// Merge actions
		allActions = append(allActions, exec.Actions...)

		// Merge requirements (convert from []interface{} to []Requirement)
		for _, reqRaw := range exec.Requirements {
			req, convertErr := convertRequirement(reqRaw)
			if convertErr != nil {
				fmt.Printf("Warning: could not convert requirement: %v\n", convertErr)
				continue
			}
			allRequirements = append(allRequirements, req)
		}
	}

	// Convert v0.5.0 input fields to flat format (split into inputs and sources)
	flatInputs, flatSources := convertV050InputToFlat(allInputs)

	rule.Properties = Properties{
		Parameters:  allParameters,
		Input:       flatInputs,
		Sources:     flatSources,
		Output:      allOutputs,
		Definitions: allDefinitions,
	}
	rule.Actions = allActions
	rule.Requirements = allRequirements

	return rule, nil
}

// convertRequirement converts a raw interface{} (from v0.5.0 requirements) to a Requirement.
// It re-marshals to YAML and then unmarshals into the typed Requirement struct.
func convertRequirement(raw interface{}) (Requirement, error) {
	data, err := yaml.Marshal(raw)
	if err != nil {
		return Requirement{}, fmt.Errorf("marshal requirement: %w", err)
	}
	var req Requirement
	if err := yaml.Unmarshal(data, &req); err != nil {
		return Requirement{}, fmt.Errorf("unmarshal requirement: %w", err)
	}
	return req, nil
}

// parseUUID parses a UUID string. It uses the looplab UUID package.
func parseUUID(s string) (uuid.UUID, error) {
	return uuid.Parse(s)
}

// strPtr returns a pointer to the given string, or nil if empty
func strPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// parseRuleFromData parses raw YAML data into a RuleSpec, detecting v0.5.0 format automatically
func parseRuleFromData(data []byte) (RuleSpec, error) {
	// First, check if this is v0.5.0 format
	var raw map[string]interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return RuleSpec{}, fmt.Errorf("error parsing raw YAML: %w", err)
	}

	if isV050Format(raw) {
		var articleSpec ArticleBasedSpec
		if err := yaml.Unmarshal(data, &articleSpec); err != nil {
			return RuleSpec{}, fmt.Errorf("error parsing v0.5.0 YAML: %w", err)
		}
		return flattenV050(articleSpec)
	}

	// Fall back to v0.4.x format
	var rule RuleSpec
	if err := yaml.Unmarshal(data, &rule); err != nil {
		return RuleSpec{}, fmt.Errorf("error parsing v0.4.x YAML: %w", err)
	}
	return rule, nil
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

		rule, err := parseRuleFromData(data)
		if err != nil {
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

	// Parse using format-aware parser (supports both v0.4.x and v0.5.0)
	result, err := parseRuleFromData(data)
	if err != nil {
		return RuleSpec{}, fmt.Errorf("error parsing rule YAML: %w", err)
	}

	result.Path = rule.Path
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
