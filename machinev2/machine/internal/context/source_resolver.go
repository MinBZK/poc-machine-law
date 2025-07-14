package context

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

var _ Resolver = &PropertySpecSourceResolver{}

type PropertySpecSourceResolver struct {
	rc                    *RuleContext
	propertySpec          map[string]ruleresolver.Field
	externalClaimResolver *ExternalClaimResolver
}

func NewPropertySpecSourceResolver(rc *RuleContext, propertySpec map[string]ruleresolver.Field) *PropertySpecSourceResolver {
	var externalClaimResolver *ExternalClaimResolver
	if rc.ServiceProvider.HasExternalClaimResolverEndpoint() {
		externalClaimResolver = NewExternalClaimResolver(rc.ServiceProvider.GetExternalClaimResolverEndpoint(), propertySpec)
	}

	return &PropertySpecSourceResolver{
		rc:                    rc,
		propertySpec:          propertySpec,
		externalClaimResolver: externalClaimResolver,
	}
}

// Resolve implements Resolver.
func (l *PropertySpecSourceResolver) Resolve(ctx context.Context, key string) (*Resolved, bool) {
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

	value, err := l.resolveFromSourceReference(ctx, *sourceRef)
	if err != nil {
		// logger.Debugf(ctx, "resolving from source: %s", err)
		return nil, false
	}

	if value == nil {
		return nil, false
	}

	required := false
	if spec.GetBase().Required != nil {
		required = *spec.GetBase().Required
	}

	resolved := &Resolved{
		Value:    value,
		Required: required,
		Details:  make(map[string]any),
	}

	// Add type information to the node
	if spec.GetBase().Type != "" {
		resolved.Details["type"] = spec.GetBase().Type
	}

	if spec.GetBase().TypeSpec != nil {
		resolved.Details["type_spec"] = spec.GetBase().TypeSpec.ToMap()
	}

	logging.FromContext(ctx).Debugf(ctx, "Resolving from SOURCE %v: %v", sourceRef.Table, value)

	return resolved, true

}

// ResolveType implements Resolver.
func (l *PropertySpecSourceResolver) ResolveType() string {
	return "SOURCE"
}

// resolveFromSourceReference resolves a value from a data source
func (l *PropertySpecSourceResolver) resolveFromSourceReference(
	ctx context.Context,
	sourceRef ruleresolver.SourceReference) (any, error) {

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
		df, err = l.resolveFromSourceReferenceTable(ctx, sourceRef)
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
			l.rc.logger.WithIndent().Warningf(ctx, "Fields %v not found in source for table %s", missingFields, tableName)
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
			l.rc.logger.WithIndent().Warningf(ctx, "Field %s not found in source for table %s", *sourceRef.Field, tableName)
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
	df := model.DataFrame(dataframe.New(l.rc.ServiceProvider.GetRuleResolver().RulesDataFrame()))
	df, err := l.filter(ctx, sourceRef, df)
	if err != nil {
		return nil, fmt.Errorf("filter: %w", err)
	}

	return df, nil
}

func (l *PropertySpecSourceResolver) resolveFromSourceReferenceEvents(ctx context.Context, sourceRef ruleresolver.SourceReference) (model.DataFrame, error) {
	// TODO: improve, currently all events are getting queried
	caseManager := l.rc.ServiceProvider.GetCaseManager()

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

func (l *PropertySpecSourceResolver) resolveFromSourceReferenceTable(ctx context.Context, sourceRef ruleresolver.SourceReference) (model.DataFrame, error) {
	if df, exists := l.rc.Sources.Get(sourceRef.Table); exists {
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

		filters = append(filters, Filter{Value: value, Operation: operation, Key: selectCond.Name})
	}

	resolved, ok := l.externalClaimResolver.Resolve(ctx, sourceRef.Table, *sourceRef.Field, filters)
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

type ExternalClaimResolver struct {
	endpoint     string
	client       *http.Client
	propertySpec map[string]ruleresolver.Field
}

type Filter struct {
	Key       string `json:"key"`
	Value     any    `json:"value"`
	Operation string `json:"operation"`
}

type Filters []Filter

func NewExternalClaimResolver(endpoint string, propertySpec map[string]ruleresolver.Field) *ExternalClaimResolver {
	return &ExternalClaimResolver{
		propertySpec: propertySpec,
		endpoint:     endpoint,
		client:       http.DefaultClient,
	}
}

// Resolve implements Resolver.
func (c *ExternalClaimResolver) Resolve(ctx context.Context, table string, field string, filters Filters) (*Resolved, bool) {
	logger := logging.FromContext(ctx)
	logger = logger.WithField("resolver", "external_claim")

	value, err := c.do(ctx, table, field, filters)
	if err != nil {
		logger.Errorf(ctx, "could not execute external claim: %w", err)
		return nil, false
	}

	if value == nil {
		logger.Warningf(ctx, "external claim empty")
		return nil, false
	}

	logger.Debugf(ctx, "value: %v", value)

	resolved := &Resolved{
		Value:   value,
		Details: make(map[string]any),
	}

	// Add type information for claims
	if spec, ok := c.propertySpec[field]; ok {
		if spec.GetBase().Type != "" {
			resolved.Details["type"] = spec.GetBase().Type
		}

		if spec.GetBase().TypeSpec != nil {
			resolved.Details["type_spec"] = map[string]any{
				"type":      spec.GetBase().TypeSpec.Type,
				"unit":      spec.GetBase().TypeSpec.Unit,
				"precision": spec.GetBase().TypeSpec.Precision,
				"min":       spec.GetBase().TypeSpec.Min,
				"max":       spec.GetBase().TypeSpec.Max,
			}
		}

		required := false
		if spec.GetBase().Required != nil {
			required = *spec.GetBase().Required
		}
		resolved.Required = required
	}

	return resolved, true
}

// Resolve implements Resolver.
func (c *ExternalClaimResolver) do(ctx context.Context, table string, field string, filters Filters) (any, error) {
	logger := logging.FromContext(ctx)
	logger = logger.WithField("resolver", "external_claim").
		WithField("table", table).
		WithField("field", field).
		WithField("filters", filters)

	endpoint, err := url.Parse(fmt.Sprintf("%s%s", c.endpoint, table))
	if err != nil {
		return nil, fmt.Errorf("url parse: %w", err)
	}

	b := &bytes.Buffer{}
	if err := json.NewEncoder(b).Encode(filters); err != nil {
		return nil, fmt.Errorf("encode: %w", err)
	}

	values := url.Values{}
	values.Add("fields", field)
	values.Add("filter", b.String())

	endpoint.RawQuery = values.Encode()

	logger.Debug(ctx, "url parse", logging.NewField("endpoint", endpoint))

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("new request with context: %w", err)
	}
	logger.Debug(ctx, "do request")

	response, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("do: %w", err)
	}

	logger.Debug(ctx, "request done")

	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		dump, _ := httputil.DumpResponse(response, true)
		return nil, fmt.Errorf("invalid http status: %d %v", response.StatusCode, string(dump))
	}

	body := []map[string]any{}
	if err := json.NewDecoder(response.Body).Decode(&body); err != nil {
		return nil, fmt.Errorf("json decode: %w", err)
	}

	switch len(body) {
	case 0:
		return nil, fmt.Errorf("field not found")
	case 1:
		return body[0][field], nil
	default:
		panic("unimplemented, multiple returns")
	}
}

func (c *ExternalClaimResolver) ResolveType() string {
	return "EXTERNAL_CLAIM"
}
