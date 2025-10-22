package service

import (
	"context"
	"fmt"

	"github.com/looplab/eventhorizon/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
)

// CaseListBasedOnBSN implements Servicer.
func (service *Service) CaseListBasedOnBSN(ctx context.Context, bsn string) ([]model.Case, error) {
	records, err := service.casemanager.GetCasesByBSN(ctx, bsn)
	if err != nil {
		return nil, fmt.Errorf("get case by bsn: %w", err)
	}

	return ToCases(records), nil
}

func (service *Service) CaseGetBasedOnBSNServiceLaw(ctx context.Context, bsn, svc, law string) (model.Case, error) {
	record, err := service.casemanager.GetCase(ctx, bsn, svc, law)
	if err != nil {
		return model.Case{}, fmt.Errorf("get case by bsn: %w", err)
	}

	if record == nil {
		return model.Case{}, model.ErrCaseNotFound
	}

	return ToCase(record), nil
}

func (service *Service) CaseListBasedOnServiceLaw(ctx context.Context, svc, law string) ([]model.Case, error) {
	records, err := service.casemanager.GetCasesByLaw(ctx, svc, law)
	if err != nil {
		return nil, fmt.Errorf("get case by bsn: %w", err)
	}

	if records == nil {
		return []model.Case{}, nil
	}

	return ToCases(records), nil
}

// CaseGet implements Servicer.
func (service *Service) CaseGet(ctx context.Context, caseID uuid.UUID) (model.Case, error) {
	record, err := service.casemanager.GetCaseByID(ctx, caseID)
	if err != nil {
		return model.Case{}, fmt.Errorf("get case by id: %w", err)
	}

	return ToCase(record), nil
}

// CaseSubmit implements Servicer.
func (service *Service) CaseSubmit(ctx context.Context, case_ model.CaseSubmit) (uuid.UUID, error) {
	caseID, err := service.casemanager.SubmitCase(
		ctx,
		case_.BSN,
		case_.Service,
		case_.Law,
		case_.Parameters,
		case_.ClaimedResult,
		case_.ApprovedClaimsOnly,
	)

	if err != nil {
		return uuid.Nil, fmt.Errorf("submit case: %w", err)
	}

	return caseID, nil
}

func (service *Service) CaseReview(ctx context.Context, case_ model.CaseReview) (uuid.UUID, error) {
	err := service.casemanager.CompleteManualReview(ctx, case_.CaseID, case_.VerifierID, case_.Approved, case_.Reason, nil)
	if err != nil {
		return uuid.Nil, fmt.Errorf("complete manual review: %w", err)
	}

	return case_.CaseID, nil
}

func (service *Service) CaseObject(ctx context.Context, case_ model.CaseObject) (uuid.UUID, error) {
	err := service.casemanager.ObjectCase(ctx, case_.CaseID, case_.Reason)
	if err != nil {
		return uuid.Nil, fmt.Errorf("object case: %w", err)
	}

	return case_.CaseID, nil
}
func ToCase(case_ *casemanager.Case) model.Case {
	return model.Case{
		ID:                 case_.ID,
		Service:            case_.Service,
		Law:                case_.Law,
		BSN:                case_.BSN,
		Status:             string(case_.Status),
		Approved:           case_.Approved,
		ApprovedClaimsOnly: case_.ApprovedClaimsOnly,
		ClaimedResult:      case_.ClaimedResult,
		VerifiedResult:     case_.VerifiedResult,
		Parameters:         case_.Parameters,
		RuleSpecID:         case_.RulespecID,
		AppealStatus:       ToCaseAppealStatus(case_.AppealStatus),
		ObjectionStatus:    ToCaseObjectionStatus(case_.ObjectionStatus),
	}
}

func ToCases(cases []*casemanager.Case) []model.Case {
	cs := make([]model.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, ToCase(cases[idx]))
	}

	return cs
}

func ToCaseObjectionStatus(objection casemanager.CaseObjectionStatus) model.CaseObjectionStatus {
	return model.CaseObjectionStatus{
		Possible:          objection.Possible,
		NotPossibleReason: objection.NotPossibleReason,
		ObjectionPeriod:   objection.ObjectionPeriod,
		DecisionPeriod:    objection.DecisionPeriod,
		ExtensionPeriod:   objection.ExtensionPeriod,
		Admissable:        objection.Admissable,
	}
}

func ToCaseAppealStatus(objection casemanager.CaseAppealStatus) model.CaseAppealStatus {
	return model.CaseAppealStatus{
		Possible:           objection.Possible,
		NotPossibleReason:  objection.NotPossibleReason,
		AppealPeriod:       objection.AppealPeriod,
		DirectAppeal:       objection.DirectAppeal,
		DirectAppealReason: objection.DirectAppealReason,
		CompetentCourt:     objection.CompetentCourt,
		CourtType:          objection.CourtType,
	}
}
