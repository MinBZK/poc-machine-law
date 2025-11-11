package handler

import (
	"context"
	"errors"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/service"
)

// ProfileList implements api.StrictServerInterface.
func (handler *Handler) ProfileList(ctx context.Context, request api.ProfileListRequestObject) (api.ProfileListResponseObject, error) {
	profiles, err := handler.servicer.ProfileList(ctx)
	if err != nil {
		return api.ProfileList400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("profile list: %w", err)),
		}, nil
	}

	return api.ProfileList200JSONResponse{
		ResponseProfileListJSONResponse: api.ResponseProfileListJSONResponse{
			Data: adapter.FromProfiles(profiles),
		},
	}, nil
}

// ProfileGet implements api.StrictServerInterface.
func (handler *Handler) ProfileGet(ctx context.Context, request api.ProfileGetRequestObject) (api.ProfileGetResponseObject, error) {
	profile, err := handler.servicer.Profile(ctx, request.Bsn)
	if err != nil {
		if errors.Is(err, service.ErrProfileNotFound) {
			return api.ProfileGet404JSONResponse{ResourceNotFoundErrorResponseJSONResponse: NewResourceNotFoundErrorResponseObject(err)}, nil
		}

		return api.ProfileGet400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("profile: %w", err))}, nil
	}

	return api.ProfileGet200JSONResponse{
		ProfileResponseJSONResponse: api.ProfileResponseJSONResponse{
			Data: adapter.FromProfile(profile),
		},
	}, nil
}
