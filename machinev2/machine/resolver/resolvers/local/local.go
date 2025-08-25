package local

import (
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	resolvermap "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/map"
)

var _ resolver.Resolver = &LocalResolver{}

type LocalResolver struct {
	resolvermap.MapResolver
}

func NewLocalResolver() *LocalResolver {
	return &LocalResolver{
		MapResolver: *resolvermap.New(make(map[string]any), "LOCAL"),
	}
}
