package memory

import (
	"context"
	"fmt"
	"sync"

	contexter "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/engine"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

// RuleService interface for executing business rules for a specific service
type RuleService struct {
	logger           logging.Logger
	ServiceName      string
	Services         contexter.ServiceProvider
	Resolver         *ruleresolver.RuleResolver
	engines          map[string]map[string]*engine.RulesEngine
	SourceDataFrames model.SourceDataFrame
	mu               sync.RWMutex
}

// New creates a new rule service instance
func New(logger logging.Logger, serviceName string, services contexter.ServiceProvider) (*RuleService, error) {
	logger.Warningf(context.Background(), "creating inmemory ruleservice: %s", serviceName)

	resolver, err := ruleresolver.New()
	if err != nil {
		return nil, fmt.Errorf("new rule resolver: %w", err)
	}

	return &RuleService{
		logger:           logger.WithName("service"),
		ServiceName:      serviceName,
		Services:         services,
		Resolver:         resolver,
		engines:          make(map[string]map[string]*engine.RulesEngine),
		SourceDataFrames: NewSourceDataFrame(),
	}, nil
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

	if spec.Service != rs.ServiceName {
		return nil, fmt.Errorf("rule spec service '%s' does not match service '%s'", spec.Service, rs.ServiceName)
	}

	ruleEngine := engine.NewRulesEngine(rs.logger, spec, rs.Services, referenceDate)
	rs.engines[law][referenceDate] = ruleEngine

	return ruleEngine, nil
}

// GetResolver returns the rule resolver
func (rs *RuleService) GetResolver() *ruleresolver.RuleResolver {
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

	return model.NewRuleResult(result, ruleEngine.Spec.UUID), nil
}

// SetSourceDataFrame sets a source DataFrame
func (rs *RuleService) SetSourceDataFrame(_ context.Context, table string, df model.DataFrame) error {
	rs.SourceDataFrames.Set(table, df)

	return nil
}

// Reset removes all data in the rule service
func (rs *RuleService) Reset(_ context.Context) error {
	rs.SourceDataFrames.Reset()

	return nil
}
