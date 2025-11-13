package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
)

// ServiceLawsDiscoverableList implements api.StrictServerInterface.
func (handler *Handler) ServiceLawsDiscoverableList(ctx context.Context, request api.ServiceLawsDiscoverableListRequestObject) (api.ServiceLawsDiscoverableListResponseObject, error) {
	discoverableBy := "CITIZEN"
	if request.Params.DiscoverableBy != nil {
		discoverableBy = *request.Params.DiscoverableBy
	}

	items, err := handler.servicer.ServiceLawsDiscoverableList(ctx, discoverableBy)
	if err != nil {
		return api.ServiceLawsDiscoverableList400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("service laws discoverable list: %w", err)),
		}, nil
	}

	return api.ServiceLawsDiscoverableList200JSONResponse{
		ServiceListResponseJSONResponse: api.ServiceListResponseJSONResponse{
			Data: adapter.FromServices(items),
		},
	}, nil
}

// RuleSpecGet implements api.StrictServerInterface.
func (handler *Handler) RuleSpecGet(ctx context.Context, request api.RuleSpecGetRequestObject) (api.RuleSpecGetResponseObject, error) {
	spec, err := handler.servicer.GetRuleSpec(request.Params.Service, request.Params.Law, request.Params.ReferenceDate.Time)
	if err != nil {
		return api.RuleSpecGet400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("get rule spec: %w", err)),
		}, err
	}

	return api.RuleSpecGet200JSONResponse{
		RuleSpecResponseJSONResponse: api.RuleSpecResponseJSONResponse{
			Data: adapter.FromRuleSpec(spec),
		},
	}, nil
}
