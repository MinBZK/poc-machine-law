package engine

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	contexter "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/path"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/context/tracker"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/typespec"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/utils"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

// RulesEngine evaluates business rules
type RulesEngine struct {
	Spec            ruleresolver.RuleSpec
	ServiceName     string
	Law             string
	Requirements    []ruleresolver.Requirement
	Actions         []ruleresolver.Action
	ParameterSpecs  []ruleresolver.ParameterField
	PropertySpecs   map[string]ruleresolver.Field
	OutputSpecs     map[string]model.TypeSpec
	Definitions     map[string]any
	ServiceProvider service.ServiceProvider
	CaseManager     casemanager.CaseManager
	ClaimManager    claimmanager.ClaimManager
	referenceDate   time.Time
}

// NewRulesEngine creates a new rules engine instance
func NewRulesEngine(
	spec ruleresolver.RuleSpec,
	serviceProvider service.ServiceProvider,
	caseManager casemanager.CaseManager,
	claimManager claimmanager.ClaimManager,
	referenceDate string,
) *RulesEngine {
	t, err := time.Parse("2006-01-02", referenceDate)
	if err != nil {
		panic("invalid reference date")
	}

	return &RulesEngine{
		Spec:            spec,
		ServiceProvider: serviceProvider,
		CaseManager:     caseManager,
		ClaimManager:    claimManager,
		ServiceName:     spec.Service,
		Law:             spec.Law,
		Requirements:    spec.Requirements,
		Actions:         spec.Actions,
		ParameterSpecs:  spec.Properties.Parameters,
		PropertySpecs:   buildPropertySpecs(spec.Properties),
		OutputSpecs:     buildOutputSpecs(spec.Properties),
		Definitions:     spec.Properties.Definitions,
		referenceDate:   t,
	}
}

// buildPropertySpecs builds a mapping of property paths to their specifications
func buildPropertySpecs(properties ruleresolver.Properties) map[string]ruleresolver.Field {
	specs := make(map[string]ruleresolver.Field, len(properties.Input)+len(properties.Sources))

	// Add input properties
	for _, prop := range properties.Input {
		specs[prop.Name] = ruleresolver.Field{
			Input: &prop,
		}
	}

	// Add source properties
	for _, source := range properties.Sources {
		specs[source.Name] = ruleresolver.Field{
			Source: &source,
		}
	}

	return specs
}

// buildOutputSpecs builds a mapping of output names to their type specifications
func buildOutputSpecs(properties ruleresolver.Properties) map[string]model.TypeSpec {
	specs := make(map[string]model.TypeSpec)

	// Process output properties
	for _, output := range properties.Output {
		typeSpec := model.TypeSpec{
			Type: output.Type,
		}

		// Extract type_spec details
		if output.TypeSpec != nil {
			typeSpec.Unit = output.TypeSpec.Unit
			typeSpec.Precision = output.TypeSpec.Precision
			typeSpec.Min = output.TypeSpec.Min
			typeSpec.Max = output.TypeSpec.Max
		}

		specs[output.Name] = typeSpec
	}

	return specs
}

// enforceOutputType enforces type specifications on an output value
func (re *RulesEngine) enforceOutputType(ctx context.Context, name string, value any) any {
	logr := logger.FromContext(ctx)

	if spec, exists := re.OutputSpecs[name]; exists {
		result := typespec.Enforce(spec, value)

		if equal, _ := utils.Equal(result, value); !equal {
			logr.Debugf("Enforcing type spec changed value from: %v to %v", value, result)
		}

		return result
	}

	return value
}

// topologicalSort performs topological sort on dependencies
// Returns outputs in order they should be calculated
func topologicalSort(dependencies map[string]map[string]struct{}) ([]string, error) {
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

// isLowercase checks if a string contains only lowercase letters, digits, and underscores
// This is more efficient than strings.ToLower() as it avoids string allocation
func isLowercase(s string) bool {
	for _, r := range s {
		if r >= 'A' && r <= 'Z' {
			return false
		}
	}
	return true
}

// analyzeDependencies finds all outputs an action depends on
func analyzeDependencies(action ruleresolver.Action) map[string]struct{} {
	// Pre-allocate with larger capacity based on profiling data
	deps := make(map[string]struct{}, 0)

	var traverse func(any)
	var traverseActionValue func(ruleresolver.ActionValue)
	var traverseActionValues func(ruleresolver.ActionValues)
	var traverseCondition func(ruleresolver.Condition)
	var traverseAction func(ruleresolver.Action)

	resolveString := func(v string) {
		if len(v) <= 1 || v[0] != '$' {
			return
		}

		value := v[1:] // Remove $ prefix
		// If all lowercase, consider it an output reference
		if isLowercase(value) {
			deps[value] = struct{}{}
		}
	}

	traverseActionValue = func(v ruleresolver.ActionValue) {
		if v.Action != nil {
			traverseAction(*v.Action)
		}
		if v.Value != nil {
			traverse(*v.Value)
		}
	}

	traverseActionValues = func(v ruleresolver.ActionValues) {
		if v.ActionValues != nil {
			for _, value := range *v.ActionValues {
				traverseActionValue(value)
			}
		}
		if v.Value != nil {
			traverse(*v.Value)
		}
	}

	traverseCondition = func(v ruleresolver.Condition) {
		if v.Test != nil {
			traverseAction(*v.Test)
		}
		if v.Then != nil {
			traverseActionValue(*v.Then)
		}
		if v.Else != nil {
			traverseActionValue(*v.Else)
		}
	}

	traverseAction = func(v ruleresolver.Action) {
		if v.Value != nil {
			traverseActionValue(*v.Value)
		}
		if v.Operation != nil {
			resolveString(*v.Operation)
		}
		if v.Subject != nil {
			resolveString(*v.Subject)
		}
		if v.Unit != nil {
			resolveString(*v.Unit)
		}
		if v.Combine != nil {
			resolveString(*v.Combine)
		}
		if v.Values != nil {
			traverseActionValues(*v.Values)
		}
		// Use range directly for better performance
		for i := range v.Conditions {
			traverseCondition(v.Conditions[i])
		}
	}

	traverse = func(obj any) {
		switch v := obj.(type) {
		case string:
			resolveString(v)
		case map[string]any:
			for _, value := range v {
				traverse(value)
			}
		case []any:
			for _, item := range v {
				traverse(item)
			}
		case ruleresolver.ActionValue:
			traverseActionValue(v)
		case ruleresolver.ActionValues:
			traverseActionValues(v)
		case ruleresolver.Condition:
			traverseCondition(v)
		case ruleresolver.Action:
			traverseAction(v)
		}
	}

	traverseAction(action)
	return deps
}

// getRequiredActions gets all actions needed to compute requested output in dependency order
func getRequiredActions(requestedOutput string, actions []ruleresolver.Action) ([]ruleresolver.Action, error) {
	if requestedOutput == "" {
		return actions, nil
	}

	// Pre-allocate maps with better capacity estimates
	dependencies := make(map[string]map[string]struct{}, len(actions))
	actionByOutput := make(map[string]ruleresolver.Action, len(actions))

	// Build dependency graph with single pass
	for i := range actions { // Use index to avoid copying action structs
		actionByOutput[actions[i].Output] = actions[i]
		dependencies[actions[i].Output] = analyzeDependencies(actions[i])
	}

	// Use slice-based queue instead of map for better performance
	required := make(map[string]struct{})   // Estimate half the actions needed
	toProcessQueue := make([]string, 0, 16) // Pre-allocate queue
	toProcessQueue = append(toProcessQueue, requestedOutput)

	// Track processed to avoid duplicates
	processed := make(map[string]struct{}, len(actions)/2)

	for len(toProcessQueue) > 0 {
		// Pop from end for better performance
		output := toProcessQueue[len(toProcessQueue)-1]
		toProcessQueue = toProcessQueue[:len(toProcessQueue)-1]

		// Skip if already processed
		if _, alreadyProcessed := processed[output]; alreadyProcessed {
			continue
		}
		processed[output] = struct{}{}
		required[output] = struct{}{}

		// Add dependencies to processing queue
		if deps, ok := dependencies[output]; ok {
			for dep := range deps {
				if _, alreadyProcessed := processed[dep]; !alreadyProcessed {
					toProcessQueue = append(toProcessQueue, dep)
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

	orderedOutputs, err := topologicalSort(filteredDeps)
	if err != nil {
		return nil, err
	}

	// Return actions in dependency order
	var requiredActions []ruleresolver.Action
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
	parameters map[string]any,
	overwriteInput map[string]any,
	sources model.SourceDataFrame,
	referenceDate time.Time,
	effectiveDate time.Time,
	requestedOutput string,
	approved bool,
) (model.EvaluateResult, error) {
	logr := logger.FromContext(ctx).WithName("engine")

	// Check required parameters
	if re.ParameterSpecs != nil {
		for _, spec := range re.ParameterSpecs {
			if spec.Required != nil && *spec.Required {
				if _, exists := parameters[spec.Name]; !exists {
					logr.WithIndent().Warningf("Required parameter %s not found in %v", spec.Name, parameters)
				}
			}
		}
	}

	logr.Debugf("Evaluating rules for %s %s (%s %s)",
		re.ServiceName, re.Law, referenceDate.Format(time.DateOnly), requestedOutput)

	// Handle claims
	var claims map[string]model.Claim
	if bsn, ok := parameters["BSN"].(string); ok {
		claimsList, err := re.ClaimManager.GetClaimsByBSN(ctx, bsn, approved, true)
		if err != nil {
			logr.WithIndent().Warningf("Failed to get claims for BSN %s: %v", bsn, err)
		}

		// Convert claims list to map indexed by key
		claims = make(map[string]model.Claim, len(claimsList))
		for _, claim := range claimsList {
			claims[claim.Key] = claim
		}
	}

	// Create root node
	root := &model.PathNode{
		Type:   "root",
		Name:   "evaluation",
		Result: nil,
	}

	p := path.NewWith(root)
	ctx = path.WithPath(ctx, p)

	ctx = tracker.WithTracker(ctx, tracker.New())

	// Create context
	ruleCtx, err := contexter.NewRuleContext(
		re.Definitions,
		re.ServiceProvider,
		re.CaseManager,
		parameters,
		re.PropertySpecs,
		sources,
		overwriteInput,
		referenceDate,
		effectiveDate,
		claims,
		approved,
	)

	if err != nil {
		return model.EvaluateResult{}, fmt.Errorf("new rule context: %w", err)
	}

	// Check requirements
	requirementsNode := &model.PathNode{
		Type:   "requirements",
		Name:   "Check all requirements",
		Result: nil,
	}

	p.Add(requirementsNode)

	var requirementsMet bool

	if err := logr.IndentBlock(ctx, "", func(ctx context.Context) error {
		var err error
		requirementsMet, err = re.evaluateRequirements(ctx, re.Requirements, ruleCtx)
		requirementsNode.Result = requirementsMet
		return err
	}); err != nil {
		return model.EvaluateResult{}, err
	}

	p.Pop()

	outputValues := make(map[string]model.EvaluateActionResult)
	if requirementsMet {
		// Get required actions including dependencies in order
		requiredActions, err := getRequiredActions(requestedOutput, re.Actions)
		if err != nil {
			return model.EvaluateResult{}, err
		}

		for _, action := range requiredActions {
			outputDef, outputName, err := re.evaluateAction(ctx, action, ruleCtx, overwriteInput)
			if err != nil {
				return model.EvaluateResult{}, err
			}

			ruleCtx.OutputsResolver.Set(outputName, outputDef.Value)
			outputValues[outputName] = outputDef

			if ruleCtx.MissingRequired {
				logr.WithIndent().Warningf("Missing required values, breaking")
				break
			}
		}
	}

	if ruleCtx.MissingRequired {
		logr.WithIndent().Warningf("Missing required values, requirements not met, setting outputs to empty.")
		outputValues = make(map[string]model.EvaluateActionResult)
		requirementsMet = false
	}

	if len(outputValues) == 0 {
		logr.WithIndent().Warningf("No output values computed for %s %s", referenceDate.Format(time.DateOnly), requestedOutput)
	}

	return model.EvaluateResult{
		Input:           tracker.FromContext(ctx).ResolvedPaths(),
		Output:          outputValues,
		RequirementsMet: requirementsMet,
		Path:            root,
		MissingRequired: ruleCtx.MissingRequired,
	}, nil
}

// evaluateAction evaluates a single action and returns its output
func (re *RulesEngine) evaluateAction(
	ctx context.Context,
	action ruleresolver.Action,
	ruleCtx *contexter.RuleContext,
	overwriteInput map[string]any,
) (model.EvaluateActionResult, string, error) {
	logr := logger.FromContext(ctx)

	var result any

	var outputSpec *ruleresolver.OutputField
	err := logr.IndentBlock(ctx, fmt.Sprintf("Computing %s", action.Output), func(ctx context.Context) error {
		logr := logger.FromContext(ctx)

		actionNode := &model.PathNode{
			Type:   "action",
			Name:   fmt.Sprintf("Evaluate action for %s", action.Output),
			Result: nil,
		}

		ctx = path.WithPathNode(ctx, actionNode)
		defer path.FromContext(ctx).Pop()

		// Find output specification
		for _, output := range re.Spec.Properties.Output {
			if output.Name == action.Output {
				outputSpec = &output
				break
			}
		}

		// Check if we should use overwrite value
		if overwriteInput != nil {
			if val, ok := overwriteInput[action.Output]; ok {
				logr.WithIndent().Debugf("Resolving value %s/%s from OVERWRITE %v",
					re.ServiceName, action.Output, val)
				result = val
			}
		}

		// If no overwrite, evaluate the action
		if result == nil {
			if action.Operation != nil {
				var err error
				result, err = re.evaluateOperation(ctx, action, ruleCtx)
				if err != nil {
					return err
				}
			} else if action.Value != nil {
				var err error
				result, err = re.evaluateActionValue(ctx, ruleCtx, *action.Value)
				if err != nil {
					return err
				}
			} else {
				result = nil
			}
		}

		// Apply type enforcement
		result = re.enforceOutputType(ctx, action.Output, result)
		actionNode.Result = result

		return nil
	})
	if err != nil {
		return model.EvaluateActionResult{}, "", err
	}

	logr.Debugf("Result of %s: %v", action.Output, result)

	outputDef := model.EvaluateActionResult{
		Value: result,
		Type:  "unknown",
	}

	// Add metadata from output spec if available
	if outputSpec != nil {
		outputDef.Type = outputSpec.Type
		outputDef.Description = &outputSpec.Description
		outputDef.TypeSpec = outputSpec.TypeSpec
		outputDef.Temporal = outputSpec.Temporal
	}

	return outputDef, action.Output, nil
}

func (re *RulesEngine) evaluateRequirementAction(
	ctx context.Context,
	ruleCtx *contexter.RuleContext,
	r ruleresolver.ActionRequirement,
) (bool, error) {
	if r.Requirement != nil {
		res, err := re.evaluateRequirements(ctx, []ruleresolver.Requirement{*r.Requirement}, ruleCtx)
		if err != nil {
			return false, fmt.Errorf("evaluate requirements: %w", err)
		}

		return res, nil
	} else if r.Action != nil {
		res, err := re.evaluateOperation(ctx, *r.Action, ruleCtx)
		if err != nil {
			return false, fmt.Errorf("evaluate operation: %w", err)
		}

		var result bool
		switch v := res.(type) {
		case bool:
			result = v
		case int:
			result = v != 0
		case int64:
			result = v != 0
		case float64:
			result = v != 0
		default:
			result = res != nil
		}

		return result, nil
	}

	return false, fmt.Errorf("action requirement is missing action")
}

// evaluateRequirements evaluates all requirements
func (re *RulesEngine) evaluateRequirements(
	ctx context.Context,
	requirements []ruleresolver.Requirement,
	ruleCtx *contexter.RuleContext,
) (bool, error) {
	logr := logger.FromContext(ctx)

	if len(requirements) == 0 {
		logr.WithIndent().Debugf("No requirements found")
		return true, nil
	}

	for _, req := range requirements {
		var nodeName string
		if req.All != nil {
			nodeName = "Check ALL conditions"
		} else if req.Or != nil {
			nodeName = "Check OR conditions"
		} else {
			nodeName = "Test condition"
		}

		var result bool

		err := logr.IndentBlock(ctx, fmt.Sprintf("Requirements %+v", req), func(ctx context.Context) error {
			logr := logger.FromContext(ctx)

			node := &model.PathNode{
				Type:   "requirement",
				Name:   nodeName,
				Result: nil,
			}

			ctx = path.WithPathNode(ctx, node)
			defer path.FromContext(ctx).Pop()

			if req.All != nil {
				results := []bool{}

				for _, r := range *req.All {
					res, err := re.evaluateRequirementAction(ctx, ruleCtx, r)
					if err != nil {
						return err
					}

					results = append(results, res)

					if !res {
						logr.Debugf("False value found in an ALL, no need to compute the rest, breaking.")
						break
					}

					if ruleCtx.MissingRequired {
						logr.WithIndent().Warningf("Missing required values, breaking")
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

			} else if req.Or != nil {
				results := []bool{}

				for _, r := range *req.Or {
					res, err := re.evaluateRequirementAction(ctx, ruleCtx, r)
					if err != nil {
						return err
					}

					results = append(results, res)

					if res {
						logr.Debugf("True value found in an OR, no need to compute the rest, breaking.")
						break
					}

					if ruleCtx.MissingRequired {
						logr.WithIndent().Warningf("Missing required values, breaking")
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
			}

			node.Result = result
			return nil
		})
		if err != nil {
			return false, err
		}

		logr.WithIndent().Debugf("Requirement met: %v", result)

		if !result {
			return false, nil
		}
	}

	return true, nil
}

// evaluateIfOperation evaluates an IF operation
func (re *RulesEngine) evaluateIfOperation(
	ctx context.Context,
	operation ruleresolver.Action,
	ruleCtx *contexter.RuleContext,
) (any, error) {
	ifNode := &model.PathNode{
		Type:    "operation",
		Name:    "IF conditions",
		Result:  nil,
		Details: map[string]any{"condition_results": []any{}},
	}

	ctx = path.WithPathNode(ctx, ifNode)
	defer path.FromContext(ctx).Pop()

	var result any
	conditionResults := make([]any, 0)

	for i, condition := range operation.Conditions {
		conditionResult := map[string]any{
			"condition_index": i,
		}

		if condition.Test != nil {
			conditionResult["type"] = "test"

			testResult, err := re.evaluateOperation(ctx, *condition.Test, ruleCtx)
			if err != nil {
				return nil, err
			}

			conditionResult["test_result"] = testResult

			// Convert to boolean
			test := false
			switch v := testResult.(type) {
			case bool:
				test = v
			case int:
				test = v != 0
			case int64:
				test = v != 0
			case float64:
				test = v != 0
			default:
				test = testResult != nil
			}

			if test {
				thenVal, err := re.evaluateActionValue(ctx, ruleCtx, *condition.Then)
				if err != nil {
					return nil, err
				}

				result = thenVal
				conditionResult["then_value"] = result
				conditionResults = append(conditionResults, conditionResult)
				break
			}
		} else if condition.Else != nil {
			conditionResult["type"] = "else"

			val, err := re.evaluateActionValue(ctx, ruleCtx, *condition.Else)
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
	operation ruleresolver.Action,
	ruleCtx *contexter.RuleContext,
) (any, error) {
	logr := logger.FromContext(ctx)

	arrayData, err := re.evaluateValue(ctx, *operation.Subject, ruleCtx)
	if err != nil {
		return nil, err
	}

	if arrayData == nil {
		logr.WithIndent().Warningf("No data found to run FOREACH on")
		return re.evaluateAggregateOps(ctx, *operation.Subject, []any{}), nil
	}

	// Convert to array if not already
	var arrayItems []any
	switch v := arrayData.(type) {
	case []any:
		arrayItems = v
	case []map[string]any:
		arrayItems = make([]any, 0, len(v))
		for _, item := range v {
			arrayItems = append(arrayItems, item)
		}
	default:
		arrayItems = []any{arrayData}
	}

	var values []any
	if operation.Combine == nil {
		return nil, fmt.Errorf("combine operation not specified for FOREACH")
	}

	err = logr.IndentBlock(ctx, fmt.Sprintf("Foreach(%s)", *operation.Combine), func(ctx context.Context) error {
		logr := logger.FromContext(ctx)

		for _, item := range arrayItems {
			err := logr.IndentBlock(ctx, fmt.Sprintf("Item %v", item), func(ctx context.Context) error {
				// Create a new context with the item as local scope
				itemCtx := *ruleCtx // Shallow copy

				// Set local to the item
				switch v := item.(type) {
				case map[string]any:
					for k1, v1 := range v {
						itemCtx.LocalResolver.Set(k1, v1)
					}
				default:
					// If not a map, create a map with "value" key
					itemCtx.LocalResolver.Set("value", v)
				}

				var result any
				if operation.Value.Action != nil {
					// Evaluate the value
					result, err = re.evaluateOperation(ctx, *operation.Value.Action, &itemCtx)
					if err != nil {
						return err
					}
				} else {
					// Evaluate the value
					result, err = re.evaluateValue(ctx, operation.GetValue(), &itemCtx)
					if err != nil {
						return err
					}
				}

				// Add to values
				if resultArray, ok := result.([]any); ok {
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

		logr.WithIndent().Debugf("Foreach values: %v", values)
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Apply combine operation
	result := re.evaluateAggregateOps(ctx, *operation.Combine, values)
	logr.WithIndent().Debugf("Foreach result: %v", result)

	return result, nil
}

// Comparison operators
var comparisonOps = map[string]func(a, b any) (bool, error){
	"EQUALS":     utils.Equal,
	"NOT_EQUALS": utils.NotEqual,
	"GREATER_THAN": func(a, b any) (bool, error) {
		c, err := utils.Compare(a, b)
		if err != nil {
			return false, err
		}

		return c > 0, nil
	},
	"LESS_THAN": func(a, b any) (bool, error) {
		c, err := utils.Compare(a, b)
		if err != nil {
			return false, err
		}

		return c < 0, nil
	},
	"GREATER_OR_EQUAL": func(a, b any) (bool, error) {
		c, err := utils.Compare(a, b)
		if err != nil {
			return false, err
		}

		return c >= 0, nil
	},
	"LESS_OR_EQUAL": func(a, b any) (bool, error) {
		c, err := utils.Compare(a, b)
		if err != nil {
			return false, err
		}

		return c <= 0, nil
	},
}

// Helper to convert various types to float64
func convertToFloat(v any) (float64, error) {
	switch val := v.(type) {
	case int:
		return float64(val), nil
	case int32:
		return float64(val), nil
	case int64:
		return float64(val), nil
	case uint:
		return float64(val), nil
	case uint32:
		return float64(val), nil
	case uint64:
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
		if t, err := strconv.Atoi(val); err == nil {
			return float64(t), nil
		}

		return 0, fmt.Errorf("cannot convert string %s to number", val)
	case time.Time:
		return float64(val.Unix()), nil
	case bool:
		if val {
			return 1, nil
		}
		return 0, nil

	default:
		return 0, fmt.Errorf("cannot convert %v of type %T to number", v, v)
	}
}

// evaluateAggregateOps evaluates aggregate operations
func (re *RulesEngine) evaluateAggregateOps(ctx context.Context, op string, values []any) any {
	logr := logger.FromContext(ctx)

	// Filter out nil values
	filteredValues := make([]any, 0, len(values))
	for _, v := range values {
		if v != nil {
			filteredValues = append(filteredValues, v)
		}
	}

	if len(filteredValues) == 0 {
		logr.WithIndent().Warningf("No values found (or they were nil), returning 0 for %s(%v)", op, values)
		return 0
	} else if len(filteredValues) < len(values) {
		logr.WithIndent().Warningf("Dropped %d values because they were nil", len(values)-len(filteredValues))
	}

	var result any

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
					logr.Warningf("could not convert value to float: %w", err)
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
		logr.WithIndent().Warningf("Unknown aggregate operation: %s", op)
		result = 0.0
	}

	logr.Debugf("Compute %s(%v) = %v", op, filteredValues, result)
	return result
}

// evaluateComparison evaluates comparison operations
func (re *RulesEngine) evaluateComparison(ctx context.Context, op string, left, right any) (bool, error) {
	logr := logger.FromContext(ctx)

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
		logr.WithIndent().Warningf("Error computing %s(%v, %v): %v", op, left, right, err)
		return false, err
	}

	logr.Debugf("Compute %s(%v, %v) = %v", op, left, right, result)
	return result, nil
}

// evaluateDateOperation evaluates date-specific operations
func (re *RulesEngine) evaluateDateOperation(ctx context.Context, op string, values []any, unit string) (int, error) {
	logr := logger.FromContext(ctx)

	if op != "SUBTRACT_DATE" {
		return 0, fmt.Errorf("unknown date operation: %s", op)
	}

	if len(values) != 2 {
		logr.WithIndent().Warningf("Warning: SUBTRACT_DATE requires exactly 2 values")
		return 0, nil
	}

	// Convert to time.Time
	endDate, err := convertToTime(values[0])
	if err != nil {
		// enddate not specified take today
		endDate = re.referenceDate
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
		logr.WithIndent().Warningf("Warning: Unknown date unit %s", unit)
		result = 0
	}

	logr.Debugf("Compute %s(%v, %s) = %d", op, values, unit, result)
	return result, nil
}

// Helper function to convert various types to time.Time
func convertToTime(v any) (time.Time, error) {
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

		if v, err := strconv.Atoi(val); err == nil {
			return time.Unix(int64(v), 0), nil
		}

		return time.Time{}, fmt.Errorf("cannot convert string %s to date", val)
	default:
		return time.Time{}, fmt.Errorf("cannot convert %v of type %T to date", v, v)
	}
}

func (re *RulesEngine) evaluateOperation(
	ctx context.Context,
	operation ruleresolver.Action,
	ruleCtx *contexter.RuleContext,
) (any, error) {
	logr := logger.FromContext(ctx)

	// Direct value assignment - no operation needed
	if operation.Value != nil && operation.Operation == nil {
		node := &model.PathNode{
			Type:    "direct_value",
			Name:    "Direct value assignment",
			Result:  nil,
			Details: map[string]any{"raw_value": *operation.Value},
		}

		ctx = path.WithPathNode(ctx, node)
		defer path.FromContext(ctx).Pop()

		value, err := re.evaluateActionValue(ctx, ruleCtx, *operation.Value)
		if err != nil {
			return nil, err
		}

		node.Result = value
		return value, nil
	}

	if operation.Operation == nil || *operation.Operation == "" {
		logr.WithIndent().Warningf("Operation type is nil (or missing).")
		return nil, nil
	}

	// Handle operation
	node := &model.PathNode{
		Type:    "operation",
		Name:    fmt.Sprintf("Operation: %s", *operation.Operation),
		Result:  nil,
		Details: map[string]any{"operation_type": *operation.Operation},
	}

	ctx = path.WithPathNode(ctx, node)
	defer path.FromContext(ctx).Pop()

	var result any
	var err error

	switch *operation.Operation {
	case "IF":
		result, err = re.evaluateIfOperation(ctx, operation, ruleCtx)

	case "FOREACH":
		result, err = re.evaluateForeach(ctx, operation, ruleCtx)
		if err == nil {
			node.Details["raw_values"] = operation.GetValue()
			node.Details["arithmetic_type"] = *operation.Operation
		}

	case "IN", "NOT_IN":
		err = logr.IndentBlock(ctx, *operation.Operation, func(ctx context.Context) error {
			logr := logger.FromContext(ctx)

			subject, err := re.evaluateValue(ctx, *operation.Subject, ruleCtx)
			if err != nil {
				return err
			}

			allowedValues, err := re.evaluateActionValues(ctx, ruleCtx, *operation.Values)
			if err != nil {
				return err
			}

			// Convert allowedValues to a slice if it's not already
			var valuesList []any
			switch v := allowedValues.(type) {
			case []any:
				valuesList = v
			case map[any]any:
				valuesList = make([]any, 0, len(v))

				for key := range v {
					valuesList = append(valuesList, key)
				}
			case map[string]any:
				valuesList = make([]any, 0, len(v))

				for _, key := range v {
					valuesList = append(valuesList, key)
				}

			default:
				valuesList = []any{allowedValues}
			}

			// Check if subject is in the list
			found := false
			for _, val := range valuesList {
				if equal, _ := utils.Equal(subject, val); equal {
					found = true
					break
				}
			}

			if *operation.Operation == "NOT_IN" {
				found = !found
			}

			result = found
			node.Details["subject_value"] = subject
			node.Details["allowed_values"] = allowedValues

			logr.Debugf("Result %v %s %v: %v", subject, *operation.Operation, allowedValues, result)
			return nil
		})

	case "NOT_NULL":
		subject, err := re.evaluateValue(ctx, *operation.Subject, ruleCtx)
		if err != nil {
			return nil, err
		}

		result = subject != nil
		node.Details["subject_value"] = subject
	case "IS_NULL":
		subject, err := re.evaluateValue(ctx, *operation.Subject, ruleCtx)
		if err != nil {
			return nil, err
		}

		result = subject == nil
		node.Details["subject_value"] = subject
	case "AND":
		err = logr.IndentBlock(ctx, "AND", func(ctx context.Context) error {
			logr := logger.FromContext(ctx)

			values := []any{}

			for _, v := range *operation.Values.ActionValues {
				r, err := re.evaluateActionValue(ctx, ruleCtx, v)
				if err != nil {
					return err
				}

				values = append(values, r)

				// Short-circuit on first false value
				if !isTruthy(r) {
					logr.Debugf("False value found in an AND, no need to compute the rest, breaking.")
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
			logr.Debugf("Result %v AND: %v", values, result)
			return nil
		})

	case "OR":
		err = logr.IndentBlock(ctx, "OR", func(ctx context.Context) error {
			logr := logger.FromContext(ctx)

			values := []any{}
			for _, v := range *operation.Values.ActionValues {
				r, err := re.evaluateActionValue(ctx, ruleCtx, v)
				if err != nil {
					return err
				}

				values = append(values, r)

				// Short-circuit on first true value
				if isTruthy(r) {
					logr.Debugf("True value found in an OR, no need to compute the rest, breaking.")
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
			logr.Debugf("Result %v OR: %v", values, result)
			return nil
		})

	case "SUBTRACT_DATE":
		var values []any
		for _, v := range *operation.Values.ActionValues {
			val, err := re.evaluateActionValue(ctx, ruleCtx, v)
			if err != nil {
				return nil, err
			}
			values = append(values, val)
		}

		unit := "days" // Default unit
		if operation.Unit != nil {
			unit = *operation.Unit
		}

		intResult, err := re.evaluateDateOperation(ctx, *operation.Operation, values, unit)
		if err != nil {
			return nil, err
		}

		result = intResult
		node.Details["evaluated_values"] = values
		node.Details["unit"] = unit

	case "EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN", "GREATER_OR_EQUAL", "LESS_OR_EQUAL":
		// Get values to compare
		var subject, value any

		if operation.Subject != nil {
			subject, err = re.evaluateValue(ctx, *operation.Subject, ruleCtx)
			if err != nil {
				return nil, err
			}

			value, err = re.evaluateValue(ctx, operation.GetValue(), ruleCtx)
			if err != nil {
				return nil, err
			}
		} else if len(*operation.Values.ActionValues) >= 2 { // TODO verify that this should be greator or equal instead of equal
			values := make([]any, 0, len(*operation.Values.ActionValues))
			for _, v := range *operation.Values.ActionValues {
				value, err := re.evaluateActionValue(ctx, ruleCtx, v)
				if err != nil {
					return nil, err
				}

				values = append(values, value)
			}

			subject = values[0]
			value = values[1]
		} else {
			logr.WithIndent().Warningf("Comparison operation expects two values or subject/value")
			return nil, fmt.Errorf("invalid comparison format")
		}

		boolResult, err := re.evaluateComparison(ctx, *operation.Operation, subject, value)
		if err != nil {
			return nil, err
		}

		result = boolResult
		node.Details["subject_value"] = subject
		node.Details["comparison_value"] = value
		node.Details["comparison_type"] = *operation.Operation
	case "GET":
		subject, err := re.evaluateValue(ctx, *operation.Subject, ruleCtx)
		if err != nil {
			return nil, err
		}

		values, err := re.evaluateValue(ctx, operation.GetValue(), ruleCtx)
		if err != nil {
			return nil, err
		}

		switch t := values.(type) {
		case map[any]any:
			result = t[subject]
		default:
			return nil, fmt.Errorf("invalid type: %t", t)
		}

		node.Details["subject_value"] = subject
		node.Details["allowed_values"] = values
	case "MIN", "MAX", "ADD", "CONCAT", "MULTIPLY", "SUBTRACT", "DIVIDE":
		// This is probably an arithmetic operation
		values := make([]any, 0, len(*operation.Values.ActionValues))
		for _, v := range *operation.Values.ActionValues {
			value, err := re.evaluateActionValue(ctx, ruleCtx, v)
			if err != nil {
				return nil, err
			}

			values = append(values, value)
		}

		result = re.evaluateAggregateOps(ctx, *operation.Operation, values)

		node.Details["raw_values"] = operation.Values.GetValue()
		node.Details["evaluated_values"] = values
		node.Details["arithmetic_type"] = *operation.Operation
	default:
		result = nil
		node.Details["error"] = "Invalid operation format"
		logr.WithIndent().Errorf("Not matched to any operation %s", *operation.Operation)
	}

	node.Result = result
	return result, err
}

// Helper function to check if a value is truthy
func isTruthy(v any) bool {
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
	value any,
	ruleCtx *contexter.RuleContext,
) (any, error) {
	if value == nil {
		return value, nil
	}

	// For primitive types, return directly
	switch v := value.(type) {
	case int, int64, float64, bool, time.Time:
		return v, nil
	case []any:
		return re.evaluateValue(ctx, v[0], ruleCtx) // TODO this is a work in progress
	}

	// Otherwise, resolve from context
	return ruleCtx.ResolveValue(ctx, value)
}

func (re *RulesEngine) evaluateActionValue(
	ctx context.Context,
	ruleCtx *contexter.RuleContext,
	value ruleresolver.ActionValue,
) (any, error) {
	if value.Action != nil {
		return re.evaluateOperation(ctx, *value.Action, ruleCtx)
	}

	return re.evaluateValue(ctx, *value.Value, ruleCtx)
}

func (re *RulesEngine) evaluateActionValues(
	ctx context.Context,
	ruleCtx *contexter.RuleContext,
	values ruleresolver.ActionValues,
) (any, error) {
	if values.ActionValues != nil {
		return re.evaluateActionValue(ctx, ruleCtx, (*values.ActionValues)[0])
	}

	return re.evaluateValue(ctx, *values.Value, ruleCtx)
}
