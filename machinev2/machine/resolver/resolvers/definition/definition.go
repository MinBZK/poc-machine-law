package definition

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	resolvermap "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/map"
)

var _ resolver.Resolver = &DefinitionsResolver{}

type DefinitionsResolver struct {
	resolvermap.MapResolver
}

func New(data map[string]any) *DefinitionsResolver {
	return &DefinitionsResolver{
		MapResolver: *resolvermap.New(data, "DEFINITION"),
	}
}

// Resolve implements Resolver with special handling for legal_basis metadata.
func (d *DefinitionsResolver) Resolve(_ context.Context, key string) (*resolver.Resolved, bool) {
	v, ok := d.Get(key)
	if !ok {
		return nil, false
	}

	// Check if the definition contains both 'value' and 'legal_basis' fields
	if defMap, isMap := v.(map[string]any); isMap {
		if value, hasValue := defMap["value"]; hasValue {
			if _, hasLegalBasis := defMap["legal_basis"]; hasLegalBasis {
				// Extract only the value, ignoring legal_basis metadata
				return &resolver.Resolved{Value: value}, true
			}
		}
	}

	// Return the value as-is for normal definitions
	return &resolver.Resolved{Value: v}, ok
}
