package output

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	resolvermap "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/map"
)

var _ resolver.Resolver = &OutputsResolver{}

type OutputsResolver struct {
	resolvermap.MapResolver
}

func NewOutputsResolver() *OutputsResolver {
	return &OutputsResolver{
		MapResolver: *resolvermap.New(make(map[string]any), "OUTPUT"),
	}
}

// Resolve implements Resolver.
func (l *OutputsResolver) Resolve(_ context.Context, key string) (*resolver.Resolved, bool) {
	v, ok := l.Get(key)
	return &resolver.Resolved{Value: v}, ok
}
