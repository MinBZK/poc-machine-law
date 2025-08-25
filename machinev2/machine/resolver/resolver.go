package resolver

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

type Resolved struct {
	Value           any
	Required        bool
	MissingRequired *bool
	Details         Details
}

type Details struct {
	Type     string
	TypeSpec map[string]any
}

func (d Details) ToMap() map[string]any {
	return map[string]any{
		"type":      d.Type,
		"type_spec": d.TypeSpec,
	}
}

type Resolver interface {
	Resolve(ctx context.Context, key string) (*Resolved, bool)
	ResolveType() string
}

type RuleContexter interface {
	ResolveAction(context.Context, ruleresolver.Action) (any, error)
	ResolveValue(context.Context, any) (any, error)
}
