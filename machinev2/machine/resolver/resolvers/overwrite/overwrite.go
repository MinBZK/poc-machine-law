package overwrite

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

var _ resolver.Resolver = &PropertySpecOverwriteResolver{}

type PropertySpecOverwriteResolver struct {
	service        string
	propertySpec   map[string]ruleresolver.Field
	overwriteInput map[string]map[string]any
}

func New(service string, propertySpec map[string]ruleresolver.Field, overwriteInput map[string]map[string]any) *PropertySpecOverwriteResolver {
	return &PropertySpecOverwriteResolver{
		service:        service,
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

	if spec.Input != nil {
		return l.resolveServiceReference(spec.Input.ServiceReference)
	} else if spec.Source != nil {
		if spec.Source.ServiceReference != nil {
			return l.resolveServiceReference(*spec.Source.ServiceReference)
		} else if spec.Source.SourceReference != nil {
			return l.resolveSourceReference(*spec.Source.SourceReference)
		}
	}

	return nil, false
}

// ResolveType implements Resolver.
func (l *PropertySpecOverwriteResolver) ResolveType() string {
	return "OVERWRITE"
}

func (l *PropertySpecOverwriteResolver) resolveServiceReference(serviceRef ruleresolver.ServiceReference) (*resolver.Resolved, bool) {
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

func (l *PropertySpecOverwriteResolver) resolveSourceReference(sourceRef ruleresolver.SourceReference) (*resolver.Resolved, bool) {
	input, ok := l.overwriteInput[l.service]
	if !ok {
		return nil, false
	}

	if sourceRef.Field != nil {
		if value, ok := input[*sourceRef.Field]; ok {
			return &resolver.Resolved{Value: value}, true
		}

	}

	if sourceRef.Fields != nil {
		for _, field := range *sourceRef.Fields {
			if value, ok := input[field]; ok {
				return &resolver.Resolved{Value: value}, true
			}

		}
	}

	return nil, false
}
