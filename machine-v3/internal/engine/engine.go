package engine

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"time"

	contexter "github.com/minbzk/poc-machine-law/machine-v3/internal/context"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/logging"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/model"
)

var logger = logging.GetLogger("rules_engine")

// RulesEngine evaluates business rules
type RulesEngine struct {
	Spec            map[string]interface{}
	ServiceName     string
	Law             string
	Requirements    []interface{}
	Actions         []interface{}
	ParameterSpecs  map[string]interface{}
	PropertySpecs   map[string]map[string]interface{}
	OutputSpecs     map[string]contexter.TypeSpec
	Definitions     map[string]interface{}
	ServiceProvider contexter.ServiceProvider
}

// NewRulesEngine creates a new rules engine instance
func NewRulesEngine(spec map[string]interface{}, serviceProvider contexter.ServiceProvider) *RulesEngine {
	engine := &RulesEngine{
		Spec:            spec,
		ServiceProvider: serviceProvider,
		PropertySpecs:   make(map[string]map[string]interface{}),
		OutputSpecs:     make(map[string]contexter.TypeSpec),
	}

	// Extract main components
	if serviceName, ok := spec["service"].(string); ok {
		engine.ServiceName = serviceName
	}

	if law, ok := spec["law"].(string); ok {
		engine.Law = law
	}

	if requirements, ok := spec["requirements"].([]interface{}); ok {
		engine.Requirements = requirements
	}

	if actions, ok := spec["actions"].([]interface{}); ok {
		engine.Actions = actions
	}

	// Extract properties
	propertiesMap, _ := spec["properties"].(map[string]interface{})
	if propertiesMap != nil {
		// Get parameter specs
		engine.ParameterSpecs, _ = propertiesMap["parameters"].(map[string]interface{})

		// Build property specs
		engine.PropertySpecs = engine.buildPropertySpecs(propertiesMap)

		// Build output specs
		engine.OutputSpecs = engine.buildOutputSpecs(propertiesMap)

		// Get definitions
		engine.Definitions, _ = propertiesMap["definitions"].(map[string]interface{})
		if engine.Definitions == nil {
			engine.Definitions = make(map[string]interface{})
		}
	}

	return engine
}

// buildPropertySpecs builds a mapping of property paths to their specifications
func (re *RulesEngine) buildPropertySpecs(properties map[string]interface{}) map[string]map[string]interface{} {
	specs := make(map[string]map[string]interface{})

	// Add input properties
	if inputProps, ok := properties["input"].([]interface{}); ok {
		for _, prop := range inputProps {
			if propMap, ok := prop.(map[string]interface{}); ok {
				if name, ok := propMap["name"].(string); ok {
					specs[name] = propMap
				}
			}
		}
	}

	// Add source properties
	if sources, ok := properties["sources"].([]interface{}); ok {
		for _, source := range sources {
			if sourceMap, ok := source.(map[string]interface{}); ok {
				if name, ok := sourceMap["name"].(string); ok {
					specs[name] = sourceMap
				}
			}
		}
	}

	return specs
}

// buildOutputSpecs builds a mapping of output names to their type specifications
func (re *RulesEngine) buildOutputSpecs(properties map[string]interface{}) map[string]contexter.TypeSpec {
	specs := make(map[string]contexter.TypeSpec)

	// Process output properties
	if outputProps, ok := properties["output"].([]interface{}); ok {
		for _, output := range outputProps {
			if outputMap, ok := output.(map[string]interface{}); ok {
				if name, ok := outputMap["name"].(string); ok {
					var typeSpec contexter.TypeSpec

					// Extract type
					if typeVal, ok := outputMap["type"].(string); ok {
						typeSpec.Type = typeVal
					}

					// Extract type_spec details
					if typeSpecMap, ok := outputMap["type_spec"].(map[string]interface{}); ok {
						if unit, ok := typeSpecMap["unit"].(string); ok {
							typeSpec.Unit = unit
						}

						if precision, ok := typeSpecMap["precision"].(int); ok {
							typeSpec.Precision = &precision
						} else if precisionFloat, ok := typeSpecMap["precision"].(float64); ok {
							precision := int(precisionFloat)
							typeSpec.Precision = &precision
						}

						if min, ok := typeSpecMap["min"].(float64); ok {
							typeSpec.Min = min
						} else if minInt, ok := typeSpecMap["min"].(int); ok {
							typeSpec.Min = float64(minInt)
						}

						if max, ok := typeSpecMap["max"].(float64); ok {
							typeSpec.Max = max
						} else if maxInt, ok := typeSpecMap["max"].(int); ok {
							typeSpec.Max = float64(maxInt)
						}
					}

					specs[name] = typeSpec
				}
			}
		}
	}

	return specs
}

// enforceOutputType enforces type specifications on an output value
func (re *RulesEngine) enforceOutputType(name string, value interface{}) interface{} {
	if spec, exists := re.OutputSpecs[name]; exists {
		return spec.Enforce(value)
	}
	return value
}

// topologicalSort performs topological sort on dependencies
// Returns outputs in order they should be calculated
func (re *RulesEngine) topologicalSort(dependencies map[string]map[string]struct{}) ([]string, error) {
	// First create complete set of all nodes including leaf nodes
	allNodes := make(map[string]struct{})
	for node := range dependencies {
		allNodes[node] = struct{}{}
		for dep := range dependencies[node] {
			allNodes[dep] = struct{}{}
		}
	}

	// Initialize complete dependency map
	completeDeps := make(map[string]map[string]struct{})
	for node := range allNodes {
		completeDeps[node] = make(map[string]struct{})
	}

	// Copy existing dependencies
	for node, deps := range dependencies {
		for dep := range deps {
			completeDeps[node][dep] = struct{}{}
		}
	}

	// Build adjacency list (reverse dependencies)
	graph := make(map[string]map[string]struct{})
	for output, deps := range completeDeps {
		for dep := range deps {
			if graph[dep] == nil {
				graph[dep] = make(map[string]struct{})
			}
			graph[dep][output] = struct{}{}
		}
	}

	// Find nodes with no dependencies
	ready := []string{}
	for node, deps := range completeDeps {
		if len(deps) == 0 {
			ready = append(ready, node)
		}
	}

	// Process nodes
	sortedOutputs := []string{}

	for len(ready) > 0 {
		node := ready[0]
		ready = ready[1:]
		sortedOutputs = append(sortedOutputs, node)

		// Remove this node as dependency
		if dependents, ok := graph[node]; ok {
			for dependent := range dependents {
				delete(completeDeps[dependent], node)

				// If no more dependencies, add to ready
				if len(completeDeps[dependent]) == 0 {
					ready = append(ready, dependent)
				}

				delete(graph[node], dependent)
			}
		}
	}

	// Check for circular dependencies
	for _, deps := range completeDeps {
		if len(deps) > 0 {
			return nil, fmt.Errorf("circular dependency detected")
		}
	}

	return sortedOutputs, nil
}

// analyzeDependencies finds all outputs an action depends on
func (re *RulesEngine) analyzeDependencies(action interface{}) map[string]struct{} {
	deps := make(map[string]struct{})

	var traverse func(obj interface{})
	traverse = func(obj interface{}) {
		switch v := obj.(type) {
		case string:
			if strings.HasPrefix(v, "$") {
				value := v[1:] // Remove $ prefix
				// If all lowercase, consider it an output reference
				if strings.ToLower(value) == value {
					deps[value] = struct{}{}
				}
			}
		case map[string]interface{}:
			for _, value := range v {
				traverse(value)
			}
		case []interface{}:
			for _, item := range v {
				traverse(item)
			}
		}
	}

	traverse(action)
	return deps
}

// getRequiredActions gets all actions needed to compute requested output in dependency order
func (re *RulesEngine) getRequiredActions(requestedOutput string, actions []interface{}) ([]interface{}, error) {
	if requestedOutput == "" {
		return actions, nil
	}

	// Build dependency graph
	dependencies := make(map[string]map[string]struct{})
	actionByOutput := make(map[string]interface{})

	for _, action := range actions {
		if actionMap, ok := action.(map[string]interface{}); ok {
			if output, ok := actionMap["output"].(string); ok {
				actionByOutput[output] = action
				dependencies[output] = re.analyzeDependencies(action)
			}
		}
	}

	// Find all required outputs
	required := make(map[string]struct{})
	toProcess := map[string]struct{}{requestedOutput: {}}

	for len(toProcess) > 0 {
		// Pop an output from toProcess
		var output string
		for o := range toProcess {
			output = o
			break
		}
		delete(toProcess, output)

		required[output] = struct{}{}

		// Add dependencies to processing queue
		if deps, ok := dependencies[output]; ok {
			for dep := range deps {
				if _, alreadyRequired := required[dep]; !alreadyRequired {
					toProcess[dep] = struct{}{}
				}
			}
		}
	}

	// Get execution order via topological sort
	filteredDeps := make(map[string]map[string]struct{})
	for output, deps := range dependencies {
		if _, isRequired := required[output]; isRequired {
			filteredDeps[output] = deps
		}
	}

	orderedOutputs, err := re.topologicalSort(filteredDeps)
	if err != nil {
		return nil, err
	}

	// Return actions in dependency order
	var requiredActions []interface{}
	for _, output := range orderedOutputs {
		if action, ok := actionByOutput[output]; ok {
			requiredActions = append(requiredActions, action)
		}
	}

	return requiredActions, nil
}

// Evaluate evaluates rules using service context and sources
func (re *RulesEngine) Evaluate(
	ctx context.Context,
	parameters map[string]interface{},
	overwriteInput map[string]map[string]interface{},
	sources map[string]model.DataFrame,
	calculationDate string,
	requestedOutput string,
	approved bool,
) (map[string]interface{}, error) {
	// Check required parameters
	if re.ParameterSpecs != nil {
		for _, p := range re.ParameterSpecs {
			if paramMap, ok := p.(map[string]interface{}); ok {
				if required, ok := paramMap["required"].(bool); ok && required {
					if name, ok := paramMap["name"].(string); ok {
						if _, exists := parameters[name]; !exists {
							logger.WithIndent().Warningf("Required parameter %s not found in %v", name, parameters)
						}
					}
				}
			}
		}
	}

	logger.WithIndent().Debugf("Evaluating rules for %s %s (%s %s)",
		re.ServiceName, re.Law, calculationDate, requestedOutput)

	// Create root node
	root := &model.PathNode{
		Type:   "root",
		Name:   "evaluation",
		Result: nil,
	}

	// Handle claims
	var claims map[string]*model.Claim
	if bsn, ok := parameters["BSN"].(string); ok {
		// In a real implementation, we would get claims from the claim manager
		// For now, we'll just create an empty map
		claims = make(map[string]*model.Claim)
		claims["bsn"] = &model.Claim{
			BSN: bsn,
		}
	}

	// Create context
	ruleCtx := contexter.NewRuleContext(
		ctx,
		re.Definitions,
		re.ServiceProvider,
		parameters,
		re.PropertySpecs,
		re.OutputSpecs,
		sources,
		[]*model.PathNode{root},
		overwriteInput,
		calculationDate,
		re.ServiceName,
		claims,
		approved,
	)

	// Check requirements
	requirementsNode := &model.PathNode{
		Type:   "requirements",
		Name:   "Check all requirements",
		Result: nil,
	}
	ruleCtx.AddToPath(requirementsNode)

	var requirementsMet bool
	err := logging.IndentBlock(ctx, "", false, func(ctx context.Context) error {
		var err error
		requirementsMet, err = re.evaluateRequirements(ctx, re.Requirements, ruleCtx)
		requirementsNode.Result = requirementsMet
		return err
	})
	if err != nil {
		return nil, err
	}

	ruleCtx.PopPath()

	outputValues := make(map[string]interface{})
	if requirementsMet {
		// Get required actions including dependencies in order
		requiredActions, err := re.getRequiredActions(requestedOutput, re.Actions)
		if err != nil {
			return nil, err
		}

		for _, action := range requiredActions {
			outputDef, outputName, err := re.evaluateAction(ctx, action, ruleCtx)
			if err != nil {
				return nil, err
			}

			ruleCtx.Outputs[outputName] = outputDef["value"]
			outputValues[outputName] = outputDef

			if ruleCtx.MissingRequired {
				logger.WithIndent().Warningf("Missing required values, breaking")
				break
			}
		}
	}

	if ruleCtx.MissingRequired {
		logger.WithIndent().Warningf("Missing required values, requirements not met, setting outputs to empty.")
		outputValues = make(map[string]interface{})
		requirementsMet = false
	}

	if len(outputValues) == 0 {
		logger.WithIndent().Warningf("No output values computed for %s %s", calculationDate, requestedOutput)
	}

	result := map[string]interface{}{
		"input":            ruleCtx.ResolvedPaths,
		"output":           outputValues,
		"requirements_met": requirementsMet,
		"path":             root,
		"missing_required": ruleCtx.MissingRequired,
	}

	return result, nil
}

// evaluateAction evaluates a single action and returns its output
func (re *RulesEngine) evaluateAction(
	ctx context.Context,
	action interface{},
	ruleCtx *contexter.RuleContext,
) (map[string]interface{}, string, error) {
	var outputName string
	var err error

	actionMap, ok := action.(map[string]interface{})
	if !ok {
		return nil, "", fmt.Errorf("action is not a map")
	}

	outputName, ok = actionMap["output"].(string)
	if !ok {
		return nil, "", fmt.Errorf("action does not have an output field")
	}

	var result interface{}

	var outputSpec map[string]interface{}
	err = logging.IndentBlock(ctx, fmt.Sprintf("Computing %s", outputName), false, func(ctx context.Context) error {
		actionNode := &model.PathNode{
			Type:   "action",
			Name:   fmt.Sprintf("Evaluate action for %s", outputName),
			Result: nil,
		}
		ruleCtx.AddToPath(actionNode)
		defer ruleCtx.PopPath()

		// Find output specification
		if props, ok := re.Spec["properties"].(map[string]interface{}); ok {
			if outputs, ok := props["output"].([]interface{}); ok {
				for _, spec := range outputs {
					if specMap, ok := spec.(map[string]interface{}); ok {
						if name, ok := specMap["name"].(string); ok && name == outputName {
							outputSpec = specMap
							break
						}
					}
				}
			}
		}

		// Check if we should use overwrite value
		if ruleCtx.OverwriteInput != nil {
			if serviceMap, ok := ruleCtx.OverwriteInput[re.ServiceName]; ok {
				if val, ok := serviceMap[outputName]; ok {
					logger.WithIndent().Debugf("Resolving value %s/%s from OVERWRITE %v",
						re.ServiceName, outputName, val)
					result = val
				}
			}
		}

		// If no overwrite, evaluate the action
		if result == nil {
			if _, hasValue := actionMap["value"]; hasValue {
				var err error
				result, err = re.evaluateValue(ctx, actionMap["value"], ruleCtx)
				if err != nil {
					return err
				}
			} else {
				var err error
				result, err = re.evaluateOperation(ctx, actionMap, ruleCtx)
				if err != nil {
					return err
				}
			}
		}

		// Apply type enforcement
		result = re.enforceOutputType(outputName, result)
		actionNode.Result = result

		logger.WithIndent().Debugf("Result of %s: %v", outputName, result)
		return nil
	})
	if err != nil {
		return nil, "", err
	}

	// Build output with metadata
	outputDef := map[string]interface{}{
		"value": result,
		"type":  "unknown",
	}

	// Add metadata from output spec if available
	if outputSpec != nil {
		if typeVal, ok := outputSpec["type"].(string); ok {
			outputDef["type"] = typeVal
		}

		if desc, ok := outputSpec["description"].(string); ok {
			outputDef["description"] = desc
		}

		if typeSpec, ok := outputSpec["type_spec"].(map[string]interface{}); ok {
			outputDef["type_spec"] = typeSpec
		}

		if temporal, ok := outputSpec["temporal"].(map[string]interface{}); ok {
			outputDef["temporal"] = temporal
		}
	}

	return outputDef, outputName, nil
}

// evaluateRequirements evaluates all requirements
func (re *RulesEngine) evaluateRequirements(
	ctx context.Context,
	requirements []interface{},
	ruleCtx *contexter.RuleContext,
) (bool, error) {
	if len(requirements) == 0 {
		logger.WithIndent().Debugf("No requirements found")
		return true, nil
	}

	for _, req := range requirements {
		reqMap, ok := req.(map[string]interface{})
		if !ok {
			continue
		}

		var nodeName string
		if _, hasAll := reqMap["all"]; hasAll {
			nodeName = "Check ALL conditions"
		} else if _, hasOr := reqMap["or"]; hasOr {
			nodeName = "Check OR conditions"
		} else {
			nodeName = "Test condition"
		}

		var result bool
		var err error

		err = logging.IndentBlock(ctx, fmt.Sprintf("Requirements %v", req), false, func(ctx context.Context) error {
			node := &model.PathNode{
				Type:   "requirement",
				Name:   nodeName,
				Result: nil,
			}
			ruleCtx.AddToPath(node)
			defer ruleCtx.PopPath()

			if allConds, hasAll := reqMap["all"].([]interface{}); hasAll {
				results := []bool{}

				for _, r := range allConds {
					res, err := re.evaluateRequirements(ctx, []interface{}{r}, ruleCtx)
					if err != nil {
						return err
					}

					results = append(results, res)

					if !res {
						logger.WithIndent().Debugf("False value found in an ALL, no need to compute the rest, breaking.")
						break
					}

					if ruleCtx.MissingRequired {
						logger.WithIndent().Warningf("Missing required values, breaking")
						break
					}
				}

				result = true
				for _, r := range results {
					if !r {
						result = false
						break
					}
				}
			} else if orConds, hasOr := reqMap["or"].([]interface{}); hasOr {
				results := []bool{}

				for _, r := range orConds {
					res, err := re.evaluateRequirements(ctx, []interface{}{r}, ruleCtx)
					if err != nil {
						return err
					}

					results = append(results, res)

					if res {
						logger.WithIndent().Debugf("True value found in an OR, no need to compute the rest, breaking.")
						break
					}

					if ruleCtx.MissingRequired {
						logger.WithIndent().Warningf("Missing required values, breaking")
						break
					}
				}

				result = false
				for _, r := range results {
					if r {
						result = true
						break
					}
				}
			} else {
				var err error
				resultVal, err := re.evaluateOperation(ctx, reqMap, ruleCtx)
				if err != nil {
					return err
				}

				// Convert to boolean
				switch v := resultVal.(type) {
				case bool:
					result = v
				case int:
					result = v != 0
				case int64:
					result = v != 0
				case float64:
					result = v != 0
				default:
					result = resultVal != nil
				}
			}

			node.Result = result
			return nil
		})
		if err != nil {
			return false, err
		}

		logger.WithIndent().Debugf("Requirement met: %v", result)

		if !result {
			return false, nil
		}
	}

	return true, nil
}

// evaluateIfOperation evaluates an IF operation
func (re *RulesEngine) evaluateIfOperation(
	ctx context.Context,
	operation map[string]interface{},
	ruleCtx *contexter.RuleContext,
) (interface{}, error) {
	ifNode := &model.PathNode{
		Type:    "operation",
		Name:    "IF conditions",
		Result:  nil,
		Details: map[string]interface{}{"condition_results": []interface{}{}},
	}
	ruleCtx.AddToPath(ifNode)
	defer ruleCtx.PopPath()

	var result interface{}
	conditions, ok := operation["conditions"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("conditions not found or not an array")
	}

	conditionResults := make([]interface{}, 0)

	for i, condition := range conditions {
		condMap, ok := condition.(map[string]interface{})
		if !ok {
			continue
		}

		conditionResult := map[string]interface{}{
			"condition_index": i,
		}

		if test, hasTest := condMap["test"]; hasTest {
			conditionResult["type"] = "test"

			testResult, err := re.evaluateOperation(ctx, test.(map[string]interface{}), ruleCtx)
			if err != nil {
				return nil, err
			}

			conditionResult["test_result"] = testResult

			// Convert to boolean
			testBool := false
			switch v := testResult.(type) {
			case bool:
				testBool = v
			case int:
				testBool = v != 0
			case int64:
				testBool = v != 0
			case float64:
				testBool = v != 0
			default:
				testBool = testResult != nil
			}

			if testBool {
				thenVal, err := re.evaluateValue(ctx, condMap["then"], ruleCtx)
				if err != nil {
					return nil, err
				}

				result = thenVal
				conditionResult["then_value"] = result
				conditionResults = append(conditionResults, conditionResult)
				break
			}
		} else if elseVal, hasElse := condMap["else"]; hasElse {
			conditionResult["type"] = "else"

			val, err := re.evaluateValue(ctx, elseVal, ruleCtx)
			if err != nil {
				return nil, err
			}

			result = val
			conditionResult["else_value"] = result
			conditionResults = append(conditionResults, conditionResult)
			break
		}

		conditionResults = append(conditionResults, conditionResult)
	}

	ifNode.Details["condition_results"] = conditionResults
	ifNode.Result = result

	return result, nil
}

// evaluateForeach evaluates a FOREACH operation
func (re *RulesEngine) evaluateForeach(
	ctx context.Context,
	operation map[string]interface{},
	ruleCtx *contexter.RuleContext,
) (interface{}, error) {
	combine, ok := operation["combine"].(string)
	if !ok {
		return nil, fmt.Errorf("combine operation not specified for FOREACH")
	}

	arrayData, err := re.evaluateValue(ctx, operation["subject"], ruleCtx)
	if err != nil {
		return nil, err
	}

	if arrayData == nil {
		logger.WithIndent().Warningf("No data found to run FOREACH on")
		return re.evaluateAggregateOps(combine, []interface{}{}), nil
	}

	// Convert to array if not already
	var arrayItems []interface{}
	switch v := arrayData.(type) {
	case []interface{}:
		arrayItems = v
	case []map[string]interface{}:
		arrayItems = make([]interface{}, len(v))
		for i, item := range v {
			arrayItems[i] = item
		}
	default:
		arrayItems = []interface{}{arrayData}
	}

	var values []interface{}

	err = logging.IndentBlock(ctx, fmt.Sprintf("Foreach(%s)", combine), false, func(ctx context.Context) error {
		for _, item := range arrayItems {
			err := logging.IndentBlock(ctx, fmt.Sprintf("Item %v", item), false, func(ctx context.Context) error {
				// Create a new context with the item as local scope
				itemCtx := *ruleCtx // Shallow copy

				// Set local to the item
				switch v := item.(type) {
				case map[string]interface{}:
					itemCtx.Local = v
				default:
					// If not a map, create a map with "value" key
					itemCtx.Local = map[string]interface{}{"value": v}
				}

				// Get the value to evaluate
				var valueToEvaluate interface{}
				if valueArray, ok := operation["value"].([]interface{}); ok && len(valueArray) > 0 {
					valueToEvaluate = valueArray[0]
				} else {
					valueToEvaluate = operation["value"]
				}

				// Evaluate the value
				result, err := re.evaluateValue(ctx, valueToEvaluate, &itemCtx)
				if err != nil {
					return err
				}

				// Add to values
				if resultArray, ok := result.([]interface{}); ok {
					values = append(values, resultArray...)
				} else {
					values = append(values, result)
				}

				return nil
			})
			if err != nil {
				return err
			}
		}

		logger.WithIndent().Debugf("Foreach values: %v", values)
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Apply combine operation
	result := re.evaluateAggregateOps(combine, values)
	logger.WithIndent().Debugf("Foreach result: %v", result)

	return result, nil
}

// Comparison operators
var comparisonOps = map[string]func(a, b interface{}) (bool, error){
	"EQUALS": func(a, b interface{}) (bool, error) {
		return reflect.DeepEqual(a, b), nil
	},
	"NOT_EQUALS": func(a, b interface{}) (bool, error) {
		return !reflect.DeepEqual(a, b), nil
	},
	"GREATER_THAN": func(a, b interface{}) (bool, error) {
		return compareValues(a, b, func(x, y float64) bool { return x > y })
	},
	"LESS_THAN": func(a, b interface{}) (bool, error) {
		return compareValues(a, b, func(x, y float64) bool { return x < y })
	},
	"GREATER_OR_EQUAL": func(a, b interface{}) (bool, error) {
		return compareValues(a, b, func(x, y float64) bool { return x >= y })
	},
	"LESS_OR_EQUAL": func(a, b interface{}) (bool, error) {
		return compareValues(a, b, func(x, y float64) bool { return x <= y })
	},
}

// Helper function to compare values with a comparison function
func compareValues(a, b interface{}, cmp func(x, y float64) bool) (bool, error) {
	// Convert to comparable types
	var aFloat, bFloat float64
	var err error

	aFloat, err = convertToFloat(a)
	if err != nil {
		return false, err
	}

	bFloat, err = convertToFloat(b)
	if err != nil {
		return false, err
	}

	return cmp(aFloat, bFloat), nil
}

// Helper to convert various types to float64
func convertToFloat(v interface{}) (float64, error) {
	switch val := v.(type) {
	case int:
		return float64(val), nil
	case int32:
		return float64(val), nil
	case int64:
		return float64(val), nil
	case float32:
		return float64(val), nil
	case float64:
		return val, nil
	case string:
		// Try to parse as date first
		if t, err := time.Parse(time.RFC3339, val); err == nil {
			return float64(t.Unix()), nil
		}

		// Then try to parse as number
		if f, err := time.Parse("2006-01-02", val); err == nil {
			return float64(f.Unix()), nil
		}

		return 0, fmt.Errorf("cannot convert string %s to number", val)
	case time.Time:
		return float64(val.Unix()), nil
	default:
		return 0, fmt.Errorf("cannot convert %v of type %T to number", v, v)
	}
}

// evaluateAggregateOps evaluates aggregate operations
func (re *RulesEngine) evaluateAggregateOps(op string, values []interface{}) interface{} {
	// Filter out nil values
	filteredValues := make([]interface{}, 0, len(values))
	for _, v := range values {
		if v != nil {
			filteredValues = append(filteredValues, v)
		}
	}

	if len(filteredValues) == 0 {
		logger.WithIndent().Warningf("No values found (or they were nil), returning 0 for %s(%v)", op, values)
		return 0
	} else if len(filteredValues) < len(values) {
		logger.WithIndent().Warningf("Dropped %d values because they were nil", len(values)-len(filteredValues))
	}

	var result interface{}

	switch op {
	case "OR":
		result = false
		for _, v := range filteredValues {
			switch val := v.(type) {
			case bool:
				if val {
					result = true
					break
				}
			default:
				// Any non-nil, non-false value is considered true
				if val != nil && val != false {
					result = true
					break
				}
			}
		}

	case "AND":
		result = true
		for _, v := range filteredValues {
			switch val := v.(type) {
			case bool:
				if !val {
					result = false
					break
				}
			default:
				// Any nil or false value makes the result false
				if val == nil || val == false {
					result = false
					break
				}
			}
		}

	case "MIN":
		var minVal float64
		for i, v := range filteredValues {
			f, err := convertToFloat(v)
			if err != nil {
				continue
			}
			if i == 0 || f < minVal {
				minVal = f
			}
		}
		result = minVal

	case "MAX":
		var maxVal float64
		for i, v := range filteredValues {
			f, err := convertToFloat(v)
			if err != nil {
				continue
			}
			if i == 0 || f > maxVal {
				maxVal = f
			}
		}
		result = maxVal

	case "ADD":
		sum := 0.0
		for _, v := range filteredValues {
			f, err := convertToFloat(v)
			if err != nil {
				continue
			}
			sum += f
		}
		result = sum

	case "CONCAT":
		var builder strings.Builder
		for _, v := range filteredValues {
			builder.WriteString(fmt.Sprintf("%v", v))
		}
		result = builder.String()

	case "MULTIPLY":
		if len(filteredValues) == 0 {
			result = 0.0
		} else {
			prod := 1.0
			for _, v := range filteredValues {
				f, err := convertToFloat(v)
				if err != nil {
					continue
				}
				prod *= f
			}
			result = prod
		}

	case "SUBTRACT":
		if len(filteredValues) == 0 {
			result = 0.0
		} else {
			f, err := convertToFloat(filteredValues[0])
			if err != nil {
				result = 0.0
			} else {
				sum := f
				for i := 1; i < len(filteredValues); i++ {
					f, err := convertToFloat(filteredValues[i])
					if err != nil {
						continue
					}
					sum -= f
				}
				result = sum
			}
		}

	case "DIVIDE":
		if len(filteredValues) < 2 {
			result = 0.0
		} else {
			f, err := convertToFloat(filteredValues[0])
			if err != nil {
				result = 0.0
			} else {
				quotient := f
				for i := 1; i < len(filteredValues); i++ {
					f, err := convertToFloat(filteredValues[i])
					if err != nil || f == 0 {
						continue
					}
					quotient /= f
				}
				result = quotient
			}
		}

	default:
		logger.WithIndent().Warningf("Unknown aggregate operation: %s", op)
		result = 0.0
	}

	logger.WithIndent().Debugf("Compute %s(%v) = %v", op, filteredValues, result)
	return result
}

// evaluateComparison evaluates comparison operations
func (re *RulesEngine) evaluateComparison(op string, left, right interface{}) (bool, error) {
	// Handle date comparisons
	leftTime, leftIsTime := left.(time.Time)
	rightTime, rightIsTime := right.(time.Time)

	if leftIsTime && !rightIsTime {
		if rightStr, ok := right.(string); ok {
			var err error
			rightTime, err = time.Parse("2006-01-02", rightStr)
			if err != nil {
				rightTime, err = time.Parse(time.RFC3339, rightStr)
				if err != nil {
					return false, fmt.Errorf("cannot parse date: %v", right)
				}
			}
			rightIsTime = true
		}
	} else if rightIsTime && !leftIsTime {
		if leftStr, ok := left.(string); ok {
			var err error
			leftTime, err = time.Parse("2006-01-02", leftStr)
			if err != nil {
				leftTime, err = time.Parse(time.RFC3339, leftStr)
				if err != nil {
					return false, fmt.Errorf("cannot parse date: %v", left)
				}
			}
			leftIsTime = true
		}
	}

	// Use time comparison if both are dates
	if leftIsTime && rightIsTime {
		switch op {
		case "EQUALS":
			return leftTime.Equal(rightTime), nil
		case "NOT_EQUALS":
			return !leftTime.Equal(rightTime), nil
		case "GREATER_THAN":
			return leftTime.After(rightTime), nil
		case "LESS_THAN":
			return leftTime.Before(rightTime), nil
		case "GREATER_OR_EQUAL":
			return leftTime.After(rightTime) || leftTime.Equal(rightTime), nil
		case "LESS_OR_EQUAL":
			return leftTime.Before(rightTime) || leftTime.Equal(rightTime), nil
		}
	}

	// Use standard comparison for other types
	compFunc, ok := comparisonOps[op]
	if !ok {
		return false, fmt.Errorf("unknown comparison operation: %s", op)
	}

	result, err := compFunc(left, right)
	if err != nil {
		logger.WithIndent().Warningf("Error computing %s(%v, %v): %v", op, left, right, err)
		return false, err
	}

	logger.WithIndent().Debugf("Compute %s(%v, %v) = %v", op, left, right, result)
	return result, nil
}

// evaluateDateOperation evaluates date-specific operations
func (re *RulesEngine) evaluateDateOperation(op string, values []interface{}, unit string) (int, error) {
	if op != "SUBTRACT_DATE" {
		return 0, fmt.Errorf("unknown date operation: %s", op)
	}

	if len(values) != 2 {
		logger.WithIndent().Warningf("Warning: SUBTRACT_DATE requires exactly 2 values")
		return 0, nil
	}

	// Convert to time.Time
	endDate, err := convertToTime(values[0])
	if err != nil {
		return 0, err
	}

	startDate, err := convertToTime(values[1])
	if err != nil {
		return 0, err
	}

	// Calculate difference based on unit
	var result int

	switch unit {
	case "days":
		duration := endDate.Sub(startDate)
		result = int(duration.Hours() / 24)

	case "years":
		years := endDate.Year() - startDate.Year()

		// Adjust for incomplete years
		endMonth := endDate.Month()
		startMonth := startDate.Month()
		endDay := endDate.Day()
		startDay := startDate.Day()

		if endMonth < startMonth || (endMonth == startMonth && endDay < startDay) {
			years--
		}

		result = years

	case "months":
		yearDiff := endDate.Year() - startDate.Year()
		monthDiff := int(endDate.Month()) - int(startDate.Month())

		result = yearDiff*12 + monthDiff

	default:
		logger.WithIndent().Warningf("Warning: Unknown date unit %s", unit)
		result = 0
	}

	logger.WithIndent().Debugf("Compute %s(%v, %s) = %d", op, values, unit, result)
	return result, nil
}

// Helper function to convert various types to time.Time
func convertToTime(v interface{}) (time.Time, error) {
	switch val := v.(type) {
	case time.Time:
		return val, nil
	case string:
		// Try multiple date formats
		for _, format := range []string{"2006-01-02", time.RFC3339, "2006-01-02T15:04:05Z"} {
			if t, err := time.Parse(format, val); err == nil {
				return t, nil
			}
		}
		return time.Time{}, fmt.Errorf("cannot convert string %s to date", val)
	default:
		return time.Time{}, fmt.Errorf("cannot convert %v of type %T to date", v, v)
	}
}

// evaluateOperation evaluates an operation or condition
func (re *RulesEngine) evaluateOperation(
	ctx context.Context,
	operation interface{},
	ruleCtx *contexter.RuleContext,
) (interface{}, error) {
	// If operation is not a map, evaluate as value
	opMap, ok := operation.(map[string]interface{})
	if !ok {
		node := &model.PathNode{
			Type:    "value",
			Name:    "Direct value evaluation",
			Result:  nil,
			Details: map[string]interface{}{"raw_value": operation},
		}
		ruleCtx.AddToPath(node)
		defer ruleCtx.PopPath()

		value, err := re.evaluateValue(ctx, operation, ruleCtx)
		if err != nil {
			return nil, err
		}

		node.Result = value
		return value, nil
	}

	// Direct value assignment - no operation needed
	if val, hasValue := opMap["value"]; hasValue && opMap["operation"] == nil {
		node := &model.PathNode{
			Type:    "direct_value",
			Name:    "Direct value assignment",
			Result:  nil,
			Details: map[string]interface{}{"raw_value": val},
		}
		ruleCtx.AddToPath(node)
		defer ruleCtx.PopPath()

		value, err := re.evaluateValue(ctx, val, ruleCtx)
		if err != nil {
			return nil, err
		}

		node.Result = value
		return value, nil
	}

	// Handle operation
	opType, _ := opMap["operation"].(string)
	node := &model.PathNode{
		Type:    "operation",
		Name:    fmt.Sprintf("Operation: %s", opType),
		Result:  nil,
		Details: map[string]interface{}{"operation_type": opType},
	}
	ruleCtx.AddToPath(node)
	defer ruleCtx.PopPath()

	var result interface{}
	var err error

	if opType == "" {
		logger.WithIndent().Warningf("Operation type is nil (or missing).")
		return nil, nil
	}

	switch opType {
	case "IF":
		result, err = re.evaluateIfOperation(ctx, opMap, ruleCtx)

	case "FOREACH":
		result, err = re.evaluateForeach(ctx, opMap, ruleCtx)
		if err == nil {
			node.Details["raw_values"] = opMap["value"]
			node.Details["arithmetic_type"] = opType
		}

	case "IN", "NOT_IN":
		err = logging.IndentBlock(ctx, opType, false, func(ctx context.Context) error {
			subject, err := re.evaluateValue(ctx, opMap["subject"], ruleCtx)
			if err != nil {
				return err
			}

			allowedValues, err := re.evaluateValue(ctx, opMap["values"], ruleCtx)
			if err != nil {
				return err
			}

			// Convert allowedValues to a slice if it's not already
			var valuesList []interface{}
			switch v := allowedValues.(type) {
			case []interface{}:
				valuesList = v
			default:
				valuesList = []interface{}{allowedValues}
			}

			// Check if subject is in the list
			found := false
			for _, val := range valuesList {
				if reflect.DeepEqual(subject, val) {
					found = true
					break
				}
			}

			if opType == "NOT_IN" {
				found = !found
			}

			result = found
			node.Details["subject_value"] = subject
			node.Details["allowed_values"] = allowedValues

			logger.WithIndent().Debugf("Result %v %s %v: %v", subject, opType, allowedValues, result)
			return nil
		})

	case "NOT_NULL":
		subject, err := re.evaluateValue(ctx, opMap["subject"], ruleCtx)
		if err != nil {
			return nil, err
		}

		result = subject != nil
		node.Details["subject_value"] = subject

	case "AND":
		err = logging.IndentBlock(ctx, "AND", false, func(ctx context.Context) error {
			values := []interface{}{}
			vals, ok := opMap["values"].([]interface{})
			if !ok {
				return fmt.Errorf("AND operation requires values array")
			}

			for _, v := range vals {
				r, err := re.evaluateValue(ctx, v, ruleCtx)
				if err != nil {
					return err
				}

				values = append(values, r)

				// Short-circuit on first false value
				if !isTruthy(r) {
					logger.WithIndent().Debugf("False value found in an AND, no need to compute the rest, breaking.")
					break
				}
			}

			// Compute final result
			result = true
			for _, v := range values {
				if !isTruthy(v) {
					result = false
					break
				}
			}

			node.Details["evaluated_values"] = values
			logger.WithIndent().Debugf("Result %v AND: %v", values, result)
			return nil
		})

	case "OR":
		err = logging.IndentBlock(ctx, "OR", false, func(ctx context.Context) error {
			values := []interface{}{}
			vals, ok := opMap["values"].([]interface{})
			if !ok {
				return fmt.Errorf("OR operation requires values array")
			}

			for _, v := range vals {
				r, err := re.evaluateValue(ctx, v, ruleCtx)
				if err != nil {
					return err
				}

				values = append(values, r)

				// Short-circuit on first true value
				if isTruthy(r) {
					logger.WithIndent().Debugf("True value found in an OR, no need to compute the rest, breaking.")
					break
				}
			}

			// Compute final result
			result = false
			for _, v := range values {
				if isTruthy(v) {
					result = true
					break
				}
			}

			node.Details["evaluated_values"] = values
			logger.WithIndent().Debugf("Result %v OR: %v", values, result)
			return nil
		})

	case "SUBTRACT_DATE":
		var values []interface{}
		if vals, ok := opMap["values"].([]interface{}); ok {
			for _, v := range vals {
				val, err := re.evaluateValue(ctx, v, ruleCtx)
				if err != nil {
					return nil, err
				}
				values = append(values, val)
			}
		}

		unit, _ := opMap["unit"].(string)
		if unit == "" {
			unit = "days" // Default unit
		}

		intResult, err := re.evaluateDateOperation(opType, values, unit)
		if err != nil {
			return nil, err
		}

		result = intResult
		node.Details["evaluated_values"] = values
		node.Details["unit"] = unit

	case "EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN", "GREATER_OR_EQUAL", "LESS_OR_EQUAL":
		// Get values to compare
		var subject, value interface{}

		if subj, hasSubject := opMap["subject"]; hasSubject {
			subject, err = re.evaluateValue(ctx, subj, ruleCtx)
			if err != nil {
				return nil, err
			}

			value, err = re.evaluateValue(ctx, opMap["value"], ruleCtx)
			if err != nil {
				return nil, err
			}
		} else if vals, hasValues := opMap["values"].([]interface{}); hasValues && len(vals) >= 2 {
			values := make([]interface{}, len(vals))
			for i, v := range vals {
				values[i], err = re.evaluateValue(ctx, v, ruleCtx)
				if err != nil {
					return nil, err
				}
			}

			subject = values[0]
			value = values[1]
		} else {
			logger.WithIndent().Warningf("Comparison operation expects two values or subject/value")
			return nil, fmt.Errorf("invalid comparison format")
		}

		boolResult, err := re.evaluateComparison(opType, subject, value)
		if err != nil {
			return nil, err
		}

		result = boolResult
		node.Details["subject_value"] = subject
		node.Details["comparison_value"] = value
		node.Details["comparison_type"] = opType

	default:
		// Check if it's an aggregate operation
		if vals, hasValues := opMap["values"].([]interface{}); hasValues {
			// This is probably an arithmetic operation
			values := make([]interface{}, len(vals))
			for i, v := range vals {
				values[i], err = re.evaluateValue(ctx, v, ruleCtx)
				if err != nil {
					return nil, err
				}
			}

			result = re.evaluateAggregateOps(opType, values)
			node.Details["raw_values"] = opMap["values"]
			node.Details["evaluated_values"] = values
			node.Details["arithmetic_type"] = opType
		} else {
			result = nil
			node.Details["error"] = "Invalid operation format"
			logger.WithIndent().Warningf("Not matched to any operation %s", opType)
		}
	}

	node.Result = result
	return result, err
}

// Helper function to check if a value is truthy
func isTruthy(v interface{}) bool {
	if v == nil {
		return false
	}

	switch val := v.(type) {
	case bool:
		return val
	case int:
		return val != 0
	case int64:
		return val != 0
	case float64:
		return val != 0
	case string:
		return val != ""
	default:
		return true // Non-nil objects are truthy
	}
}

// evaluateValue evaluates a value which might be a number, operation, or reference
func (re *RulesEngine) evaluateValue(
	ctx context.Context,
	value interface{},
	ruleCtx *contexter.RuleContext,
) (interface{}, error) {
	// For primitive types, return directly
	switch v := value.(type) {
	case int, int64, float64, bool:
		return v, nil
	case time.Time:
		return v, nil
	case map[string]interface{}:
		// todo why do we need this
		if _, hasOp := v["operation"]; hasOp {
			return re.evaluateOperation(ctx, v, ruleCtx)
		}
	}

	// Otherwise, resolve from context
	return ruleCtx.ResolveValue(value)
}
