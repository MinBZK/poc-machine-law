package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/service"
)

// GetClaimsBsn implements api.StrictServerInterface.
func (handler *Handler) GetClaimsBsn(ctx context.Context, request api.GetClaimsBsnRequestObject) (api.GetClaimsBsnResponseObject, error) {
	filter := service.ClaimListFilter{
		OnlyApproved:    request.Params.Approved,
		IncludeRejected: request.Params.IncludeRejected,
	}

	claims, err := handler.servicer.ClaimListBasedOnBSN(ctx, request.Bsn, filter)
	if err != nil {
		return api.GetClaimsBsn400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim list based on bsn: %w", err)),
		}, nil
	}

	return api.GetClaimsBsn200JSONResponse{
		ClaimListResponseJSONResponse: api.ClaimListResponseJSONResponse{
			Data: adapter.FromClaims(claims),
		},
	}, nil
}

// GetClaimsBsnServiceLaw implements api.StrictServerInterface.
func (handler *Handler) GetClaimsBsnServiceLaw(ctx context.Context, request api.GetClaimsBsnServiceLawRequestObject) (api.GetClaimsBsnServiceLawResponseObject, error) {
	filter := service.ClaimListFilter{
		OnlyApproved:    request.Params.Approved,
		IncludeRejected: request.Params.IncludeRejected,
	}

	claims, err := handler.servicer.ClaimListBasedOnBSNServiceLaw(ctx, request.Bsn, request.Service, request.Law, filter)
	if err != nil {
		return api.GetClaimsBsnServiceLaw400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("claim list based on bsn: %w", err)),
		}, nil
	}

	list := make(map[string]api.Claim, len(claims))

	for key, value := range claims {
		list[key] = adapter.FromClaim(value)
	}

	return api.GetClaimsBsnServiceLaw200JSONResponse{
		ClaimListWithKeyResponseJSONResponse: api.ClaimListWithKeyResponseJSONResponse{
			Data: list,
		},
	}, err
}
