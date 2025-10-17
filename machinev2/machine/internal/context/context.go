package context

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"time"
	"unicode"

	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/path"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/tracker"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver"
	claimresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/claim"
	definitionresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/definition"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/local"
	"github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/output"
	overwriteresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/overwrite"
	parameterresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/parameter"
	serviceresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/service"
	sourceresolver "github.com/minbzk/poc-machine-law/machinev2/machine/resolver/resolvers/source"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

type RuleContextData struct {
	ServiceProvider service.ServiceProvider
	Parameters      map[string]any
	PropertySpecs   map[string]ruleresolver.Field
	Sources         model.SourceDataFrame
	CalculationDate string
	Approved        bool
}

// RuleContext holds context for rule evaluation
type RuleContext struct {
	ServiceProvider service.ServiceProvider
	propertySpecs   map[string]ruleresolver.Field
	calculationDate string
	LocalResolver   *local.LocalResolver
	OutputsResolver *output.OutputsResolver
	Resolvers       []resolver.Resolver
	MissingRequired bool
}

// NewRuleContext creates a new rule context
func NewRuleContext(
	service string, definitions map[string]any, serviceProvider service.ServiceProvider,
	parameters map[string]any, propertySpecs map[string]ruleresolver.Field,
	sources model.SourceDataFrame,
	overwriteInput map[string]map[string]any, calculationDate string,
	claims map[string]model.Claim, approved bool) *RuleContext {

	localresolver := local.NewLocalResolver()
	outputresolver := output.NewOutputsResolver()

	rc := &RuleContext{
		propertySpecs:   propertySpecs,
		calculationDate: calculationDate,
		MissingRequired: false,
		LocalResolver:   localresolver,
		OutputsResolver: outputresolver,
	}

	rc.Resolvers = []resolver.Resolver{
		claimresolver.New(claims, propertySpecs),
		localresolver,
		definitionresolver.New(definitions),
		parameterresolver.New(parameters),
		outputresolver,
		overwriteresolver.New(service, propertySpecs, overwriteInput),
		sourceresolver.New(rc, serviceProvider, sources, propertySpecs),
		serviceresolver.New(rc, serviceProvider, propertySpecs, parameters, overwriteInput, calculationDate, approved),
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
	logr := logger.FromContext(ctx).WithName("context")

	var value any
	if err := logr.IndentBlock(ctx, fmt.Sprintf("Resolving path: %v", path), func(ctx context.Context) error {
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

	logger := logger.FromContext(ctx)

	// Resolve dates first
	dateValue, err := resolveDate(strPath, rc.calculationDate)
	if err == nil && dateValue != nil {
		logger.Debugf("Resolved date $%s: %v", strPath, dateValue)
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
			logger.Warningf("Value is nil, could not resolve value $%s: nil", strPath)
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
				logger.Warningf("Value is nil, could not resolve nested path $%s.%s", root, rest)
				node.Result = nil
				return nil, nil
			}

			// Handle map
			if rValue.Kind() == reflect.Map {
				mapValue := rValue.MapIndex(reflect.ValueOf(part))
				if !mapValue.IsValid() {
					logger.Warningf("Key %s not found in map, could not resolve value $%s", part, strPath)
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
						logger.Warningf("Field %s not found in struct, could not resolve value $%s", part, strPath)
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
				logger.Warningf("Value is not map or struct, could not resolve value $%s", strPath)
				node.Result = nil
				return nil, nil
			}
		}

		logger.Debugf("Resolved value $%s: %v", strPath, currentValue)
		node.Result = currentValue
		return currentValue, nil
	}

	for _, resolve := range rc.Resolvers {
		if resolved, ok := resolve.Resolve(ctx, strPath); ok {
			node.Result = resolved.Value
			node.ResolveType = resolve.ResolveType()
			node.Details = resolved.Details.ToMap()

			if resolved.MissingRequired != nil {
				rc.MissingRequired = rc.MissingRequired || *resolved.MissingRequired
			}

			logger.Debugf("Resolving from %s: %v", resolve.ResolveType(), resolved.Value)

			return resolved.Value, nil
		}
	}

	// Handle property specs
	if spec, exists := rc.propertySpecs[strPath]; exists {
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

	logger.Warningf("Could not resolve value for %s", strPath)
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
