package context

import (
	"context"
	"fmt"
	"maps"
	"strings"
	"sync"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/path"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

type Resolved struct {
	Value    any
	Required bool
	Details  map[string]any
}

type Resolver interface {
	Resolve(ctx context.Context, key string) (*Resolved, bool)
	ResolveType() string
}

var _ Resolver = &ClaimResolver{}

type ClaimResolver struct {
	claims       map[string]model.Claim
	propertySpec map[string]ruleresolver.Field
}

func NewClaimResolver(claims map[string]model.Claim, propertySpec map[string]ruleresolver.Field) *ClaimResolver {
	return &ClaimResolver{
		claims:       claims,
		propertySpec: propertySpec,
	}
}

// Resolve implements Resolver.
func (c *ClaimResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
	claim, exists := c.claims[key]
	if !exists {
		return nil, false
	}

	resolved := &Resolved{
		Value:   claim.NewValue,
		Details: make(map[string]any),
	}

	// Add type information for claims
	if spec, ok := c.propertySpec[key]; ok {
		if spec.GetBase().Type != "" {
			resolved.Details["type"] = spec.GetBase().Type
		}

		if spec.GetBase().TypeSpec != nil {
			resolved.Details["type_spec"] = map[string]any{
				"type":      spec.GetBase().TypeSpec.Type,
				"unit":      spec.GetBase().TypeSpec.Unit,
				"precision": spec.GetBase().TypeSpec.Precision,
				"min":       spec.GetBase().TypeSpec.Min,
				"max":       spec.GetBase().TypeSpec.Max,
			}
		}

		required := false
		if spec.GetBase().Required != nil {
			required = *spec.GetBase().Required
		}
		resolved.Required = required
	}

	return resolved, true
}

func (c *ClaimResolver) ResolveType() string {
	return "CLAIM"
}

var _ Resolver = &MapResolver{}

type MapResolver struct {
	data         map[string]any
	resolverType string
	mu           sync.RWMutex
}

func newMapResolver(data map[string]any, rt string) *MapResolver {
	return &MapResolver{
		data:         data,
		resolverType: rt,
		mu:           sync.RWMutex{},
	}
}

// Resolve implements Resolver.
func (l *MapResolver) Resolve(_ context.Context, key string) (*Resolved, bool) {
	v, ok := l.get(key)
	return &Resolved{Value: v}, ok
}

func (l *MapResolver) set(key string, data any) {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.data[key] = data
}

func (l *MapResolver) get(key string) (any, bool) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	value, ok := l.data[key]
	return value, ok
}

// ResolveType implements Resolver.
func (l *MapResolver) ResolveType() string {
	return l.resolverType
}

var _ Resolver = &LocalResolver{}

type LocalResolver struct {
	MapResolver
}

func NewLocalResolver() *LocalResolver {
	return &LocalResolver{
		MapResolver: *newMapResolver(make(map[string]any), "LOCAL"),
	}
}

func (lr *LocalResolver) Set(key string, data any) {
	lr.set(key, data)
}

var _ Resolver = &DefinitionsResolver{}

type DefinitionsResolver struct {
	MapResolver
}

func NewDefinitionsResolver(data map[string]any) *DefinitionsResolver {
	return &DefinitionsResolver{
		MapResolver: *newMapResolver(data, "DEFINITION"),
	}
}

// Resolve implements Resolver with special handling for legal_basis metadata.
func (d *DefinitionsResolver) Resolve(_ context.Context, key string) (*Resolved, bool) {
	v, ok := d.get(key)
	if !ok {
		return nil, false
	}

	// Check if the definition contains both 'value' and 'legal_basis' fields
	if defMap, isMap := v.(map[string]any); isMap {
		if value, hasValue := defMap["value"]; hasValue {
			if _, hasLegalBasis := defMap["legal_basis"]; hasLegalBasis {
				// Extract only the value, ignoring legal_basis metadata
				return &Resolved{Value: value}, true
			}
		}
	}

	// Return the value as-is for normal definitions
	return &Resolved{Value: v}, ok
}

var _ Resolver = &ParametersResolver{}

type ParametersResolver struct {
	MapResolver
}

func NewParametersResolver(data map[string]any) *ParametersResolver {
	return &ParametersResolver{
		MapResolver: *newMapResolver(data, "PARAMETER"),
	}
}

var _ Resolver = &OutputsResolver{}

type OutputsResolver struct {
	MapResolver
}

func NewOutputsResolver() *OutputsResolver {
	return &OutputsResolver{
		MapResolver: *newMapResolver(make(map[string]any), "OUTPUT"),
	}
}

// Resolve implements Resolver.
func (l *OutputsResolver) Resolve(_ context.Context, key string) (*Resolved, bool) {
	v, ok := l.get(key)
	return &Resolved{Value: v}, ok
}

func (lr *OutputsResolver) Set(key string, data any) {
	lr.set(key, data)
}

var _ Resolver = &PropertySpecOverwriteResolver{}

type PropertySpecOverwriteResolver struct {
	propertySpec   map[string]ruleresolver.Field
	overwriteInput map[string]map[string]any
}

func NewPropertySpecOverwriteResolver(propertySpec map[string]ruleresolver.Field, overwriteInput map[string]map[string]any) *PropertySpecOverwriteResolver {
	return &PropertySpecOverwriteResolver{
		propertySpec:   propertySpec,
		overwriteInput: overwriteInput,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecOverwriteResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
	spec, ok := l.propertySpec[key]
	if !ok {
		return nil, false
	}

	var serviceRef *ruleresolver.ServiceReference
	if spec.Input != nil {
		serviceRef = &spec.Input.ServiceReference
	} else if spec.Source != nil {
		serviceRef = spec.Source.ServiceReference
	}

	if serviceRef == nil {
		return nil, false
	}

	if serviceRef.Service == "" || serviceRef.Field == "" || l.overwriteInput == nil {
		return nil, false
	}

	serviceOverwrites, ok := l.overwriteInput[serviceRef.Service]
	if !ok {
		return nil, false
	}

	value, ok := serviceOverwrites[serviceRef.Field]
	if !ok {
		return nil, false
	}

	return &Resolved{Value: value}, true
}

// ResolveType implements Resolver.
func (l *PropertySpecOverwriteResolver) ResolveType() string {
	return "OVERWRITE"
}

var _ Resolver = &PropertySpecServiceResolver{}

type PropertySpecServiceResolver struct {
	propertySpec map[string]ruleresolver.Field
	rc           *RuleContext
}

func NewPropertySpecServiceResolver(rc *RuleContext, propertySpec map[string]ruleresolver.Field) *PropertySpecServiceResolver {
	return &PropertySpecServiceResolver{
		propertySpec: propertySpec,
		rc:           rc,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecServiceResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
	spec, ok := l.propertySpec[key]
	if !ok {
		return nil, false
	}

	var serviceRef *ruleresolver.ServiceReference
	if spec.Input != nil {
		serviceRef = &spec.Input.ServiceReference
	} else if spec.Source != nil {
		serviceRef = spec.Source.ServiceReference
	}

	if serviceRef == nil {
		return nil, false
	}

	value, err := resolveFromService(ctx, l.rc, key, *serviceRef, spec)
	if err != nil {
		return nil, false
	}

	logging.FromContext(ctx).
		Debugf(ctx, "Result for $%s from %s field %s: %v", key, serviceRef.Service, serviceRef.Field, value)

	required := false
	if spec.GetBase().Required != nil {
		required = *spec.GetBase().Required
	}

	resolved := &Resolved{
		Value:    value,
		Required: required,
		Details:  make(map[string]any),
	}

	// Add type information to the node
	if spec.GetBase().Type != "" {
		resolved.Details["type"] = spec.GetBase().Type
	}

	if spec.GetBase().TypeSpec != nil {
		resolved.Details["type_spec"] = spec.GetBase().TypeSpec.ToMap()
	}

	return resolved, true

}

// resolveFromService resolves a value from a service
func resolveFromService(
	ctx context.Context,
	rc *RuleContext,
	ppath string,
	serviceRef ruleresolver.ServiceReference,
	spec ruleresolver.Field,
) (any, error) {

	// Clone parameters
	parameters := make(map[string]any)
	maps.Copy(parameters, rc.Parameters)

	// Add service reference parameters
	for _, param := range serviceRef.Parameters {
		value, err := rc.ResolveValue(ctx, param.Reference)
		if err != nil {
			return nil, err
		}
		parameters[param.Name] = value
	}

	// Get reference date
	referenceDate := rc.CalculationDate
	if spec.GetBase().Temporal != nil {
		if reference, ok := spec.GetBase().Temporal.Reference.(string); ok {
			refDate, err := rc.ResolveValue(ctx, reference)
			if err != nil {
				return nil, err
			}

			if refDateStr, ok := refDate.(string); ok {
				referenceDate = refDateStr
			}
		}
	}

	cacheKeyStr := getCacheKey(ppath, referenceDate, parameters)
	if cachedVal, exists := rc.ValuesCache.Load(cacheKeyStr); exists {
		rc.logger.WithIndent().Debugf(ctx, "Resolving from CACHE with key '%s': %v", cacheKeyStr, cachedVal)
		return cachedVal, nil
	}

	// Create service evaluation node
	details := map[string]any{
		"service":        serviceRef.Service,
		"law":            serviceRef.Law,
		"field":          serviceRef.Field,
		"reference_date": referenceDate,
		"parameters":     parameters,
		"path":           ppath,
	}

	// Copy type information from spec to details
	if spec.GetBase().Type != "" {
		details["type"] = spec.GetBase().Type
	}

	if spec.GetBase().TypeSpec != nil {
		details["type_spec"] = spec.GetBase().TypeSpec.ToMap()
	}

	serviceNode := &model.PathNode{
		Type:    "service_evaluation",
		Name:    fmt.Sprintf("Service call: %s.%s", serviceRef.Service, serviceRef.Law),
		Result:  nil,
		Details: details,
	}

	ctx = path.WithPathNode(ctx, serviceNode)
	defer path.FromContext(ctx).Pop()

	result, err := rc.ServiceProvider.Evaluate(
		ctx,
		serviceRef.Service,
		serviceRef.Law,
		parameters,
		referenceDate,
		rc.OverwriteInput,
		serviceRef.Field,
		rc.Approved,
	)
	if err != nil {
		return nil, err
	}

	value := result.Output[serviceRef.Field]
	rc.ValuesCache.Store(cacheKeyStr, value)

	// Update the service node with the result and add child path
	serviceNode.Result = value
	if result.Path != nil {
		serviceNode.AddChild(result.Path)
	}

	rc.MissingRequired = rc.MissingRequired || result.MissingRequired

	return value, nil
}

// ResolveType implements Resolver.
func (l *PropertySpecServiceResolver) ResolveType() string {
	return "SERVICE"
}

func getCacheKey(path string, referenceDate string, parameters map[string]any) string {
	// Check cache
	var cacheKey strings.Builder
	cacheKey.WriteString(path)
	cacheKey.WriteString("(")

	// Sort keys for consistency
	paramKeys := make([]string, 0, len(parameters))
	for k := range parameters {
		paramKeys = append(paramKeys, k)
	}

	// Stable sorting would be better but this works for simple keys
	for i, k := range paramKeys {
		if i > 0 {
			cacheKey.WriteString(",")
		}
		cacheKey.WriteString(fmt.Sprintf("%s:%v", k, parameters[k]))
	}
	cacheKey.WriteString(",")
	cacheKey.WriteString(referenceDate)
	cacheKey.WriteString(")")

	return cacheKey.String()
}
