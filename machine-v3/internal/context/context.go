package context

import (
	"context"
	"fmt"
	"math"
	"reflect"
	"strconv"
	"strings"
	"time"

	"github.com/minbzk/poc-machine-law/machine-v3/internal/logging"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/model"
)

var logger = logging.GetLogger("context")

// TypeSpec defines specifications for value types
type TypeSpec struct {
	Type      string  `json:"type,omitempty" yaml:"type,omitempty"`
	Unit      string  `json:"unit,omitempty" yaml:"unit,omitempty"`
	Precision *int    `json:"precision,omitempty" yaml:"precision,omitempty"`
	Min       float64 `json:"min,omitempty" yaml:"min,omitempty"`
	Max       float64 `json:"max,omitempty" yaml:"max,omitempty"`
}

// Enforce applies type specifications to a value
func (ts *TypeSpec) Enforce(value interface{}) interface{} {
	if ts.Type == "string" {
		return fmt.Sprintf("%v", value)
	}

	if value == nil {
		if ts.Type == "int" {
			return 0
		}
		if ts.Type == "float" {
			return 0.0
		}
		return value
	}

	// Convert to numeric if needed
	var floatVal float64
	switch v := value.(type) {
	case string:
		var err error
		floatVal, err = strconv.ParseFloat(v, 64)
		if err != nil {
			return value
		}
	case int:
		floatVal = float64(v)
	case int32:
		floatVal = float64(v)
	case int64:
		floatVal = float64(v)
	case float32:
		floatVal = float64(v)
	case float64:
		floatVal = v
	default:
		return value
	}

	// Apply min/max constraints
	if ts.Min != 0 {
		floatVal = math.Max(floatVal, ts.Min)
	}
	if ts.Max != 0 {
		floatVal = math.Min(floatVal, ts.Max)
	}

	// Apply precision
	if ts.Precision != nil {
		factor := math.Pow(10, float64(*ts.Precision))
		floatVal = math.Round(floatVal*factor) / factor
	}

	// Convert to int for cent units
	if ts.Unit == "eurocent" {
		return int(floatVal)
	}

	return floatVal
}

// ServiceProvider interface defines what a service provider needs to implement
type ServiceProvider interface {
	Evaluate(ctx context.Context, service, law string, parameters map[string]interface{}, referenceDate string,
		overwriteInput map[string]map[string]interface{}, requestedOutput string, approved bool) (*model.RuleResult, error)
}

// RuleContext holds context for rule evaluation
type RuleContext struct {
	Definitions     map[string]interface{}
	ServiceProvider ServiceProvider
	Parameters      map[string]interface{}
	PropertySpecs   map[string]map[string]interface{}
	OutputSpecs     map[string]TypeSpec
	Sources         map[string]model.DataFrame
	Local           map[string]interface{}
	AccessedPaths   map[string]struct{}
	ValuesCache     map[string]interface{}
	Path            []*model.PathNode
	OverwriteInput  map[string]map[string]interface{}
	Outputs         map[string]interface{}
	CalculationDate string
	ResolvedPaths   map[string]interface{}
	ServiceName     string
	Claims          map[string]*model.Claim
	Approved        bool
	MissingRequired bool
	ctx             context.Context
}

// NewRuleContext creates a new rule context
func NewRuleContext(ctx context.Context, definitions map[string]interface{}, serviceProvider ServiceProvider,
	parameters map[string]interface{}, propertySpecs map[string]map[string]interface{},
	outputSpecs map[string]TypeSpec, sources map[string]model.DataFrame, path []*model.PathNode,
	overwriteInput map[string]map[string]interface{}, calculationDate string,
	serviceName string, claims map[string]*model.Claim, approved bool) *RuleContext {

	if path == nil {
		path = make([]*model.PathNode, 0)
	}

	return &RuleContext{
		Definitions:     definitions,
		ServiceProvider: serviceProvider,
		Parameters:      parameters,
		PropertySpecs:   propertySpecs,
		OutputSpecs:     outputSpecs,
		Sources:         sources,
		Local:           make(map[string]interface{}),
		AccessedPaths:   make(map[string]struct{}),
		ValuesCache:     make(map[string]interface{}),
		Path:            path,
		OverwriteInput:  overwriteInput,
		Outputs:         make(map[string]interface{}),
		CalculationDate: calculationDate,
		ResolvedPaths:   make(map[string]interface{}),
		ServiceName:     serviceName,
		Claims:          claims,
		Approved:        approved,
		MissingRequired: false,
		ctx:             ctx,
	}
}

// TrackAccess tracks accessed data paths
func (rc *RuleContext) TrackAccess(path string) {
	rc.AccessedPaths[path] = struct{}{}
}

// AddToPath adds node to evaluation path
func (rc *RuleContext) AddToPath(node *model.PathNode) {
	if len(rc.Path) > 0 {
		rc.Path[len(rc.Path)-1].AddChild(node)
	}
	rc.Path = append(rc.Path, node)
}

// PopPath removes the last node from path
func (rc *RuleContext) PopPath() {
	if len(rc.Path) > 0 {
		rc.Path = rc.Path[:len(rc.Path)-1]
	}
}

// ResolveValue resolves a value from definitions, services, or sources
func (rc *RuleContext) ResolveValue(path interface{}) (interface{}, error) {
	value, err := rc.resolveValueInternal(path)
	if err != nil {
		return nil, err
	}

	if strPath, ok := path.(string); ok {
		rc.ResolvedPaths[strPath] = value
	}
	return value, nil
}

func (rc *RuleContext) resolveValueInternal(path interface{}) (interface{}, error) {
	node := &model.PathNode{
		Type:    "resolve",
		Name:    fmt.Sprintf("Resolving value: %v", path),
		Result:  nil,
		Details: map[string]interface{}{"path": path},
	}
	rc.AddToPath(node)

	defer rc.PopPath()

	logger.WithIndent().Debugf("Resolving %v", path)

	// If path is not a string or doesn't start with $, return it as is
	strPath, ok := path.(string)
	if !ok || !strings.HasPrefix(strPath, "$") {
		node.Result = path
		return path, nil
	}

	// Remove $ prefix
	strPath = strPath[1:]
	rc.TrackAccess(strPath)

	// Resolve dates first
	dateValue, err := rc.resolveDate(strPath)
	if err == nil && dateValue != nil {
		logger.WithIndent().Debugf("Resolved date $%s: %v", strPath, dateValue)
		node.Result = dateValue
		return dateValue, nil
	}

	// Handle paths with dots (nested access)
	if strings.Contains(strPath, ".") {
		parts := strings.SplitN(strPath, ".", 2)
		root, rest := parts[0], parts[1]

		rootValue, err := rc.ResolveValue("$" + root)
		if err != nil {
			return nil, err
		}

		if rootValue == nil {
			logger.WithIndent().Warningf("Value is nil, could not resolve value $%s: nil", strPath)
			node.Result = nil
			return nil, nil
		}

		// Navigate through the nested path
		pathParts := strings.Split(rest, ".")
		currentValue := rootValue

		for _, part := range pathParts {
			rValue := reflect.ValueOf(currentValue)

			if currentValue == nil {
				logger.WithIndent().Warningf("Value is nil, could not resolve nested path $%s.%s", root, rest)
				node.Result = nil
				return nil, nil
			}

			// Handle map
			if rValue.Kind() == reflect.Map {
				mapValue := rValue.MapIndex(reflect.ValueOf(part))
				if !mapValue.IsValid() {
					logger.WithIndent().Warningf("Key %s not found in map, could not resolve value $%s", part, strPath)
					node.Result = nil
					return nil, nil
				}
				currentValue = mapValue.Interface()
			} else if rValue.Kind() == reflect.Struct {
				// Handle struct
				field := rValue.FieldByName(part)
				if !field.IsValid() {
					logger.WithIndent().Warningf("Field %s not found in struct, could not resolve value $%s", part, strPath)
					node.Result = nil
					return nil, nil
				}
				currentValue = field.Interface()
			} else {
				logger.WithIndent().Warningf("Value is not map or struct, could not resolve value $%s", strPath)
				node.Result = nil
				return nil, nil
			}
		}

		logger.WithIndent().Debugf("Resolved value $%s: %v", strPath, currentValue)
		node.Result = currentValue
		return currentValue, nil
	}

	// Lookup from claims
	if rc.Claims != nil {
		if claim, exists := rc.Claims[strPath]; exists {
			value := claim.NewValue
			logger.WithIndent().Debugf("Resolving from CLAIM: %v", value)
			node.Result = value
			node.ResolveType = "CLAIM"

			// Add type information for claims
			if spec, exists := rc.PropertySpecs[strPath]; exists {
				if typeVal, exists := spec["type"]; exists {
					node.Details["type"] = typeVal
				}
				if typeSpec, exists := spec["type_spec"]; exists {
					node.Details["type_spec"] = typeSpec
				}
				node.Required = getBoolFromMap(spec, "required", false)
			}

			return value, nil
		}
	}

	// Check local scope
	if value, exists := rc.Local[strPath]; exists {
		logger.WithIndent().Debugf("Resolving from LOCAL: %v", value)
		node.Result = value
		node.ResolveType = "LOCAL"
		return value, nil
	}

	// Check definitions
	if value, exists := rc.Definitions[strPath]; exists {
		logger.WithIndent().Debugf("Resolving from DEFINITION: %v", value)
		node.Result = value
		node.ResolveType = "DEFINITION"
		return value, nil
	}

	// Check parameters
	if value, exists := rc.Parameters[strPath]; exists {
		logger.WithIndent().Debugf("Resolving from PARAMETERS: %v", value)
		node.Result = value
		node.ResolveType = "PARAMETER"
		return value, nil
	}

	// Check outputs
	if value, exists := rc.Outputs[strPath]; exists {
		logger.WithIndent().Debugf("Resolving from previous OUTPUT: %v", value)
		node.Result = value
		node.ResolveType = "OUTPUT"
		return value, nil
	}

	// Handle property specs
	if spec, exists := rc.PropertySpecs[strPath]; exists {
		// Check overwrite data
		if serviceRef, ok := spec["service_reference"].(map[string]interface{}); ok {
			serviceName, hasService := serviceRef["service"].(string)
			fieldName, hasField := serviceRef["field"].(string)

			if hasService && hasField && rc.OverwriteInput != nil {
				if serviceOverwrites, ok := rc.OverwriteInput[serviceName]; ok {
					if value, ok := serviceOverwrites[fieldName]; ok {
						logger.WithIndent().Debugf("Resolving from OVERWRITE: %v", value)
						node.Result = value
						node.ResolveType = "OVERWRITE"
						return value, nil
					}
				}
			}
		}

		// Check sources
		if sourceRef, ok := spec["source_reference"].(map[string]interface{}); ok {
			value, err := rc.resolveFromSource(sourceRef, spec)
			if err == nil && value != nil {
				node.Result = value
				node.ResolveType = "SOURCE"
				node.Required = getBoolFromMap(spec, "required", false)

				// Add type information to the node
				if typeVal, exists := spec["type"]; exists {
					node.Details["type"] = typeVal
				}
				if typeSpec, exists := spec["type_spec"]; exists {
					node.Details["type_spec"] = typeSpec
				}

				return value, nil
			}
		}

		// Check services
		if serviceRef, ok := spec["service_reference"].(map[string]interface{}); ok && rc.ServiceProvider != nil {
			value, err := rc.resolveFromService(strPath, serviceRef, spec)
			if err == nil {
				logger.WithIndent().Debugf("Result for $%s from %s field %s: %v",
					strPath, serviceRef["service"], serviceRef["field"], value)
				node.Result = value
				node.ResolveType = "SERVICE"
				node.Required = getBoolFromMap(spec, "required", false)

				// Add type information to the node
				if typeVal, exists := spec["type"]; exists {
					node.Details["type"] = typeVal
				}
				if typeSpec, exists := spec["type_spec"]; exists {
					node.Details["type_spec"] = typeSpec
				}

				return value, nil
			}
		}

		// Handle required fields
		node.Required = getBoolFromMap(spec, "required", false)
		if node.Required {
			rc.MissingRequired = true
		}

		// Add type information
		if typeVal, exists := spec["type"]; exists {
			node.Details["type"] = typeVal
		}
		if typeSpec, exists := spec["type_spec"]; exists {
			node.Details["type_spec"] = typeSpec
		}
	}

	logger.WithIndent().Warningf("Could not resolve value for %s", strPath)
	node.Result = nil
	node.ResolveType = "NONE"

	return nil, nil
}

// resolveDate handles special date-related paths
func (rc *RuleContext) resolveDate(path string) (interface{}, error) {
	if path == "calculation_date" {
		return rc.CalculationDate, nil
	}

	if path == "january_first" {
		calcDate, err := time.Parse("2006-01-02", rc.CalculationDate)
		if err != nil {
			return nil, err
		}
		januaryFirst := time.Date(calcDate.Year(), 1, 1, 0, 0, 0, 0, calcDate.Location())
		return januaryFirst.Format("2006-01-02"), nil
	}

	if path == "prev_january_first" {
		calcDate, err := time.Parse("2006-01-02", rc.CalculationDate)
		if err != nil {
			return nil, err
		}
		prevJanuaryFirst := time.Date(calcDate.Year()-1, 1, 1, 0, 0, 0, 0, calcDate.Location())
		return prevJanuaryFirst.Format("2006-01-02"), nil
	}

	if path == "year" {
		if len(rc.CalculationDate) >= 4 {
			return rc.CalculationDate[:4], nil
		}
	}

	return nil, fmt.Errorf("not a date path")
}

// resolveFromService resolves a value from a service
func (rc *RuleContext) resolveFromService(
	path string,
	serviceRef map[string]interface{},
	spec map[string]interface{}) (interface{}, error) {

	// Clone parameters
	parameters := make(map[string]interface{})
	for k, v := range rc.Parameters {
		parameters[k] = v
	}

	// Add service reference parameters
	if serviceParams, ok := serviceRef["parameters"].([]interface{}); ok {
		for _, paramObj := range serviceParams {
			if param, ok := paramObj.(map[string]interface{}); ok {
				name, hasName := param["name"].(string)
				reference, hasRef := param["reference"].(string)

				if hasName && hasRef {
					value, err := rc.ResolveValue(reference)
					if err != nil {
						return nil, err
					}
					parameters[name] = value
				}
			}
		}
	}

	// Get reference date
	referenceDate := rc.CalculationDate
	if temporal, ok := spec["temporal"].(map[string]interface{}); ok {
		if reference, ok := temporal["reference"].(string); ok {
			refDate, err := rc.ResolveValue(reference)
			if err != nil {
				return nil, err
			}
			if refDateStr, ok := refDate.(string); ok {
				referenceDate = refDateStr
			}
		}
	}

	// Check cache
	var cacheKey strings.Builder
	cacheKey.WriteString(path)
	cacheKey.WriteString("(")

	// Sort keys for consistency
	paramKeys := make([]string, 0, len(parameters))
	for k := range parameters {
		paramKeys = append(paramKeys, k)
	}

	// Stable sorting would be better but this works for simple keys
	for i, k := range paramKeys {
		if i > 0 {
			cacheKey.WriteString(",")
		}
		cacheKey.WriteString(fmt.Sprintf("%s:%v", k, parameters[k]))
	}
	cacheKey.WriteString(",")
	cacheKey.WriteString(referenceDate)
	cacheKey.WriteString(")")

	cacheKeyStr := cacheKey.String()
	if cachedVal, exists := rc.ValuesCache[cacheKeyStr]; exists {
		logger.WithIndent().Debugf("Resolving from CACHE with key '%s': %v", cacheKeyStr, cachedVal)
		return cachedVal, nil
	}

	// Create service evaluation node
	details := map[string]interface{}{
		"service":        serviceRef["service"],
		"law":            serviceRef["law"],
		"field":          serviceRef["field"],
		"reference_date": referenceDate,
		"parameters":     parameters,
		"path":           path,
	}

	// Copy type information from spec to details
	if typeVal, exists := spec["type"]; exists {
		details["type"] = typeVal
	}
	if typeSpec, exists := spec["type_spec"]; exists {
		details["type_spec"] = typeSpec
	}

	serviceNode := &model.PathNode{
		Type:    "service_evaluation",
		Name:    fmt.Sprintf("Service call: %s.%s", serviceRef["service"], serviceRef["law"]),
		Result:  nil,
		Details: details,
	}
	rc.AddToPath(serviceNode)
	defer rc.PopPath()

	service, hasService := serviceRef["service"].(string)
	law, hasLaw := serviceRef["law"].(string)
	field, hasField := serviceRef["field"].(string)

	if !hasService || !hasLaw || !hasField {
		return nil, fmt.Errorf("invalid service reference format")
	}

	result, err := rc.ServiceProvider.Evaluate(
		context.TODO(),
		service,
		law,
		parameters,
		referenceDate,
		rc.OverwriteInput,
		field,
		rc.Approved,
	)
	if err != nil {
		return nil, err
	}

	value := result.Output[field]
	rc.ValuesCache[cacheKeyStr] = value

	// Update the service node with the result and add child path
	serviceNode.Result = value
	if result.Path != nil {
		serviceNode.AddChild(result.Path)
	}

	rc.MissingRequired = rc.MissingRequired || result.MissingRequired

	return value, nil
}

// resolveFromSource resolves a value from a data source
func (rc *RuleContext) resolveFromSource(
	sourceRef map[string]interface{},
	spec map[string]interface{}) (interface{}, error) {

	var df model.DataFrame
	tableName := ""

	sourceType, hasSourceType := sourceRef["source_type"].(string)

	// Determine the DataFrame to use
	if hasSourceType {
		if sourceType == "laws" {
			tableName = "laws"
			// This would need the resolver, which we don't have direct access to here
			// We'd need to refactor to inject this dependency
			return nil, fmt.Errorf("laws source type not implemented")
		} else if sourceType == "events" {
			tableName = "events"
			// This would need the case manager, which we don't have direct access to here
			return nil, fmt.Errorf("events source type not implemented")
		}
	}

	// Try to find from provided sources
	if rc.Sources != nil {
		if table, ok := sourceRef["table"].(string); ok {
			tableName = table
			var exists bool
			df, exists = rc.Sources[table]
			if !exists {
				return nil, fmt.Errorf("table %s not found in sources", table)
			}
		}
	}

	if df == nil {
		return nil, fmt.Errorf("no dataframe found for source")
	}

	// Apply filters
	if selectOn, ok := sourceRef["select_on"].([]interface{}); ok {
		for _, selectCond := range selectOn {
			if cond, ok := selectCond.(map[string]interface{}); ok {
				nameVal, hasName := cond["name"].(string)
				valueRef, hasValue := cond["value"]

				if hasName && hasValue {
					value, err := rc.ResolveValue(valueRef)
					if err != nil {
						return nil, err
					}

					// Handle special operations
					if valueMap, isMap := value.(map[string]interface{}); isMap {
						if op, hasOp := valueMap["operation"].(string); hasOp && op == "IN" {
							if valuesRef, hasValues := valueMap["values"]; hasValues {
								allowedValues, err := rc.ResolveValue(valuesRef)
								if err != nil {
									return nil, err
								}
								df, err = df.Filter(nameVal, "in", allowedValues)
								if err != nil {
									return nil, err
								}
							}
						}
					} else {
						// Standard equality filter
						df, err = df.Filter(nameVal, "=", value)
						if err != nil {
							return nil, err
						}
					}
				}
			}
		}
	}

	// Get results according to requested fields
	var result interface{}

	if fields, ok := sourceRef["fields"].([]string); ok && len(fields) > 0 {
		// Check if all requested fields exist
		missingFields := []string{}
		for _, f := range fields {
			if !df.HasColumn(f) {
				missingFields = append(missingFields, f)
			}
		}

		if len(missingFields) > 0 {
			logger.WithIndent().Warningf("Fields %v not found in source for table %s", missingFields, tableName)
		}

		// Get existing fields
		existingFields := []string{}
		for _, f := range fields {
			if df.HasColumn(f) {
				existingFields = append(existingFields, f)
			}
		}

		result = df.Select(existingFields).ToRecords()
	} else if field, ok := sourceRef["field"].(string); ok {
		if !df.HasColumn(field) {
			logger.WithIndent().Warningf("Field %s not found in source for table %s", field, tableName)
			return nil, nil
		}
		result = df.GetColumnValues(field)
	} else {
		result = df.ToRecords()
	}

	if result == nil {
		return nil, nil
	}

	// Handle array results
	switch r := result.(type) {
	case []interface{}:
		if len(r) == 0 {
			return nil, nil
		}
		if len(r) == 1 {
			return r[0], nil
		}
	case []map[string]interface{}:
		if len(r) == 0 {
			return nil, nil
		}
		if len(r) == 1 {
			return r[0], nil
		}
	}

	return result, nil
}

// Helper function to safely get a boolean from a map
func getBoolFromMap(m map[string]interface{}, key string, defaultValue bool) bool {
	if val, exists := m[key]; exists {
		if boolVal, ok := val.(bool); ok {
			return boolVal
		}
	}
	return defaultValue
}
