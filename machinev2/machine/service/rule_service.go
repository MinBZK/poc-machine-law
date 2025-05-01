package service

import (
	"context"
	"fmt"
	"sync"

	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/engine"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/utils"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
)

// RuleService interface for executing business rules for a specific service
type RuleService struct {
	logger           logging.Logger
	ServiceName      string
	Services         *Services
	Resolver         *utils.RuleResolver
	engines          map[string]map[string]*engine.RulesEngine
	SourceDataFrames model.SourceDataFrame
	mu               sync.RWMutex
}

// NewRuleService creates a new rule service instance
func NewRuleService(logger logging.Logger, serviceName string, services *Services) *RuleService {
	return &RuleService{
		logger:           logger.WithName("service"),
		ServiceName:      serviceName,
		Services:         services,
		Resolver:         utils.NewRuleResolver(),
		engines:          make(map[string]map[string]*engine.RulesEngine),
		SourceDataFrames: NewSourceDataFrame(),
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

	ruleEngine := engine.NewRulesEngine(rs.logger, spec, rs.Services, referenceDate)
	rs.engines[law][referenceDate] = ruleEngine

	return ruleEngine, nil
}

// GetResolver returns the rule resolver
func (rs *RuleService) GetResolver() *utils.RuleResolver {
	return rs.Resolver
}

// Evaluate evaluates rules for given law and reference date
func (rs *RuleService) Evaluate(
	ctx context.Context,
	law string,
	referenceDate string,
	parameters map[string]any,
	overwriteInput map[string]map[string]any,
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

	rulespecID, err := uuid.Parse(ruleEngine.Spec["uuid"].(string))
	if err != nil {
		return nil, err
	}

	return model.NewRuleResult(result, rulespecID), nil
}

// GetRuleInfo gets metadata about the rule that would be applied for given law and date
func (rs *RuleService) GetRuleInfo(law, referenceDate string) map[string]any {
	rule, err := rs.Resolver.FindRule(law, referenceDate, rs.ServiceName)
	if err != nil {
		return nil
	}

	return map[string]any{
		"uuid":       rule.UUID,
		"name":       rule.Name,
		"valid_from": rule.ValidFrom.Format("2006-01-02"),
	}
}

// SetSourceDataFrame sets a source DataFrame
func (rs *RuleService) SetSourceDataFrame(table string, df model.DataFrame) {
	rs.SourceDataFrames.Set(table, df)
}

// Reset removes all data in the rule service
func (rs *RuleService) Reset() {
	rs.SourceDataFrames.Reset()
}
