package ruleservice

import (
	"context"
	"strings"

	contexter "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice/httpservice"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice/memory"
)

type RuleServicer interface {
	Evaluate(ctx context.Context, law string, referenceDate string, parameters map[string]any, overwriteInput map[string]map[string]any, requestedOutput string, approved bool) (*model.RuleResult, error)
	SetSourceDataFrame(ctx context.Context, table string, df model.DataFrame) error
	Reset(ctx context.Context) error
}

func New(logger logging.Logger, service string, services contexter.ServiceProvider) (RuleServicer, error) {
	resolver := services.GetServiceResolver()

	if services.RuleServicesInMemory() {
		return memory.New(logger, service, services)
	}

	if services.HasOrganizationName() && strings.Compare(strings.ToLower(services.GetOrganizationName()), strings.ToLower(service)) == 0 {
		return memory.New(logger, service, services)
	}

	for _, svc := range resolver.Services {
		if strings.Compare(strings.ToLower(svc.Name), strings.ToLower(service)) == 0 {
			return httpservice.New(logger, service, services, svc, services.InStandAloneMode())
		}
	}

	return memory.New(logger, service, services)
}
