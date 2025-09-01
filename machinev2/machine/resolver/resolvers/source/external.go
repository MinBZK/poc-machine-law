package source

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

type ExternalClaimResolver struct {
	resolver     externalResolver
	propertySpec map[string]ruleresolver.Field
}

type Filter struct {
	Key       string `json:"key"`
	Value     any    `json:"value"`
	Operation string `json:"operation"`
}

type Filters []Filter

func NewExternalClaimResolver(endpoint string, propertySpec map[string]ruleresolver.Field) *ExternalClaimResolver {
	var resolver externalResolver

	resolver = newDefaultResolver(endpoint)
	resolver = newUBBResolver(endpoint, propertySpec)

	return &ExternalClaimResolver{
		propertySpec: propertySpec,
		resolver:     resolver,
	}
}

// Resolve implements Resolver.
func (c *ExternalClaimResolver) Resolve(ctx context.Context, key string, table string, field string, filters Filters) (*resolver.Resolved, bool) {
	logr := logger.FromContext(ctx).WithName("resolver")
	logr = logr.WithField("resolver", "external_claim")

	value, err := c.resolver.do(ctx, key, table, field, filters)
	if err != nil {
		logr.Errorf("could not execute external claim: %w", err)
		return nil, false
	}

	if value == nil {
		logr.Warningf("external claim empty")
		return nil, false
	}

	resolved := &resolver.Resolved{
		Value: value,
	}

	// Add type information for claims
	if spec, ok := c.propertySpec[field]; ok {
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
