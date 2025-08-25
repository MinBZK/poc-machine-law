package source

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

type externalResolver interface {
	do(ctx context.Context, key string, table string, field string, filters Filters) (any, error)
}

var _ resolver.Resolver = &PropertySpecSourceResolver{}

type PropertySpecSourceResolver struct {
	rc                    resolver.RuleContexter
	sp                    service.ServiceProvider
	sources               model.SourceDataFrame
	propertySpec          map[string]ruleresolver.Field
	externalClaimResolver *ExternalClaimResolver
}

func New(rc resolver.RuleContexter, sp service.ServiceProvider, sources model.SourceDataFrame, propertySpec map[string]ruleresolver.Field) *PropertySpecSourceResolver {
	var externalClaimResolver *ExternalClaimResolver
	if sp.HasExternalClaimResolverEndpoint() {
		externalClaimResolver = NewExternalClaimResolver(sp.GetExternalClaimResolverEndpoint(), propertySpec)
	}

	return &PropertySpecSourceResolver{
		rc:                    rc,
		sp:                    sp,
		sources:               sources,
		propertySpec:          propertySpec,
		externalClaimResolver: externalClaimResolver,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecSourceResolver) Resolve(ctx context.Context, key string) (*resolver.Resolved, bool) {
	spec, ok := l.propertySpec[key]
	if !ok {
		return nil, false
	}

	var sourceRef *ruleresolver.SourceReference
	if spec.Source != nil {
		sourceRef = spec.Source.SourceReference
	}

	// Check sources
	if sourceRef == nil {
		return nil, false
	}

	value, err := l.resolveFromSourceReference(ctx, key, *sourceRef)
	if err != nil {
		// logger.Debugf( "resolving from source: %s", err)
		return nil, false
	}

	if value == nil {
		return nil, false
	}

	required := false
	if spec.GetBase().Required != nil {
		required = *spec.GetBase().Required
	}

	resolved := &resolver.Resolved{
		Value:    value,
		Required: required,
	}

	// Add type information to the node
	if spec.GetBase().Type != "" {
		resolved.Details.Type = spec.GetBase().Type
	}

	if spec.GetBase().TypeSpec != nil {
		resolved.Details.TypeSpec = spec.GetBase().TypeSpec.ToMap()
	}

	logger.FromContext(ctx).Debugf("Resolving from SOURCE %v: %v", sourceRef.Table, value)

	return resolved, true

}

// ResolveType implements Resolver.
func (l *PropertySpecSourceResolver) ResolveType() string {
	return "SOURCE"
}

// resolveFromSourceReference resolves a value from a data source
func (l *PropertySpecSourceResolver) resolveFromSourceReference(
	ctx context.Context,
	key string,
	sourceRef ruleresolver.SourceReference) (any, error) {

	logger := logger.FromContext(ctx)

	var df model.DataFrame
	var err error
	tableName := sourceRef.SourceType

	// Determine the DataFrame to use
	switch tableName {
	case "laws":
		df, err = l.resolveFromSourceReferenceLaws(ctx, sourceRef)
	case "events":
		df, err = l.resolveFromSourceReferenceEvents(ctx, sourceRef)
	default:
		df, err = l.resolveFromSourceReferenceTable(ctx, key, sourceRef)
	}

	if err != nil {
		return nil, fmt.Errorf("resolve from source reference %s: %w", tableName, err)
	}

	// Get results according to requested fields
	var result any

	if sourceRef.Fields != nil {
		// Check if all requested fields exist
		missingFields := []string{}
		for _, field := range *sourceRef.Fields {
			if !df.HasColumn(field) {
				missingFields = append(missingFields, field)
			}
		}

		if len(missingFields) > 0 {
			logger.WithIndent().Warningf("Fields %v not found in source for table %s", missingFields, tableName)
		}

		// Get existing fields
		existingFields := []string{}
		for _, field := range *sourceRef.Fields {
			if df.HasColumn(field) {
				existingFields = append(existingFields, field)
			}
		}

		result = df.Select(existingFields).ToRecords()
	} else if sourceRef.Field != nil {
		if !df.HasColumn(*sourceRef.Field) {
			logger.WithIndent().Warningf("Field %s not found in source for table %s", *sourceRef.Field, tableName)
			return nil, nil
		}
		result = df.GetColumnValues(*sourceRef.Field)
	} else {
		result = df.ToRecords()
	}

	if result == nil {
		return nil, nil
	}

	// Handle array results
	switch r := result.(type) {
	case []any:
		if len(r) == 0 {
			return nil, nil
		}
		if len(r) == 1 {
			return r[0], nil
		}
	case []map[string]any:
		if len(r) == 0 {
			return nil, nil
		}
		if len(r) == 1 {
			return r[0], nil
		}
	}

	return result, nil
}

// resolveFromSourceReference resolves a value from a data source
func (l *PropertySpecSourceResolver) resolveFromSourceReferenceLaws(ctx context.Context, sourceRef ruleresolver.SourceReference) (model.DataFrame, error) {
	df := model.DataFrame(dataframe.New(l.sp.GetRuleResolver().RulesDataFrame()))
	df, err := l.filter(ctx, sourceRef, df)
	if err != nil {
		return nil, fmt.Errorf("filter: %w", err)
	}

	return df, nil
}

func (l *PropertySpecSourceResolver) resolveFromSourceReferenceEvents(ctx context.Context, sourceRef ruleresolver.SourceReference) (model.DataFrame, error) {
	// TODO: improve, currently all events are getting queried
	caseManager := l.sp.GetCaseManager()

	// Get events from case manager
	events := caseManager.GetEvents(nil)

	data := make([]map[string]any, 0, len(events))
	for idx := range events {
		data = append(data, events[idx].ToMap())
	}

	// Create a dataframe from events
	df := model.DataFrame(dataframe.New(data))
	df, err := l.filter(ctx, sourceRef, df)
	if err != nil {
		return nil, fmt.Errorf("filter: %w", err)
	}

	return df, nil
}

func (l *PropertySpecSourceResolver) resolveFromSourceReferenceTable(ctx context.Context, key string, sourceRef ruleresolver.SourceReference) (model.DataFrame, error) {
	if df, exists := l.sources.Get(sourceRef.Table); exists {
		df, err := l.filter(ctx, sourceRef, df)
		if err != nil {
			return nil, fmt.Errorf("filter: %w", err)
		}
		return df, nil
	}

	if l.externalClaimResolver == nil {
		return nil, fmt.Errorf("table '%s' not found in sources", sourceRef.Table)
	}

	// Apply filters
	filters := Filters{}
	for _, selectCond := range sourceRef.SelectOn {
		var value any
		var err error

		operation := "="

		if selectCond.Value.Action != nil {
			action, err := l.rc.ResolveAction(ctx, *selectCond.Value.Action)
			if err != nil {
				return nil, err
			}

			value, err = l.rc.ResolveValue(ctx, action)
			if err != nil {
				return nil, err
			}

			if *selectCond.Value.Action.Operation == "IN" {
				operation = "in"
			}

		} else if selectCond.Value.Value != nil {
			value, err = l.rc.ResolveValue(ctx, *selectCond.Value.Value)
			if err != nil {
				return nil, err
			}
		}

		if value != nil && selectCond.Name != "" {
			filters = append(filters, Filter{Value: value, Operation: operation, Key: selectCond.Name})
		}
	}

	if len(filters) == 0 {
		return nil, fmt.Errorf("zero filters active")
	}

	resolved, ok := l.externalClaimResolver.Resolve(ctx, key, sourceRef.Table, *sourceRef.Field, filters)
	if !ok {
		return nil, fmt.Errorf("external claim did not resolve")
	}

	return dataframe.New([]map[string]any{
		{
			*sourceRef.Field: resolved.Value,
		},
	}), nil
}

func (l *PropertySpecSourceResolver) filter(ctx context.Context, sourceRef ruleresolver.SourceReference, df model.DataFrame) (model.DataFrame, error) {

	// Apply filters
	for _, selectCond := range sourceRef.SelectOn {
		var value any
		var err error
		operation := "="

		if selectCond.Value.Action != nil {
			action, err := l.rc.ResolveAction(ctx, *selectCond.Value.Action)
			if err != nil {
				return nil, err
			}

			value, err = l.rc.ResolveValue(ctx, action)
			if err != nil {
				return nil, err
			}

			if *selectCond.Value.Action.Operation == "IN" {
				operation = "in"
			}

		} else if selectCond.Value.Value != nil {
			value, err = l.rc.ResolveValue(ctx, *selectCond.Value.Value)
			if err != nil {
				return nil, err
			}
		}

		// Standard equality filter
		df, err = df.Filter(selectCond.Name, operation, value)
		if err != nil {
			return nil, err
		}
	}

	return df, nil
}

func (c *ExternalClaimResolver) ResolveType() string {
	return "EXTERNAL_CLAIM"
}
