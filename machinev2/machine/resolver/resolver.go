package resolver

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

type Resolved struct {
	Value           any
	MissingRequired *bool
}

type Resolver interface {
	Resolve(ctx context.Context, key string) (*Resolved, bool)
	ResolveType() string
}

type RuleContexter interface {
	ResolveAction(context.Context, ruleresolver.Action) (any, error)
	ResolveValue(context.Context, any) (any, error)
}
