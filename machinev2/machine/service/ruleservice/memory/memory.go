package memory

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"sync"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/engine"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
)

// RuleService interface for executing business rules for a specific service
type RuleService struct {
	logger           logger.Logger
	ServiceName      string
	Services         service.ServiceProvider
	CaseManager      casemanager.CaseManager
	ClaimManager     claimmanager.ClaimManager
	Resolver         *ruleresolver.RuleResolve
	engines          map[string]map[string]*engine.RulesEngine
	SourceDataFrames model.SourceDataFrame
	mu               sync.RWMutex
}

// New creates a new rule service instance
func New(logger logger.Logger, serviceName string, services service.ServiceProvider, caseManager casemanager.CaseManager, claimManager claimmanager.ClaimManager) (*RuleService, error) {
	logger.Warningf("creating inmemory ruleservice: %s", serviceName)

	resolver, err := ruleresolver.New()
	if err != nil {
		return nil, fmt.Errorf("new rule resolver: %w", err)
	}

	return &RuleService{
		logger:           logger.WithName("service"),
		ServiceName:      serviceName,
		Services:         services,
		CaseManager:      caseManager,
		ClaimManager:     claimManager,
		Resolver:         resolver,
		engines:          make(map[string]map[string]*engine.RulesEngine),
		SourceDataFrames: NewSourceDataFrame(),
	}, nil
}

// getEngine gets or creates a RulesEngine instance for given law and date
func (rs *RuleService) getEngine(law string, referenceDate time.Time) (*engine.RulesEngine, error) {
	date := referenceDate.Format(time.DateOnly)

	rs.mu.Lock()
	defer rs.mu.Unlock()

	// Check if engine already exists
	if lawEngines, ok := rs.engines[law]; ok {
		if engine, ok := lawEngines[date]; ok {
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

	ruleEngine := engine.NewRulesEngine(spec, rs.Services, rs.CaseManager, rs.ClaimManager, date)
	rs.engines[law][date] = ruleEngine

	return ruleEngine, nil
}

// GetResolver returns the rule resolver
func (rs *RuleService) GetResolver() *ruleresolver.RuleResolve {
	return rs.Resolver
}

// Evaluate evaluates rules for given law and reference date
func (rs *RuleService) Evaluate(
	ctx context.Context,
	law string,
	referenceDate, effectiveDate time.Time,
	parameters map[string]any,
	overwriteInput map[string]any,
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
		effectiveDate,
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
func (rs *RuleService) Reset(ctx context.Context) error {
	rs.SourceDataFrames.Reset()

	switch rs.Services.GetExternalClaimResolver() {
	case "ubb":
		if err := rs.UbbReset(ctx); err != nil {
			return fmt.Errorf("ubb reset: %w", err)
		}
	}

	return nil
}

func (rs *RuleService) UbbReset(ctx context.Context) error {
	endpoint := rs.Services.GetExternalClaimResolverUBBEndpoint()
	client := http.DefaultClient

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint+":8081/reset-reseed", nil)
	if err != nil {
		return fmt.Errorf("new request: %w", err)
	}

	response, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("do: %w", err)
	}

	if response.StatusCode != http.StatusOK {
		body, _ := httputil.DumpResponse(response, true)
		return fmt.Errorf("invalid response code: %d body: %s", response.StatusCode, string(body))
	}

	return nil
}
