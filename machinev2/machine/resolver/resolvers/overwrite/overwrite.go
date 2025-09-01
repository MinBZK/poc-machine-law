package overwrite

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

var _ resolver.Resolver = &PropertySpecOverwriteResolver{}

type PropertySpecOverwriteResolver struct {
	propertySpec   map[string]ruleresolver.Field
	overwriteInput map[string]map[string]any
}

func New(propertySpec map[string]ruleresolver.Field, overwriteInput map[string]map[string]any) *PropertySpecOverwriteResolver {
	return &PropertySpecOverwriteResolver{
		propertySpec:   propertySpec,
		overwriteInput: overwriteInput,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecOverwriteResolver) Resolve(ctx context.Context, key string) (*resolver.Resolved, bool) {
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

	return &resolver.Resolved{Value: value}, true
}

// ResolveType implements Resolver.
func (l *PropertySpecOverwriteResolver) ResolveType() string {
	return "OVERWRITE"
}
