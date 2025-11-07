package ruleservice

import (
	"context"
	"strings"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/claimmanager"
	"github.com/minbzk/poc-machine-law/machinev2/machine/logger"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice/httpservice"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice/memory"
)

type RuleServicer interface {
	Evaluate(ctx context.Context, law string, referenceDate, effectiveDate time.Time, parameters map[string]any, overwriteInput map[string]any, requestedOutput string, approved bool) (*model.RuleResult, error)
	SetSourceDataFrame(ctx context.Context, table string, df model.DataFrame) error
	Reset(ctx context.Context) error
}

func New(logger logger.Logger, service string, services service.ServiceProvider, caseManager casemanager.CaseManager, claimManager claimmanager.ClaimManager) (RuleServicer, error) {
	resolver := services.GetServiceResolver()

	if services.RuleServicesInMemory() {
		return memory.New(logger, service, services, caseManager, claimManager)
	}

	if services.HasOrganizationName() && strings.Compare(strings.ToLower(services.GetOrganizationName()), strings.ToLower(service)) == 0 {
		return memory.New(logger, service, services, caseManager, claimManager)
	}

	for _, svc := range resolver.Services {
		if strings.Compare(strings.ToLower(svc.Name), strings.ToLower(service)) == 0 {
			return httpservice.New(logger, service, services, svc)
		}
	}

	return memory.New(logger, service, services, caseManager, claimManager)
}
