package context

// import (
// 	"context"
// 	"sync"

// 	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
// )

// type Resolved struct {
// 	Value    any
// 	Required bool
// 	Details  map[string]any
// }

// type Resolver interface {
// 	Resolve(ctx context.Context, key string) (*Resolved, bool)
// 	ResolveType() string
// }

// var _ Resolver = &ClaimResolver{}

// type ClaimResolver struct {
// 	claims   map[string]model.Claim
// 	resolver Resolver
// }

// func NewClaimResolver(claims map[string]model.Claim) *ClaimResolver {
// 	return &ClaimResolver{
// 		claims:   claims,
// 		resolver: nil,
// 	}
// }

// // Resolve implements Resolver.
// func (c *ClaimResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
// 	claim, exists := c.claims[key]
// 	if !exists {
// 		return nil, false
// 	}

// 	resolved := new(Resolved)
// 	resolved.Value = claim

// 	// Add type information for claims
// 	if spec, exists := c.resolver.Resolve(ctx, key); exists {
// 		if spec, ok := spec.Value.(map[string]any); ok {
// 			if typeVal, exists := spec["type"]; exists {
// 				resolved.Details["type"] = typeVal
// 			}

// 			if typeSpec, exists := spec["type_spec"]; exists {
// 				resolved.Details["type_spec"] = typeSpec
// 			}

// 			resolved.Required = getBoolFromMap(spec, "required", false)
// 		}
// 	}

// 	return resolved, true
// }

// func (c *ClaimResolver) ResolveType() string {
// 	return "CLAIM"
// }

// var _ Resolver = &MapResolver{}

// type MapResolver struct {
// 	data         map[string]any
// 	resolverType string
// 	mu           sync.RWMutex
// }

// func newMapResolver(data map[string]any, rt string) *MapResolver {
// 	return &MapResolver{
// 		data:         data,
// 		resolverType: rt,
// 		mu:           sync.RWMutex{},
// 	}
// }

// // Resolve implements Resolver.
// func (l *MapResolver) Resolve(_ context.Context, key string) (*Resolved, bool) {
// 	v, ok := l.get(key)
// 	return &Resolved{Value: v}, ok
// }

// func (l *MapResolver) set(key string, data any) {
// 	l.mu.Lock()
// 	defer l.mu.Unlock()

// 	l.data[key] = data
// }

// func (l *MapResolver) get(key string) (any, bool) {
// 	l.mu.RLock()
// 	defer l.mu.RUnlock()

// 	value, ok := l.data[key]
// 	return value, ok
// }

// // ResolveType implements Resolver.
// func (l *MapResolver) ResolveType() string {
// 	return l.resolverType
// }

// var _ Resolver = &LocalResolver{}

// type LocalResolver struct {
// 	MapResolver
// }

// func NewLocalResolver() *LocalResolver {
// 	return &LocalResolver{
// 		MapResolver: *newMapResolver(make(map[string]any), "LOCAL"),
// 	}
// }

// func (lr *LocalResolver) Set(key string, data any) {
// 	lr.set(key, data)
// }

// var _ Resolver = &DefinitionsResolver{}

// type DefinitionsResolver struct {
// 	MapResolver
// }

// func NewDefinitionsResolver(data map[string]any) *DefinitionsResolver {
// 	return &DefinitionsResolver{
// 		MapResolver: *newMapResolver(data, "DEFINITION"),
// 	}
// }

// var _ Resolver = &ParametersResolver{}

// type ParametersResolver struct {
// 	MapResolver
// }

// func NewParametersResolver(data map[string]any) *ParametersResolver {
// 	return &ParametersResolver{
// 		MapResolver: *newMapResolver(data, "PARAMETER"),
// 	}
// }

// var _ Resolver = &OutputsResolver{}

// type OutputsResolver struct {
// 	MapResolver
// }

// func NewOutputsResolver() *OutputsResolver {
// 	return &OutputsResolver{
// 		MapResolver: *newMapResolver(make(map[string]any), "OUTPUT"),
// 	}
// }

// func (lr *OutputsResolver) Set(key string, data any) {
// 	lr.set(key, data)
// }

// var _ Resolver = &PropertySpecOverwriteResolver{}

// type PropertySpecOverwriteResolver struct {
// 	propertySpec   map[string]map[string]any
// 	overwriteInput map[string]map[string]any
// }

// func NewPropertySpecOverwriteResolver(propertySpec map[string]map[string]any, overwriteInput map[string]map[string]any) *PropertySpecOverwriteResolver {
// 	return &PropertySpecOverwriteResolver{
// 		propertySpec:   propertySpec,
// 		overwriteInput: overwriteInput,
// 	}
// }

// // Resolve implements Resolver.
// func (l *PropertySpecOverwriteResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
// 	spec, ok := l.propertySpec[key]
// 	if !ok {
// 		return nil, false
// 	}

// 	serviceRef, ok := spec["service_reference"].(map[string]any)
// 	if !ok {
// 		return nil, false
// 	}

// 	serviceName, hasService := serviceRef["service"].(string)
// 	fieldName, hasField := serviceRef["field"].(string)

// 	if !hasService || !hasField || l.overwriteInput == nil {
// 		return nil, false
// 	}

// 	serviceOverwrites, ok := l.overwriteInput[serviceName]
// 	if !ok {
// 		return nil, false
// 	}

// 	value, ok := serviceOverwrites[fieldName]
// 	if !ok {
// 		return nil, false
// 	}

// 	return &Resolved{Value: value}, true
// }

// // ResolveType implements Resolver.
// func (l *PropertySpecOverwriteResolver) ResolveType() string {
// 	return "OVERWRITE"
// }

// var _ Resolver = &PropertySpecSourceResolver{}

// type PropertySpecSourceResolver struct {
// 	propertySpec map[string]map[string]any
// }

// func NewPropertySpecSourceResolver(propertySpec map[string]map[string]any) *PropertySpecSourceResolver {
// 	return &PropertySpecSourceResolver{
// 		propertySpec: propertySpec,
// 	}
// }

// // Resolve implements Resolver.
// func (l *PropertySpecSourceResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
// 	spec, ok := l.propertySpec[key]
// 	if !ok {
// 		return nil, false
// 	}

// 	// Check sources
// 	sourceRef, ok := spec["source_reference"].(map[string]any)
// 	if !ok {
// 		return nil, false
// 	}

// 	value, err := rc.resolveFromSource(ctx, sourceRef, spec)
// 	if err != nil {
// 		// logger.Debugf(ctx, "resolving from source: %s", err)
// 		return nil, false
// 	}

// 	if value == nil {
// 		return nil, false
// 	}

// 	resolved := &Resolved{
// 		Value:    value,
// 		Required: getBoolFromMap(spec, "required", false),
// 	}

// 	// Add type information to the node
// 	if typeVal, exists := spec["type"]; exists {
// 		resolved.Details["type"] = typeVal
// 	}
// 	if typeSpec, exists := spec["type_spec"]; exists {
// 		resolved.Details["type_spec"] = typeSpec
// 	}

// 	// logger.Debugf(ctx, "Resolving from SOURCE %v: %v", sourceRef["table"], value)

// 	return resolved, true

// }

// // ResolveType implements Resolver.
// func (l *PropertySpecSourceResolver) ResolveType() string {
// 	return "SOURCE"
// }

// var _ Resolver = &PropertySpecServiceResolver{}

// type PropertySpecServiceResolver struct {
// 	propertySpec map[string]map[string]any
// }

// func NewPropertySpecServiceResolver(propertySpec map[string]map[string]any) *PropertySpecServiceResolver {
// 	return &PropertySpecServiceResolver{
// 		propertySpec: propertySpec,
// 	}
// }

// // Resolve implements Resolver.
// func (l *PropertySpecServiceResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
// 	spec, ok := l.propertySpec[key]
// 	if !ok {
// 		return nil, false
// 	}

// 	serviceRef, ok := spec["service_reference"].(map[string]any)
// 	if !ok {
// 		return nil, false
// 	}

// 	value, err := rc.resolveFromService(ctx, key, serviceRef, spec)
// 	if err != nil {
// 		return nil, false
// 	}

// 	rc.logger.Debugf(ctx, "Result for $%s from %s field %s: %v", key, serviceRef["service"], serviceRef["field"], value)

// 	resolved := &Resolved{
// 		Value:    value,
// 		Required: getBoolFromMap(spec, "required", false),
// 	}

// 	// Add type information to the node
// 	if typeVal, exists := spec["type"]; exists {
// 		resolved.Details["type"] = typeVal
// 	}
// 	if typeSpec, exists := spec["type_spec"]; exists {
// 		resolved.Details["type_spec"] = typeSpec
// 	}

// 	return resolved, true

// }

// // ResolveType implements Resolver.
// func (l *PropertySpecServiceResolver) ResolveType() string {
// 	return "SERVICE"
// }
