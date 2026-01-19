package handler

import (
	"context"
	"fmt"
	"net/url"

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

	law, _ := url.QueryUnescape(request.Params.Law)
	service, _ := url.QueryUnescape(request.Params.Service)

	spec, err := handler.servicer.GetRuleSpec(service, law, request.Params.ReferenceDate.Time)
	if err != nil {
		handler.logger.Warn("rule spec", "status_code", 400, "err", err)
		return api.RuleSpecGet400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("get rule spec: %w", err)),
		}, nil
	}

	return api.RuleSpecGet200JSONResponse{
		RuleSpecResponseJSONResponse: api.RuleSpecResponseJSONResponse{
			Data: adapter.FromRuleSpec(spec),
		},
	}, nil
}
