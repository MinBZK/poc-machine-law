package service

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
)

func (service *Service) CaseGetBasedOnBSNServiceLaw(ctx context.Context, bsn, svc, law string) (model.Case, error) {
	record, err := service.service.CaseManager.GetCase(ctx, bsn, svc, law)
	if err != nil {
		return model.Case{}, fmt.Errorf("get case by bsn: %w", err)
	}

	if record == nil {
		return model.Case{}, model.ErrCaseNotFound
	}

	return ToCase(record), nil
}

func (service *Service) CaseListBasedOnServiceLaw(ctx context.Context, svc, law string) ([]model.Case, error) {
	records, err := service.service.CaseManager.GetCasesByLaw(ctx, law, svc)
	if err != nil {
		return nil, fmt.Errorf("get case by bsn: %w", err)
	}

	if records == nil {
		return []model.Case{}, nil
	}

	return ToCases(records), nil
}

func ToCase(case_ *casemanager.Case) model.Case {
	return model.Case{
		ID:      case_.ID,
		BSN:     case_.BSN,
		Service: case_.Service,
		Law:     case_.Law,
		Status:  string(case_.Status),
	}
}

func ToCases(cases []*casemanager.Case) []model.Case {
	cs := make([]model.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, ToCase(cases[idx]))
	}

	return cs
}
