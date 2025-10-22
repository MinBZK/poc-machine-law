package handler

import (
	"context"
	"fmt"
	"time"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

// Evaluate implements api.StrictServerInterface.
func (handler *Handler) Evaluate(ctx context.Context, request api.EvaluateRequestObject) (api.EvaluateResponseObject, error) {
	handler.logger.Debug("evaluate", "params", request.Body.Data)

	var date *time.Time
	if request.Body.Data.Date != nil {
		date = &request.Body.Data.Date.Time
	}

	result, err := handler.servicer.Evaluate(ctx, model.Evaluate{
		Law:        request.Body.Data.Law,
		Service:    request.Body.Data.Service,
		Parameters: request.Body.Data.Parameters,
		Date:       date,
		Input:      request.Body.Data.Input,
		Output:     request.Body.Data.Output,
		Approved:   request.Body.Data.Approved,
	})

	if err != nil {
		return api.Evaluate400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("evaluate: %w", err))}, nil
	}

	return api.Evaluate201JSONResponse{
		ResponseEvaluateJSONResponse: api.ResponseEvaluateJSONResponse{
			Data: api.ResponseEvaluateSchema{
				Input:           result.Input,
				MissingRequired: result.MissingRequired,
				Output:          result.Output,
				RequirementsMet: result.RequirementsMet,
				RulespecId:      result.RulespecId,
				Path:            *adapter.FromPathNode(result.Path),
			},
		},
	}, nil
}
