package source

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
)

type ExternalClaimResolver struct {
	resolver externalResolver
}

type Filter struct {
	Key       string `json:"key"`
	Value     any    `json:"value"`
	Operation string `json:"operation"`
}

type Filters []Filter

func NewExternalClaimResolver(resolver externalResolver) *ExternalClaimResolver {
	return &ExternalClaimResolver{
		resolver: resolver,
	}
}

// Resolve implements Resolver.
func (c *ExternalClaimResolver) Resolve(
	ctx context.Context,
	key string,
	table string,
	field string,
	filters Filters,
) (*resolver.Resolved, bool) {
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

	return &resolver.Resolved{
		Value: value,
	}, true
}
