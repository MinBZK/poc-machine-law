package service

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

// Evaluate implements Servicer.
func (service *Service) Evaluate(ctx context.Context, evaluate model.Evaluate) (model.EvaluateResponse, error) {
	var parameters map[string]any
	if evaluate.Parameters != nil {
		parameters = *evaluate.Parameters
	}

	var date string
	if evaluate.Date != nil {
		date = evaluate.Date.Format("2006-01-02")
	}

	var input map[string]map[string]any
	if evaluate.Input != nil {
		input = *evaluate.Input
	}

	var output string
	if evaluate.Output != nil {
		output = *evaluate.Output
	}

	approved := true
	if evaluate.Approved != nil {
		approved = *evaluate.Approved
	}

	result, err := service.service.Evaluate(ctx, evaluate.Service, evaluate.Law, parameters, date, input, output, approved)
	if err != nil {
		return model.EvaluateResponse{}, fmt.Errorf("evaluate: %w", err)
	}

	return model.EvaluateResponse{
		Input:           result.Input,
		MissingRequired: result.MissingRequired,
		Output:          result.Output,
		RequirementsMet: result.RequirementsMet,
		RulespecId:      result.RulespecUUID,
	}, nil
}
