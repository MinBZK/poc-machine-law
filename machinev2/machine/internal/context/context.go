package context

import (
	"context"
	"fmt"
	"maps"
	"reflect"
	"strings"
	"sync"
	"time"
	"unicode"

	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/path"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/tracker"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/serviceresolver"
)

// ServiceProvider interface defines what a service provider needs to implement
type ServiceProvider interface {
	Evaluate(ctx context.Context, service, law string, parameters map[string]any, referenceDate string,
		overwriteInput map[string]map[string]any, requestedOutput string, approved bool) (*model.RuleResult, error)
	GetRuleResolver() *ruleresolver.RuleResolver
	GetServiceResolver() *serviceresolver.ServiceResolver
	GetCaseManager() CaseManagerAccessor
	GetClaimManager() ClaimManagerAccessor
	RuleServicesInMemory() bool
	HasOrganizationName() bool
	GetOrganizationName() string
	InStandAloneMode() bool
}

// CaseManagerAccessor interface for accessing case manager events
type CaseManagerAccessor interface {
	GetEvents(caseID any) []model.Event
}

// ClaimManagerAccessor interface for accessing claim manager functionality
type ClaimManagerAccessor interface {
	GetClaimsByBSN(bsn string, approved bool, includeRejected bool) ([]model.Claim, error)
	GetClaimByBSNServiceLaw(bsn string, service string, law string, approved bool, includeRejected bool) (map[string]model.Claim, error)
}

type RuleContextData struct {
	ServiceProvider ServiceProvider
	Parameters      map[string]any
	PropertySpecs   map[string]ruleresolver.Field
	Sources         model.SourceDataFrame
	CalculationDate string
	Approved        bool
}

// RuleContext holds context for rule evaluation
type RuleContext struct {
	ServiceProvider ServiceProvider
	Parameters      map[string]any
	PropertySpecs   map[string]ruleresolver.Field
	Sources         model.SourceDataFrame
	ValuesCache     *sync.Map
	OverwriteInput  map[string]map[string]any
	CalculationDate string
	LocalResolver   *LocalResolver
	OutputsResolver *OutputsResolver
	Resolvers       []Resolver
	Approved        bool
	MissingRequired bool
	logger          logging.Logger
}

// NewRuleContext creates a new rule context
func NewRuleContext(logr logging.Logger, definitions map[string]any, serviceProvider ServiceProvider,
	parameters map[string]any, propertySpecs map[string]ruleresolver.Field,
	outputSpecs map[string]model.TypeSpec, sources model.SourceDataFrame,
	overwriteInput map[string]map[string]any, calculationDate string,
	serviceName string, claims map[string]model.Claim, approved bool) *RuleContext {

	local := NewLocalResolver()
	output := NewOutputsResolver()

	rc := &RuleContext{
		ServiceProvider: serviceProvider,
		Parameters:      parameters,
		PropertySpecs:   propertySpecs,
		Sources:         sources,
		ValuesCache:     new(sync.Map),
		OverwriteInput:  overwriteInput,
		CalculationDate: calculationDate,
		Approved:        approved,
		MissingRequired: false,
		LocalResolver:   local,
		OutputsResolver: output,
		logger:          logr.WithName("context"),
	}

	rc.Resolvers = []Resolver{
		NewClaimResolver(claims, propertySpecs),
		local,
		NewDefinitionsResolver(definitions),
		NewParametersResolver(parameters),
		output,
		NewPropertySpecOverwriteResolver(propertySpecs, overwriteInput),
		NewPropertySpecSourceResolver(rc, propertySpecs),
		NewPropertySpecServiceResolver(rc, propertySpecs),
		NewExternalClaimResolver("http://belastingdienst-backend-svc/box1/1", parameters["BSN"].(string), propertySpecs),
	}

	return rc
}

func (rc *RuleContext) ResolveAction(ctx context.Context, action ruleresolver.Action) (any, error) {
	if action.Value != nil {
		return *action.Value, nil
	} else if action.Values != nil {
		if action.Values.ActionValues != nil {
			return *action.Values.ActionValues, nil
		} else if action.Values.Value != nil {
			return *action.Values.Value, nil
		}
	}

	return nil, fmt.Errorf("action not set")
}

// ResolveValue resolves a value from definitions, services, or sources
func (rc *RuleContext) ResolveValue(ctx context.Context, path any) (any, error) {
	var value any
	if err := rc.logger.IndentBlock(ctx, fmt.Sprintf("Resolving path: %v", path), func(ctx context.Context) error {
		var err error
		if value, err = rc.resolveValueInternal(ctx, path); err != nil {
			return err
		}

		if strPath, ok := path.(string); ok {
			tracker.WithResolvedPath(ctx, strPath, value)
		}

		return nil
	}); err != nil {
		return nil, err
	}

	return value, nil
}

func (rc *RuleContext) resolveValueInternal(ctx context.Context, key any) (any, error) {
	node := &model.PathNode{
		Type:    "resolve",
		Name:    fmt.Sprintf("Resolving value: %v", key),
		Result:  nil,
		Details: map[string]any{"path": key},
	}

	ctx = path.WithPathNode(ctx, node)
	defer path.FromContext(ctx).Pop()

	// If path is not a string or doesn't start with $, return it as is
	strPath, ok := key.(string)
	if !ok || !strings.HasPrefix(strPath, "$") {
		node.Result = key
		return key, nil
	}

	strPath = strPath[1:]

	logger := logging.FromContext(ctx)

	// Resolve dates first
	dateValue, err := resolveDate(strPath, rc.CalculationDate)
	if err == nil && dateValue != nil {
		logger.Debugf(ctx, "Resolved date $%s: %v", strPath, dateValue)
		node.Result = dateValue
		return dateValue, nil
	}

	// Handle paths with dots (nested access)
	if strings.Contains(strPath, ".") {
		parts := strings.SplitN(strPath, ".", 2)
		root, rest := parts[0], parts[1]

		rootValue, err := rc.ResolveValue(ctx, "$"+root)
		if err != nil {
			return nil, err
		}

		if rootValue == nil {
			logger.Warningf(ctx, "Value is nil, could not resolve value $%s: nil", strPath)
			node.Result = nil
			return nil, nil
		}

		// Navigate through the nested path
		pathParts := strings.Split(rest, ".")
		currentValue := rootValue

		for _, part := range pathParts {
			rValue := reflect.ValueOf(currentValue)
			if rValue.Kind() == reflect.Pointer {
				rValue = rValue.Elem()
			}

			if currentValue == nil {
				logger.Warningf(ctx, "Value is nil, could not resolve nested path $%s.%s", root, rest)
				node.Result = nil
				return nil, nil
			}

			// Handle map
			if rValue.Kind() == reflect.Map {
				mapValue := rValue.MapIndex(reflect.ValueOf(part))
				if !mapValue.IsValid() {
					logger.Warningf(ctx, "Key %s not found in map, could not resolve value $%s", part, strPath)
					node.Result = nil
					return nil, nil
				}
				currentValue = mapValue.Interface()
			} else if rValue.Kind() == reflect.Struct {

				var field reflect.Value
				// We are asking for a Public field
				if unicode.IsUpper(rune(part[0])) {
					// Handle struct
					field = rValue.FieldByName(part)
					if !field.IsValid() {
						logger.Warningf(ctx, "Field %s not found in struct, could not resolve value $%s", part, strPath)
						node.Result = nil
						return nil, nil
					}
				} else {
					// we are asking for a json based struct tag

					typ := rValue.Type()
					// Iterate through all fields of the struct
					for i := range rValue.NumField() {
						f := typ.Field(i)

						// Get the json tag value
						tag := f.Tag.Get("json")

						// Split the tag value by comma to handle options like omitempty
						tagParts := strings.Split(tag, ",")

						// Compare the tag name with the requested jsonTag
						if tagParts[0] == part {
							field = rValue.Field(i)
							break
						}
					}
				}

				if field.Kind() == reflect.Pointer {
					field = field.Elem()
				}

				currentValue = field.Interface()
			} else {
				logger.Warningf(ctx, "Value is not map or struct, could not resolve value $%s", strPath)
				node.Result = nil
				return nil, nil
			}
		}

		logger.Debugf(ctx, "Resolved value $%s: %v", strPath, currentValue)
		node.Result = currentValue
		return currentValue, nil
	}

	for _, resolve := range rc.Resolvers {
		if resolved, ok := resolve.Resolve(ctx, strPath); ok {
			node.Result = resolved.Value
			node.ResolveType = resolve.ResolveType()
			maps.Copy(node.Details, resolved.Details)

			logger.Debugf(ctx, "Resolving from %s: %v", resolve.ResolveType(), resolved.Value)

			return resolved.Value, nil
		}
	}

	// Handle property specs
	if spec, exists := rc.PropertySpecs[strPath]; exists {
		// Handle required fields
		node.Required = false
		if spec.GetBase().Required != nil {
			node.Required = *spec.GetBase().Required
		}

		if node.Required {
			rc.MissingRequired = true
		}

		// Add type information
		if spec.GetBase().Type != "" {
			node.Details["type"] = spec.GetBase().Type
		}

		if spec.GetBase().TypeSpec != nil {
			node.Details["type_spec"] = spec.GetBase().TypeSpec.ToMap()
		}
	}

	logger.Warningf(ctx, "Could not resolve value for %s", strPath)
	node.Result = nil
	node.ResolveType = "NONE"

	return nil, nil
}

// resolveDate handles special date-related paths
func resolveDate(path string, date string) (any, error) {
	if path == "calculation_date" {
		return date, nil
	}

	if path == "january_first" {
		calcDate, err := time.Parse("2006-01-02", date)
		if err != nil {
			return nil, err
		}
		januaryFirst := time.Date(calcDate.Year(), 1, 1, 0, 0, 0, 0, calcDate.Location())
		return januaryFirst.Format("2006-01-02"), nil
	}

	if path == "prev_january_first" {
		calcDate, err := time.Parse("2006-01-02", date)
		if err != nil {
			return nil, err
		}
		prevJanuaryFirst := time.Date(calcDate.Year()-1, 1, 1, 0, 0, 0, 0, calcDate.Location())
		return prevJanuaryFirst.Format("2006-01-02"), nil
	}

	if path == "year" {
		if len(date) >= 4 {
			return date[:4], nil
		}
	}

	return nil, fmt.Errorf("not a date path")
}

// resolveFromSource resolves a value from a data source
func (rc *RuleContext) resolveFromSource(
	ctx context.Context,
	sourceRef ruleresolver.SourceReference) (any, error) {

	var df model.DataFrame
	tableName := ""

	// Determine the DataFrame to use
	if sourceRef.SourceType == "laws" {
		tableName = "laws"

		df = dataframe.New(rc.ServiceProvider.GetRuleResolver().RulesDataFrame())
	} else if sourceRef.SourceType == "events" {
		tableName = "events"

		caseManager := rc.ServiceProvider.GetCaseManager()

		// Get events from case manager
		events := caseManager.GetEvents(nil)

		data := make([]map[string]any, 0, len(events))
		for idx := range events {
			data = append(data, events[idx].ToMap())
		}

		// Create a dataframe from events
		df = dataframe.New(data)
	} else {
		tableName = sourceRef.Table

		var exists bool
		df, exists = rc.Sources.Get(tableName)
		if !exists {
			return nil, fmt.Errorf("table %s not found in sources", tableName)
		}
	}

	if df == nil {
		return nil, fmt.Errorf("no dataframe found for source")
	}

	// Apply filters
	for _, selectCond := range sourceRef.SelectOn {
		var value any
		var err error
		operation := "="

		if selectCond.Value.Action != nil {
			action, err := rc.ResolveAction(ctx, *selectCond.Value.Action)
			if err != nil {
				return nil, err
			}

			value, err = rc.ResolveValue(ctx, action)
			if err != nil {
				return nil, err
			}

			if *selectCond.Value.Action.Operation == "IN" {
				operation = "in"
			}

		} else if selectCond.Value.Value != nil {
			value, err = rc.ResolveValue(ctx, *selectCond.Value.Value)
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
			rc.logger.WithIndent().Warningf(ctx, "Fields %v not found in source for table %s", missingFields, tableName)
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
			rc.logger.WithIndent().Warningf(ctx, "Field %s not found in source for table %s", *sourceRef.Field, tableName)
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
