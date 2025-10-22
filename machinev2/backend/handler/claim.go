package handler

import (
	"context"
	"errors"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/backend/service"
)

// ClaimListBasedOnBSN implements api.StrictServerInterface.
func (handler *Handler) ClaimListBasedOnBSN(
	ctx context.Context,
	request api.ClaimListBasedOnBSNRequestObject,
) (api.ClaimListBasedOnBSNResponseObject, error) {
	filter := service.ClaimListFilter{
		OnlyApproved:    request.Params.Approved,
		IncludeRejected: request.Params.IncludeRejected,
	}

	claims, err := handler.servicer.ClaimListBasedOnBSN(ctx, request.Bsn, filter)
	if err != nil {
		return api.ClaimListBasedOnBSN400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim list based on bsn: %w", err)),
		}, err
	}

	return api.ClaimListBasedOnBSN200JSONResponse{
		ClaimListResponseJSONResponse: api.ClaimListResponseJSONResponse{
			Data: adapter.FromClaims(claims),
		},
	}, nil
}

// ClaimListBasedOnBSNServiceLaw implements api.StrictServerInterface.
func (handler *Handler) ClaimListBasedOnBSNServiceLaw(ctx context.Context, request api.ClaimListBasedOnBSNServiceLawRequestObject) (api.ClaimListBasedOnBSNServiceLawResponseObject, error) {
	filter := service.ClaimListFilter{
		OnlyApproved:    request.Params.Approved,
		IncludeRejected: request.Params.IncludeRejected,
	}

	claims, err := handler.servicer.ClaimListBasedOnBSNServiceLaw(ctx, request.Bsn, request.Service, request.Law, filter)
	if err != nil {
		return api.ClaimListBasedOnBSNServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim list based on bsn: %w", err)),
		}, nil
	}

	list := make(map[string]api.Claim, len(claims))

	for key, value := range claims {
		list[key] = adapter.FromClaim(value)
	}

	return api.ClaimListBasedOnBSNServiceLaw200JSONResponse{
		ClaimListWithKeyResponseJSONResponse: api.ClaimListWithKeyResponseJSONResponse{
			Data: list,
		},
	}, err
}

// ClaimApprove implements api.StrictServerInterface.
func (handler *Handler) ClaimApprove(ctx context.Context, request api.ClaimApproveRequestObject) (api.ClaimApproveResponseObject, error) {
	claim := model.ClaimApprove{
		ID:            request.ClaimId,
		VerifiedBy:    request.Body.Data.VerifiedBy,
		VerifiedValue: request.Body.Data.VerifiedValue,
	}

	if err := handler.servicer.ClaimApprove(ctx, claim); err != nil {
		if errors.Is(err, model.ErrClaimNotFound) {
			return api.ClaimApprove404JSONResponse{}, nil
		}

		return api.ClaimApprove400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim approve: %w", err)),
		}, nil
	}

	return api.ClaimApprove200JSONResponse{
		ResponseClaimApproveJSONResponse: api.ResponseClaimApproveJSONResponse{
			Data: request.ClaimId,
		},
	}, nil
}

// ClaimReject implements api.StrictServerInterface.
func (handler *Handler) ClaimReject(ctx context.Context, request api.ClaimRejectRequestObject) (api.ClaimRejectResponseObject, error) {
	claim := model.ClaimReject{
		ID:              request.ClaimId,
		RejectedBy:      request.Body.Data.RejectedBy,
		RejectionReason: request.Body.Data.RejectionReason,
	}

	if err := handler.servicer.ClaimReject(ctx, claim); err != nil {
		if errors.Is(err, model.ErrClaimNotFound) {
			return api.ClaimReject404JSONResponse{}, nil
		}

		handler.logger.ErrorContext(ctx, "claim reject", "err", err)
		return api.ClaimReject400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim reject: %w", err)),
		}, nil
	}

	return api.ClaimReject200JSONResponse{
		ResponseClaimRejectJSONResponse: api.ResponseClaimRejectJSONResponse{
			Data: request.ClaimId,
		},
	}, nil
}

// SubmitClaim implements api.StrictServerInterface.
func (handler *Handler) ClaimSubmit(ctx context.Context, request api.ClaimSubmitRequestObject) (api.ClaimSubmitResponseObject, error) {
	var oldValue *any
	if request.Body.Data.OldValue != nil {
		oldValue = &request.Body.Data.OldValue
	}

	claim := model.ClaimSubmit{
		BSN:          request.Body.Data.Bsn,
		CaseID:       request.Body.Data.CaseId,
		Claimant:     request.Body.Data.Claimant,
		EvidencePath: request.Body.Data.EvidencePath,
		Key:          request.Body.Data.Key,
		Law:          request.Body.Data.Law,
		Service:      request.Body.Data.Service,
		NewValue:     request.Body.Data.NewValue,
		OldValue:     oldValue,
		Reason:       request.Body.Data.Reason,
		AutoApprove:  request.Body.Data.AutoApprove,
	}

	caseID, err := handler.servicer.ClaimSubmit(ctx, claim)
	if err != nil {
		handler.logger.ErrorContext(ctx, "claim submit", "err", err)
		return api.ClaimSubmit400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim approve: %w", err)),
		}, nil
	}

	return api.ClaimSubmit201JSONResponse{
		ResponseClaimSubmitJSONResponse: api.ResponseClaimSubmitJSONResponse{
			Data: caseID,
		},
	}, nil
}
