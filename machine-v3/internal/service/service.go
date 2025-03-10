package service

import (
	"context"
	"fmt"
	"strings"
	"sync"

	"github.com/minbzk/poc-machine-law/machine-v3/internal/engine"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/logging"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/model"
	"github.com/minbzk/poc-machine-law/machine-v3/internal/utils"
)

var logger = logging.GetLogger("service")

// RuleService interface for executing business rules for a specific service
type RuleService struct {
	ServiceName      string
	Services         *Services
	Resolver         *utils.RuleResolver
	engines          map[string]map[string]*engine.RulesEngine
	SourceDataFrames map[string]model.DataFrame
	mu               sync.RWMutex
}

// NewRuleService creates a new rule service instance
func NewRuleService(serviceName string, services *Services) *RuleService {
	return &RuleService{
		ServiceName:      serviceName,
		Services:         services,
		Resolver:         utils.NewRuleResolver(),
		engines:          make(map[string]map[string]*engine.RulesEngine),
		SourceDataFrames: make(map[string]model.DataFrame),
	}
}

// getEngine gets or creates a RulesEngine instance for given law and date
func (rs *RuleService) getEngine(law, referenceDate string) (*engine.RulesEngine, error) {
	rs.mu.Lock()
	defer rs.mu.Unlock()

	// Check if engine already exists
	if lawEngines, ok := rs.engines[law]; ok {
		if engine, ok := lawEngines[referenceDate]; ok {
			return engine, nil
		}
	} else {
		rs.engines[law] = make(map[string]*engine.RulesEngine)
	}

	// Create new engine
	spec, err := rs.Resolver.GetRuleSpec(law, referenceDate, rs.ServiceName)
	if err != nil {
		return nil, err
	}

	if service, ok := spec["service"].(string); !ok || service != rs.ServiceName {
		return nil, fmt.Errorf(
			"rule spec service '%s' does not match service '%s'",
			service, rs.ServiceName,
		)
	}

	ruleEngine := engine.NewRulesEngine(spec, rs.Services)
	rs.engines[law][referenceDate] = ruleEngine

	return ruleEngine, nil
}

// Evaluate evaluates rules for given law and reference date
func (rs *RuleService) Evaluate(
	ctx context.Context,
	law string,
	referenceDate string,
	parameters map[string]interface{},
	overwriteInput map[string]map[string]interface{},
	requestedOutput string,
	approved bool,
) (*model.RuleResult, error) {
	ruleEngine, err := rs.getEngine(law, referenceDate)
	if err != nil {
		return nil, err
	}

	result, err := ruleEngine.Evaluate(
		ctx,
		parameters,
		overwriteInput,
		rs.SourceDataFrames,
		referenceDate,
		requestedOutput,
		approved,
	)
	if err != nil {
		return nil, err
	}

	return model.NewRuleResult(result, fmt.Sprintf("%v", ruleEngine.Spec["uuid"])), nil
}

// GetRuleInfo gets metadata about the rule that would be applied for given law and date
func (rs *RuleService) GetRuleInfo(law, referenceDate string) map[string]interface{} {
	rule, err := rs.Resolver.FindRule(law, referenceDate, rs.ServiceName)
	if err != nil {
		return nil
	}

	return map[string]interface{}{
		"uuid":       rule.UUID,
		"name":       rule.Name,
		"valid_from": rule.ValidFrom.Format("2006-01-02"),
	}
}

// SetSourceDataFrame sets a source DataFrame
func (rs *RuleService) SetSourceDataFrame(table string, df model.DataFrame) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	rs.SourceDataFrames[table] = df
}

// Services is the main service provider for rule evaluation
type Services struct {
	Resolver          *utils.RuleResolver
	services          map[string]*RuleService
	RootReferenceDate string
	CaseManager       *CaseManager
	ClaimManager      *ClaimManager
	mu                sync.RWMutex
}

// NewServices creates a new services instance
func NewServices(referenceDate string) *Services {
	s := &Services{
		Resolver:          utils.NewRuleResolver(),
		services:          make(map[string]*RuleService),
		RootReferenceDate: referenceDate,
	}

	// Initialize services
	for service := range s.Resolver.GetServiceLaws() {
		s.services[service] = NewRuleService(service, s)
	}

	// Create managers
	s.CaseManager = NewCaseManager(s)
	s.ClaimManager = NewClaimManager(s)
	s.ClaimManager.CaseManager = s.CaseManager

	return s
}

// GetDiscoverableServiceLaws returns discoverable services and laws
func (s *Services) GetDiscoverableServiceLaws() map[string][]string {
	return s.Resolver.GetDiscoverableServiceLaws("CITIZEN")
}

// SetSourceDataFrame sets a source DataFrame for a service
func (s *Services) SetSourceDataFrame(service, table string, df model.DataFrame) {
	if srv, ok := s.services[service]; ok {
		srv.SetSourceDataFrame(table, df)
	}
}

// Evaluate evaluates rules for a specific service, law, and context
func (s *Services) Evaluate(
	ctx context.Context,
	service string,
	law string,
	parameters map[string]interface{},
	referenceDate string,
	overwriteInput map[string]map[string]interface{},
	requestedOutput string,
	approved bool,
) (*model.RuleResult, error) {
	s.mu.RLock()
	svc, ok := s.services[service]
	s.mu.RUnlock()

	if !ok {
		return nil, fmt.Errorf("service not found: %s", service)
	}

	if referenceDate == "" {
		referenceDate = s.RootReferenceDate
	}

	var result *model.RuleResult
	var err error

	err = logging.IndentBlock(
		ctx,
		fmt.Sprintf("%s: %s (%s %v %s)", service, law, referenceDate, parameters, requestedOutput),
		true,
		func(ctx context.Context) error {
			result, err = svc.Evaluate(
				ctx,
				law,
				referenceDate,
				parameters,
				overwriteInput,
				requestedOutput,
				approved,
			)
			return err
		},
	)

	return result, err
}

// ExtractValueTree extracts a flattened value tree from a path node
func (s *Services) ExtractValueTree(root *model.PathNode) map[string]interface{} {
	flattened := make(map[string]interface{})
	stack := []struct {
		node          *model.PathNode
		serviceParent map[string]interface{}
	}{
		{
			node:          root,
			serviceParent: nil,
		},
	}

	for len(stack) > 0 {
		// Pop from stack
		current := stack[len(stack)-1]
		stack = stack[:len(stack)-1]

		node := current.node
		serviceParent := current.serviceParent

		if node == nil {
			continue
		}

		// Handle path in details
		var path string
		if pathDetail, ok := node.Details["path"]; ok {
			if pathStr, ok := pathDetail.(string); ok && pathStr != "" {
				if len(pathStr) > 0 && pathStr[0] == '$' {
					path = pathStr[1:] // Remove $ prefix
				} else {
					path = pathStr
				}
			}
		}

		// Handle resolve nodes
		if node.Type == "resolve" &&
			(node.ResolveType == "SERVICE" || node.ResolveType == "SOURCE" ||
				node.ResolveType == "CLAIM" || node.ResolveType == "NONE") &&
			path != "" {
			resolveEntry := map[string]interface{}{
				"result":   node.Result,
				"required": node.Required,
				"details":  node.Details,
			}

			if serviceParent != nil {
				children, hasChildren := serviceParent["children"].(map[string]interface{})
				if !hasChildren {
					children = make(map[string]interface{})
					serviceParent["children"] = children
				}

				if _, exists := children[path]; !exists {
					children[path] = resolveEntry
				}
			} else if _, exists := flattened[path]; !exists {
				flattened[path] = resolveEntry
			}
		}

		// Handle service_evaluation nodes
		if node.Type == "service_evaluation" && path != "" {
			serviceEntry := map[string]interface{}{
				"result":   node.Result,
				"required": node.Required,
				"service":  node.Details["service"],
				"law":      node.Details["law"],
				"children": make(map[string]interface{}),
				"details":  node.Details,
			}

			if serviceParent != nil {
				children, hasChildren := serviceParent["children"].(map[string]interface{})
				if !hasChildren {
					children = make(map[string]interface{})
					serviceParent["children"] = children
				}
				children[path] = serviceEntry
			} else {
				flattened[path] = serviceEntry
			}

			// Process children with this service_evaluation as parent
			for i := len(node.Children) - 1; i >= 0; i-- {
				stack = append(stack, struct {
					node          *model.PathNode
					serviceParent map[string]interface{}
				}{node: node.Children[i], serviceParent: serviceEntry})
			}
			continue
		}

		// Add children to the stack for further processing
		for i := len(node.Children) - 1; i >= 0; i-- {
			stack = append(stack, struct {
				node          *model.PathNode
				serviceParent map[string]interface{}
			}{node: node.Children[i], serviceParent: serviceParent})
		}
	}

	return flattened
}

// ApplyRules applies rules in response to events
func (s *Services) ApplyRules(event *model.Event) error {
	for _, rule := range s.Resolver.Rules {
		applies, ok := rule.Properties["applies"].([]interface{})
		if !ok {
			continue
		}

		for _, applyObj := range applies {
			apply, ok := applyObj.(map[string]interface{})
			if !ok {
				continue
			}

			if s.matchesEvent(event, apply) {
				aggregateID := event.CaseID
				aggregate, err := s.CaseManager.GetCaseByID(aggregateID)
				if err != nil {
					return err
				}

				parameters := map[string]interface{}{
					apply["name"].(string): aggregate,
				}

				ctx := context.Background()
				result, err := s.Evaluate(
					ctx,
					rule.Service,
					rule.Law,
					parameters,
					s.RootReferenceDate,
					nil,
					"",
					true,
				)
				if err != nil {
					return err
				}

				// Apply updates back to aggregate
				updates, ok := apply["update"].([]interface{})
				if !ok {
					continue
				}

				for _, updateObj := range updates {
					update, ok := updateObj.(map[string]interface{})
					if !ok {
						continue
					}

					mappings, ok := update["mapping"].(map[string]interface{})
					if !ok {
						continue
					}

					// Convert values
					convertedMappings := make(map[string]interface{})
					for name, valueRef := range mappings {
						if valueStr, ok := valueRef.(string); ok && len(valueStr) > 0 && valueStr[0] == '$' {
							// Strip $ from value
							outputName := valueStr[1:]
							convertedMappings[name] = result.Output[outputName]
						}
					}

					// Apply method
					method, ok := update["method"].(string)
					if !ok {
						continue
					}

					// Call method on case manager
					switch method {
					case "determine_objection_status":
						var possible *bool
						var objectionPeriod, decisionPeriod, extensionPeriod *int
						notPossibleReason := ""

						if p, ok := convertedMappings["possible"].(bool); ok {
							possible = &p
						}
						if r, ok := convertedMappings["not_possible_reason"].(string); ok {
							notPossibleReason = r
						}
						if p, ok := convertedMappings["objection_period"].(int); ok {
							objectionPeriod = &p
						}
						if p, ok := convertedMappings["decision_period"].(int); ok {
							decisionPeriod = &p
						}
						if p, ok := convertedMappings["extension_period"].(int); ok {
							extensionPeriod = &p
						}

						err = s.CaseManager.DetermineObjectionStatus(
							aggregateID,
							possible,
							notPossibleReason,
							objectionPeriod,
							decisionPeriod,
							extensionPeriod,
						)
						if err != nil {
							return err
						}

					case "determine_objection_admissibility":
						var admissible *bool
						if a, ok := convertedMappings["admissible"].(bool); ok {
							admissible = &a
						}

						err = s.CaseManager.DetermineObjectionAdmissibility(aggregateID, admissible)
						if err != nil {
							return err
						}

					case "determine_appeal_status":
						var possible, directAppeal *bool
						var appealPeriod *int
						notPossibleReason, directAppealReason, competentCourt, courtType := "", "", "", ""

						if p, ok := convertedMappings["possible"].(bool); ok {
							possible = &p
						}
						if r, ok := convertedMappings["not_possible_reason"].(string); ok {
							notPossibleReason = r
						}
						if p, ok := convertedMappings["appeal_period"].(int); ok {
							appealPeriod = &p
						}
						if d, ok := convertedMappings["direct_appeal"].(bool); ok {
							directAppeal = &d
						}
						if r, ok := convertedMappings["direct_appeal_reason"].(string); ok {
							directAppealReason = r
						}
						if c, ok := convertedMappings["competent_court"].(string); ok {
							competentCourt = c
						}
						if t, ok := convertedMappings["court_type"].(string); ok {
							courtType = t
						}

						err = s.CaseManager.DetermineAppealStatus(
							aggregateID,
							possible,
							notPossibleReason,
							appealPeriod,
							directAppeal,
							directAppealReason,
							competentCourt,
							courtType,
						)
						if err != nil {
							return err
						}
					}
				}
			}
		}
	}

	return nil
}

// matchesEvent checks if an event matches the applies spec
func (s *Services) matchesEvent(event *model.Event, applies map[string]interface{}) bool {
	// In a real implementation, we would match event types and filters
	// For simplicity, we'll just do a very basic check

	aggregate, ok := applies["aggregate"].(string)
	if !ok || aggregate == "" {
		return false
	}

	// Check if event type matches any specified event
	events, ok := applies["events"].([]interface{})
	if !ok {
		return false
	}

	for _, eventObj := range events {
		eventSpec, ok := eventObj.(map[string]interface{})
		if !ok {
			continue
		}

		eventType, ok := eventSpec["type"].(string)
		if !ok {
			continue
		}

		if strings.ToLower(eventType) == strings.ToLower(event.EventType) {
			// Check filters if any
			filters, ok := eventSpec["filter"].(map[string]interface{})
			if !ok {
				return true // No filters, so it's a match
			}

			// All filters must match
			match := true
			for key, filterValue := range filters {
				if eventValue, ok := event.Data[key]; !ok || eventValue != filterValue {
					match = false
					break
				}
			}

			if match {
				return true
			}
		}
	}

	return false
}
