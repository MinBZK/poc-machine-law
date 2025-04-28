package handler

import (
	"context"
	"errors"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

// GetCasesBsnServiceLaw implements api.StrictServerInterface.
func (handler *Handler) GetCasesBsnServiceLaw(ctx context.Context, request api.GetCasesBsnServiceLawRequestObject) (api.GetCasesBsnServiceLawResponseObject, error) {
	case_, err := handler.servicer.CaseGetBasedOnBSNServiceLaw(ctx, request.Bsn, request.Service, request.Law)
	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.GetCasesBsnServiceLaw404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.GetCasesBsnServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case get based on bsn, service & law: %w", err)),
		}, nil
	}

	return api.GetCasesBsnServiceLaw200JSONResponse{
		CaseResponseJSONResponse: api.CaseResponseJSONResponse{
			Data: adapter.FromCase(case_),
		},
	}, nil
}

// GetCasesServiceLaw implements api.StrictServerInterface.
func (handler *Handler) GetCasesServiceLaw(ctx context.Context, request api.GetCasesServiceLawRequestObject) (api.GetCasesServiceLawResponseObject, error) {
	cases, err := handler.servicer.CaseListBasedOnServiceLaw(ctx, request.Service, request.Law)
	if err != nil {
		return api.GetCasesServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case list based on service & law: %w", err)),
		}, nil
	}

	return api.GetCasesServiceLaw200JSONResponse{
		CaseListResponseJSONResponse: api.CaseListResponseJSONResponse{
			Data: adapter.FromCases(cases),
		},
	}, nil
}

// CaseSubmit implements api.StrictServerInterface.
func (handler *Handler) CaseSubmit(ctx context.Context, request api.CaseSubmitRequestObject) (api.CaseSubmitResponseObject, error) {
	caseID, err := handler.servicer.CaseSubmit(ctx, adapter.ToCaseSubmit(request.Body.Data))
	if err != nil {
		return api.CaseSubmit400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case submit: %w", err))}, nil
	}

	return api.CaseSubmit201JSONResponse{
		CaseSubmitResponseJSONResponse: api.CaseSubmitResponseJSONResponse{
			Data: caseID,
		},
	}, nil
}

// GetCaseCaseID implements api.StrictServerInterface.
func (handler *Handler) GetCaseCaseID(ctx context.Context, request api.GetCaseCaseIDRequestObject) (api.GetCaseCaseIDResponseObject, error) {
	case_, err := handler.servicer.CaseGet(ctx, request.CaseID)
	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.GetCaseCaseID404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.GetCaseCaseID400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case get: %w", err))}, nil
	}

	return api.GetCaseCaseID200JSONResponse{
		CaseResponseJSONResponse: api.CaseResponseJSONResponse{
			Data: adapter.FromCase(case_),
		},
	}, nil
}

// CaseReview implements api.StrictServerInterface.
func (handler *Handler) CaseReview(ctx context.Context, request api.CaseReviewRequestObject) (api.CaseReviewResponseObject, error) {
	caseID, err := handler.servicer.CaseReview(ctx, model.CaseReview{
		VerifierID: request.Body.Data.VerifierId,
		Approved:   request.Body.Data.Approved,
		Reason:     request.Body.Data.Reason,
	})

	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.CaseReview404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.CaseReview400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case review: %w", err))}, nil
	}

	return api.CaseReview200JSONResponse{
		CaseReviewResponseJSONResponse: api.CaseReviewResponseJSONResponse{
			Data: caseID,
		},
	}, nil
}
