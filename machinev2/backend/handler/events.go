package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
)

// EventList implements api.StrictServerInterface.
func (handler *Handler) EventList(ctx context.Context, request api.EventListRequestObject) (api.EventListResponseObject, error) {
	events, err := handler.servicer.EventList(ctx)
	if err != nil {
		return api.EventList400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("event list: %w", err)),
		}, err
	}

	return api.EventList200JSONResponse{
		ResponseEventListJSONResponse: api.ResponseEventListJSONResponse{
			Data: adapter.FromEvents(events),
		},
	}, nil
}

// EventListBasedOnCaseID implements api.StrictServerInterface.
func (handler *Handler) EventListBasedOnCaseID(ctx context.Context, request api.EventListBasedOnCaseIDRequestObject) (api.EventListBasedOnCaseIDResponseObject, error) {
	events, err := handler.servicer.CaseEventList(ctx, request.CaseID)
	if err != nil {
		return api.EventListBasedOnCaseID400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case event list: %w}", err))}, nil
	}

	return api.EventListBasedOnCaseID200JSONResponse{
		ResponseEventListJSONResponse: api.ResponseEventListJSONResponse{
			Data: adapter.FromEvents(events),
		},
	}, nil
}
