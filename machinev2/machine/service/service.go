package service

import (
	"context"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	internalContext "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/utils"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/sirupsen/logrus"
)

// Services is the main service provider for rule evaluation
type Services struct {
	logger            logging.Logger
	Resolver          *utils.RuleResolver
	services          map[string]*RuleService
	RootReferenceDate string
	CaseManager       *CaseManager
	ClaimManager      *ClaimManager
	mu                sync.RWMutex
}

// NewServices creates a new services instance
func NewServices(referenceDate time.Time) *Services {
	s := &Services{
		logger:            logging.New("service", os.Stdout, logrus.DebugLevel),
		Resolver:          utils.NewRuleResolver(),
		services:          make(map[string]*RuleService),
		RootReferenceDate: referenceDate.Format("2006-01-02"),
	}

	// Initialize services
	for service := range s.Resolver.GetServiceLaws() {
		s.services[service] = NewRuleService(s.logger, service, s)
	}

	// Create managers
	s.CaseManager = NewCaseManager(s.logger, s)
	s.ClaimManager = NewClaimManager(s)
	s.ClaimManager.CaseManager = s.CaseManager

	return s
}

// GetDiscoverableServiceLaws returns discoverable services and laws
func (s *Services) GetDiscoverableServiceLaws(discoverableBy string) map[string][]string {
	return s.Resolver.GetDiscoverableServiceLaws(discoverableBy)
}

// SetSourceDataFrame sets a source DataFrame for a service
func (s *Services) SetSourceDataFrame(service, table string, df model.DataFrame) {
	if srv, ok := s.services[service]; ok {
		srv.SetSourceDataFrame(table, df)
	}
}

func (s *Services) Reset() {
	for key := range s.services {
		s.services[key].Reset()
	}
}

// GetResolver returns the rule resolver
func (s *Services) GetResolver() *utils.RuleResolver {
	return s.Resolver
}

// GetCaseManager returns the case manager with access to events
func (s *Services) GetCaseManager() internalContext.CaseManagerAccessor {
	return s.CaseManager
}

// GetClaimManager returns the claim manager with access to claims
func (s *Services) GetClaimManager() internalContext.ClaimManagerAccessor {
	return s.ClaimManager
}

// Evaluate evaluates rules for a specific service, law, and context
func (s *Services) Evaluate(
	ctx context.Context,
	service string,
	law string,
	parameters map[string]any,
	referenceDate string,
	overwriteInput map[string]map[string]any,
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

	// TODO add double line into logger
	err = s.logger.IndentBlock(
		ctx,
		fmt.Sprintf("%s: %s (%s %v %s)", service, law, referenceDate, parameters, requestedOutput),
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
func (s *Services) ExtractValueTree(root *model.PathNode) map[string]any {
	flattened := make(map[string]any)
	stack := []struct {
		node          *model.PathNode
		serviceParent map[string]any
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
			resolveEntry := map[string]any{
				"result":   node.Result,
				"required": node.Required,
				"details":  node.Details,
			}

			if serviceParent != nil {
				children, hasChildren := serviceParent["children"].(map[string]any)
				if !hasChildren {
					children = make(map[string]any)
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
			serviceEntry := map[string]any{
				"result":   node.Result,
				"required": node.Required,
				"service":  node.Details["service"],
				"law":      node.Details["law"],
				"children": make(map[string]any),
				"details":  node.Details,
			}

			if serviceParent != nil {
				children, hasChildren := serviceParent["children"].(map[string]any)
				if !hasChildren {
					children = make(map[string]any)
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
					serviceParent map[string]any
				}{node: node.Children[i], serviceParent: serviceEntry})
			}
			continue
		}

		// Add children to the stack for further processing
		for i := len(node.Children) - 1; i >= 0; i-- {
			stack = append(stack, struct {
				node          *model.PathNode
				serviceParent map[string]any
			}{node: node.Children[i], serviceParent: serviceParent})
		}
	}

	return flattened
}

// ApplyRules applies rules in response to events
func (s *Services) ApplyRules(ctx context.Context, event *model.Event) error {
	for _, rule := range s.Resolver.Rules {
		applies, ok := rule.Properties["applies"].([]any)
		if !ok {
			continue
		}

		for _, applyObj := range applies {
			apply, ok := applyObj.(map[string]any)
			if !ok {
				continue
			}

			if s.matchesEvent(event, apply) {
				aggregateID := event.CaseID
				aggregate, err := s.CaseManager.GetCaseByID(ctx, aggregateID)
				if err != nil {
					return err
				}

				parameters := map[string]any{
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
				updates, ok := apply["update"].([]any)
				if !ok {
					continue
				}

				for _, updateObj := range updates {
					update, ok := updateObj.(map[string]any)
					if !ok {
						continue
					}

					mappings, ok := update["mapping"].(map[string]any)
					if !ok {
						continue
					}

					// Convert values
					convertedMappings := make(map[string]any)
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
func (s *Services) matchesEvent(event *model.Event, applies map[string]any) bool {
	// In a real implementation, we would match event types and filters
	// For simplicity, we'll just do a very basic check

	aggregate, ok := applies["aggregate"].(string)
	if !ok || aggregate == "" {
		return false
	}

	// Check if event type matches any specified event
	events, ok := applies["events"].([]any)
	if !ok {
		return false
	}

	for _, eventObj := range events {
		eventSpec, ok := eventObj.(map[string]any)
		if !ok {
			continue
		}

		eventType, ok := eventSpec["type"].(string)
		if !ok {
			continue
		}

		if strings.EqualFold(strings.ToLower(eventType), strings.ToLower(event.EventType)) {
			// Check filters if any
			filters, ok := eventSpec["filter"].(map[string]any)
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
