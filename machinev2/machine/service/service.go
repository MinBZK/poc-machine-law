package service

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	internalContext "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice"
	"github.com/minbzk/poc-machine-law/machinev2/machine/serviceresolver"
	tracer "github.com/minbzk/poc-machine-law/machinev2/machine/trace"
	"github.com/sirupsen/logrus"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/trace"
)

// Services is the main service provider for rule evaluation
type Services struct {
	logger            logging.Logger
	RuleResolver      *ruleresolver.RuleResolver
	services          map[string]ruleservice.RuleServicer
	ServiceResolver   *serviceresolver.ServiceResolver
	RootReferenceDate string
	CaseManager       *CaseManager
	ClaimManager      *ClaimManager
	tracer            trace.Tracer

	mu sync.RWMutex

	shutdownFns []func(context.Context) error

	ruleServiceInMemory bool
	organization        *string
	standAloneMode      bool
	ldvEnabled          bool
	rvaIDs              map[string]uuid.UUID
}

type Option func(*Services)

func WithRuleServiceInMemory() Option {
	return func(s *Services) {
		s.logger.Warning(context.Background(), "running service in memory only mode")
		s.ruleServiceInMemory = true
	}
}

func WithOrganizationName(organization string) Option {
	return func(s *Services) {
		s.logger.Warningf(context.Background(), "starting as organization: %s", organization)
		s.organization = &organization
	}
}

func WithLogboekDataVerwerking(endpoint string, name string) Option {
	return func(s *Services) {
		s.logger.Warningf(context.Background(), "starting with ldv enabled")
		sh, err := setupOTelSDK(endpoint, name)
		if err != nil {
			s.logger.Errorf(context.Background(), "could not setup otel sdk, disabling LDV", "err", err)
			return
		}

		s.ldvEnabled = true
		s.tracer = otel.Tracer(name)
		s.shutdownFns = append(s.shutdownFns, sh)
	}
}

func SetStandaloneMode() Option {
	return func(s *Services) {
		s.logger.Warningf(context.Background(), "setup in standalone mode")
		s.standAloneMode = true
	}
}

// NewServices creates a new services instance
func NewServices(referenceDate time.Time, options ...Option) (*Services, error) {
	serviceResolver, err := serviceresolver.New(serviceresolver.DefaultServiceResolverCfg)
	if err != nil {
		return nil, fmt.Errorf("new service resolver: %w", err)
	}

	ruleResolver, err := ruleresolver.New(ruleresolver.DefaultRuleResolverCfg)
	if err != nil {
		return nil, fmt.Errorf("new rule resolver: %w", err)
	}

	s := &Services{
		logger:              logging.New("service", os.Stdout, logrus.DebugLevel),
		RuleResolver:        ruleResolver,
		ServiceResolver:     serviceResolver,
		services:            make(map[string]ruleservice.RuleServicer),
		RootReferenceDate:   referenceDate.Format("2006-01-02"),
		ruleServiceInMemory: false,
		organization:        nil,
		standAloneMode:      false,
		rvaIDs: map[string]uuid.UUID{
			"evaluate-do": uuid.MustParse("f8d630ae-86e5-4f14-a889-644108429933"),
		},
	}

	// Apply all the functional options to configure the client.
	for _, opt := range options {
		opt(s)
	}

	// Initialize services
	for service := range s.RuleResolver.GetServiceLaws() {
		svc, err := ruleservice.New(s.logger, service, s)
		if err != nil {
			return nil, fmt.Errorf("new rule service: %w", err)
		}

		s.services[service] = svc
	}

	// Create managers
	s.CaseManager = NewCaseManager(s.logger, s)
	s.ClaimManager = NewClaimManager(s)
	s.ClaimManager.CaseManager = s.CaseManager

	return s, nil
}

func (s *Services) GetService(key string) (ruleservice.RuleServicer, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	r, ok := s.services[key]
	return r, ok
}

// GetDiscoverableServiceLaws returns discoverable services and laws
func (s *Services) GetDiscoverableServiceLaws(discoverableBy string) map[string][]string {
	return s.RuleResolver.GetDiscoverableServiceLaws(discoverableBy)
}

// SetSourceDataFrame sets a source DataFrame for a service
func (s *Services) SetSourceDataFrame(ctx context.Context, service, table string, df model.DataFrame) error {
	if srv, ok := s.GetService(service); ok {
		if err := srv.SetSourceDataFrame(ctx, table, df); err != nil {
			return fmt.Errorf("set source dataframe: %w", err)
		}
	}

	return nil
}

func (s *Services) Reset(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	var errs error

	for key := range s.services {
		if err := s.services[key].Reset(ctx); err != nil {
			errs = errors.Join(errs, err)
		}
	}

	return errs
}

// GetRuleResolver returns the rule resolver
func (s *Services) GetRuleResolver() *ruleresolver.RuleResolver {
	return s.RuleResolver
}

// GetRuleResolver returns the rule resolver
func (s *Services) GetServiceResolver() *serviceresolver.ServiceResolver {
	return s.ServiceResolver
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
	var span trace.Span

	if referenceDate == "" {
		referenceDate = s.RootReferenceDate
	}

	if s.ldvEnabled {
		spec, err := s.RuleResolver.GetRuleSpec(law, referenceDate, service)
		if err != nil {
			return nil, fmt.Errorf("get rule spec: %w", err)
		}

		ctx, span = tracer.Action(ctx, s.tracer,
			fmt.Sprintf("uri://%s.example/activities/evaluate-do", strings.ToLower(s.GetOrganizationName())),
			tracer.SetAttributeBSN(parameters["BSN"].(string)),
			tracer.SetAttributeActivityID(s.rvaIDs["evaluate-do"].String()),
			tracer.SetAlgorithmID(spec.UUID.String()),
		)

		defer span.End()
	}

	result, err := s.evaluate(ctx, service, law, parameters, referenceDate, overwriteInput, requestedOutput, approved)
	if err != nil {
		if span != nil {
			span.SetStatus(codes.Error, err.Error())
		}

		return nil, err
	}

	if span != nil {
		span.SetStatus(codes.Ok, "")
	}

	return result, nil
}

func (s *Services) evaluate(
	ctx context.Context,
	service string,
	law string,
	parameters map[string]any,
	referenceDate string,
	overwriteInput map[string]map[string]any,
	requestedOutput string,
	approved bool,
) (*model.RuleResult, error) {
	svc, ok := s.GetService(service)
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
func (s *Services) ApplyRules(ctx context.Context, event model.Event) error {
	for _, rule := range s.RuleResolver.Rules {
		for _, apply := range rule.Properties.Applies {
			if s.matchesEvent(event, apply) {
				aggregateID := event.CaseID
				aggregate, err := s.CaseManager.GetCaseByID(ctx, aggregateID)
				if err != nil {
					return err
				}

				parameters := map[string]any{
					apply.Name: aggregate,
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
				for _, update := range apply.Update {
					// Convert values
					convertedMappings := make(map[string]any)
					for key, value := range update.Mapping {
						if len(value) > 0 && value[0] == '$' {
							// Strip $ from value
							outputName := value[1:]
							convertedMappings[key] = result.Output[outputName]
						}
					}

					// Call method on case manager
					switch update.Method {
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
func (s *Services) matchesEvent(event model.Event, apply ruleresolver.Apply) bool {
	// In a real implementation, we would match event types and filters
	// For simplicity, we'll just do a very basic check

	aggregate := apply.Aggregate
	if aggregate == "" {
		return false
	}

	// Check if event type matches any specified event
	for _, eventObj := range apply.Events {
		if strings.EqualFold(strings.ToLower(eventObj.Type), strings.ToLower(eventObj.Type)) {
			// All filters must match
			match := true
			for key, filterValue := range eventObj.Filter {
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

func (s *Services) HasOrganizationName() bool {
	return s.organization != nil
}

func (s *Services) GetOrganizationName() string {
	if s.organization == nil {
		return ""
	}

	return *s.organization
}

func (s *Services) RuleServicesInMemory() bool {
	return s.ruleServiceInMemory
}

func (s *Services) InStandAloneMode() bool {
	return s.standAloneMode
}
