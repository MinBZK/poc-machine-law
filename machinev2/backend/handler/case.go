package handler

import (
	"context"
	"errors"
	"fmt"
	"net/url"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

// CaseBasedOnBSNServiceLaw implements api.StrictServerInterface.
func (handler *Handler) CaseBasedOnBSNServiceLaw(ctx context.Context, request api.CaseBasedOnBSNServiceLawRequestObject) (api.CaseBasedOnBSNServiceLawResponseObject, error) {
	law, err := url.QueryUnescape(request.Law)
	if err != nil {
		return api.CaseBasedOnBSNServiceLaw400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("could not decode law"))}, nil
	}

	service, err := url.QueryUnescape(request.Service)
	if err != nil {
		return api.CaseBasedOnBSNServiceLaw400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("could not decode service"))}, nil
	}

	case_, err := handler.servicer.CaseGetBasedOnBSNServiceLaw(ctx, request.Bsn, service, law)
	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.CaseBasedOnBSNServiceLaw404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.CaseBasedOnBSNServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case get based on bsn, service & law: %w", err)),
		}, err
	}

	return api.CaseBasedOnBSNServiceLaw200JSONResponse{
		ResponseCaseJSONResponse: api.ResponseCaseJSONResponse{
			Data: adapter.FromCase(case_),
		},
	}, nil
}

// CaseListBasedOnServiceLaw implements api.StrictServerInterface.
func (handler *Handler) CaseListBasedOnServiceLaw(ctx context.Context, request api.CaseListBasedOnServiceLawRequestObject) (api.CaseListBasedOnServiceLawResponseObject, error) {
	law, err := url.QueryUnescape(request.Law)
	if err != nil {
		return api.CaseListBasedOnServiceLaw400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("could not decode law"))}, nil
	}

	service, err := url.QueryUnescape(request.Service)
	if err != nil {
		return api.CaseListBasedOnServiceLaw400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("could not decode service"))}, nil
	}

	cases, err := handler.servicer.CaseListBasedOnServiceLaw(ctx, service, law)
	if err != nil {
		return api.CaseListBasedOnServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case list based on service & law: %w", err)),
		}, err
	}

	return api.CaseListBasedOnServiceLaw200JSONResponse{
		ResponseCaseListJSONResponse: api.ResponseCaseListJSONResponse{
			Data: adapter.FromCases(cases),
		},
	}, nil
}

// CaseListBasedOnBSN implements api.StrictServerInterface.
func (handler *Handler) CaseListBasedOnBSN(ctx context.Context, request api.CaseListBasedOnBSNRequestObject) (api.CaseListBasedOnBSNResponseObject, error) {
	cases, err := handler.servicer.CaseListBasedOnBSN(ctx, request.Bsn)
	if err != nil {
		return api.CaseListBasedOnBSN400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case list based on bsn: %w", err)),
		}, err
	}

	return api.CaseListBasedOnBSN200JSONResponse{
		ResponseCaseListJSONResponse: api.ResponseCaseListJSONResponse{
			Data: adapter.FromCases(cases),
		},
	}, nil
}

// CaseSubmit implements api.StrictServerInterface.
func (handler *Handler) CaseSubmit(ctx context.Context, request api.CaseSubmitRequestObject) (api.CaseSubmitResponseObject, error) {
	caseID, err := handler.servicer.CaseSubmit(ctx, adapter.ToCaseSubmit(request.Body.Data))
	if err != nil {
		return api.CaseSubmit400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case submit: %w", err))}, err
	}

	return api.CaseSubmit201JSONResponse{
		ResponseCaseSubmitJSONResponse: api.ResponseCaseSubmitJSONResponse{
			Data: caseID,
		},
	}, nil
}

// CaseGet implements api.StrictServerInterface.
func (handler *Handler) CaseGet(ctx context.Context, request api.CaseGetRequestObject) (api.CaseGetResponseObject, error) {
	case_, err := handler.servicer.CaseGet(ctx, request.CaseID)
	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.CaseGet404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.CaseGet400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case get: %w", err))}, nil
	}

	return api.CaseGet200JSONResponse{
		ResponseCaseJSONResponse: api.ResponseCaseJSONResponse{
			Data: adapter.FromCase(case_),
		},
	}, nil
}

// CaseReview implements api.StrictServerInterface.
func (handler *Handler) CaseReview(ctx context.Context, request api.CaseReviewRequestObject) (api.CaseReviewResponseObject, error) {
	caseID, err := handler.servicer.CaseReview(ctx, model.CaseReview{
		CaseID:     request.CaseID,
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
			}, err
		}

		return api.CaseReview400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case review: %w", err))}, nil
	}

	return api.CaseReview200JSONResponse{
		ResponseCaseReviewJSONResponse: api.ResponseCaseReviewJSONResponse{
			Data: caseID,
		},
	}, nil
}

// CaseObject implements api.StrictServerInterface.
func (handler *Handler) CaseObject(ctx context.Context, request api.CaseObjectRequestObject) (api.CaseObjectResponseObject, error) {
	caseID, err := handler.servicer.CaseObject(ctx, model.CaseObject{
		CaseID: request.CaseID,
		Reason: request.Body.Data.Reason,
	})

	if err != nil {
		if errors.Is(err, model.ErrCaseNotFound) {
			return api.CaseObject404JSONResponse{
				ResourceNotFoundErrorResponseJSONResponse: api.ResourceNotFoundErrorResponseJSONResponse{
					Errors: &[]api.Error{{
						Message: err.Error(),
					}},
				},
			}, nil
		}

		return api.CaseObject400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case review: %w", err))}, nil
	}

	return api.CaseObject200JSONResponse{
		ResponseCaseObjectJSONResponse: api.ResponseCaseObjectJSONResponse{
			Data: caseID,
		},
	}, nil
}
