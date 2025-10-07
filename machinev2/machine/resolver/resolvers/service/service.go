package service

import (
	"context"
	"fmt"
	"maps"
	"strings"
	"sync"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/path"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

var _ resolver.Resolver = &PropertySpecServiceResolver{}

type CachedValue struct {
	value           any
	missingRequired bool
}

type PropertySpecServiceResolver struct {
	propertySpec    map[string]ruleresolver.Field
	rc              resolver.RuleContexter
	sp              service.ServiceProvider
	parameters      map[string]any
	overwriteInput  map[string]map[string]any
	cache           sync.Map
	calculationDate string
	approved        bool
}

func New(
	rc resolver.RuleContexter,
	sp service.ServiceProvider,
	propertySpec map[string]ruleresolver.Field,
	parameters map[string]any,
	overwriteInput map[string]map[string]any,
	calculationDate string,
	approved bool,
) *PropertySpecServiceResolver {
	return &PropertySpecServiceResolver{
		rc:              rc,
		sp:              sp,
		propertySpec:    propertySpec,
		parameters:      parameters,
		overwriteInput:  overwriteInput,
		cache:           sync.Map{},
		calculationDate: calculationDate,
		approved:        approved,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecServiceResolver) Resolve(ctx context.Context, key string) (*resolver.Resolved, bool) {
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

	value, missingRequired, err := l.resolveFromService(ctx, key, *serviceRef, spec)
	if err != nil {
		return nil, false
	}

	logger.FromContext(ctx).WithName("resolver").
		Debugf("Result for $%s from %s field %s: %v", key, serviceRef.Service, serviceRef.Field, value)

	required := false
	if spec.GetBase().Required != nil {
		required = *spec.GetBase().Required
	}

	resolved := &resolver.Resolved{
		Value:           value,
		Required:        required,
		MissingRequired: &missingRequired,
	}

	// Add type information to the node
	if spec.GetBase().Type != "" {
		resolved.Details.Type = spec.GetBase().Type
	}

	if spec.GetBase().TypeSpec != nil {
		resolved.Details.TypeSpec = spec.GetBase().TypeSpec.ToMap()
	}

	return resolved, true

}

// resolveFromService resolves a value from a service
func (l *PropertySpecServiceResolver) resolveFromService(
	ctx context.Context,
	ppath string,
	serviceRef ruleresolver.ServiceReference,
	spec ruleresolver.Field,
) (any, bool, error) {

	logr := logger.FromContext(ctx)

	// Clone parameters
	parameters := make(map[string]any)
	maps.Copy(parameters, l.parameters)

	logr.Info("parameters", logger.NewField("parameters", parameters))

	// Add service reference parameters
	for _, param := range serviceRef.Parameters {
		value, err := l.rc.ResolveValue(ctx, param.Reference)
		if err != nil {
			return nil, false, err
		}
		parameters[param.Name] = value
	}

	// Get reference date
	referenceDate := l.calculationDate
	if spec.GetBase().Temporal != nil {
		if reference, ok := spec.GetBase().Temporal.Reference.(string); ok {
			refDate, err := l.rc.ResolveValue(ctx, reference)
			if err != nil {
				return nil, false, err
			}

			if refDateStr, ok := refDate.(string); ok {
				referenceDate = refDateStr
			}
		}
	}

	key := getCacheKey(ppath, referenceDate, parameters)
	if val, ok := l.cache.Load(key); ok {
		if v, ok := val.(CachedValue); ok {
			logr.WithIndent().Debugf("Resolving from CACHE with key '%s': %v", key, v.value)
			return v.value, v.missingRequired, nil
		}
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

	result, err := l.sp.Evaluate(
		ctx,
		serviceRef.Service,
		serviceRef.Law,
		parameters,
		referenceDate,
		l.overwriteInput,
		serviceRef.Field,
		l.approved,
	)
	if err != nil {
		return nil, false, err
	}

	value := result.Output[serviceRef.Field]
	l.cache.Store(key, CachedValue{value: value, missingRequired: result.MissingRequired})

	// Update the service node with the result and add child path
	serviceNode.Result = value
	if result.Path != nil {
		serviceNode.AddChild(result.Path)
	}

	// rc.MissingRequired |= result.MissingRequired

	return value, result.MissingRequired, nil
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
