package parameter

import (
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	resolvermap "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/map"
)

var _ resolver.Resolver = &ParametersResolver{}

type ParametersResolver struct {
	resolvermap.MapResolver
}

func New(data map[string]any) *ParametersResolver {
	return &ParametersResolver{
		MapResolver: *resolvermap.New(data, "PARAMETER"),
	}
}
