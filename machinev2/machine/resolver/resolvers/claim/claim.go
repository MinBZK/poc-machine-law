package claim

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
)

var _ resolver.Resolver = &ClaimResolver{}

type ClaimResolver struct {
	claims map[string]model.Claim
}

func New(claims map[string]model.Claim) *ClaimResolver {
	return &ClaimResolver{
		claims: claims,
	}
}

// Resolve implements Resolver.
func (c *ClaimResolver) Resolve(_ context.Context, key string) (*resolver.Resolved, bool) {
	claim, exists := c.claims[key]
	if !exists {
		return nil, false
	}

	resolved := &resolver.Resolved{
		Value: claim.NewValue,
	}

	return resolved, true
}

func (c *ClaimResolver) ResolveType() string {
	return "CLAIM"
}
