package claim

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

var _ resolver.Resolver = &ClaimResolver{}

type ClaimResolver struct {
	claims       map[string]model.Claim
	propertySpec map[string]ruleresolver.Field
}

func New(claims map[string]model.Claim, propertySpec map[string]ruleresolver.Field) *ClaimResolver {
	return &ClaimResolver{
		claims:       claims,
		propertySpec: propertySpec,
	}
}

// Resolve implements Resolver.
func (c *ClaimResolver) Resolve(ctx context.Context, key string) (*resolver.Resolved, bool) {
	claim, exists := c.claims[key]
	if !exists {
		return nil, false
	}

	resolved := &resolver.Resolved{
		Value: claim.NewValue,
	}

	// Add type information for claims
	if spec, ok := c.propertySpec[key]; ok {
		if spec.GetBase().Type != "" {
			resolved.Details.Type = spec.GetBase().Type
		}

		if spec.GetBase().TypeSpec != nil {
			resolved.Details.TypeSpec = spec.GetBase().TypeSpec.ToMap()
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
