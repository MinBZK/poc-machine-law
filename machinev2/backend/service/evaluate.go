package service

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	machinemodel "github.com/minbzk/poc-machine-law/machinev2/machine/model"
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

	var input map[string]any
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
		Path:            ToPathNode(result.Path),
	}, nil
}

func ToPathNode(path *machinemodel.PathNode) *model.PathNode {
	if path == nil {
		return nil
	}

	return &model.PathNode{
		Type:        path.Type,
		Name:        path.Name,
		Result:      path.Result,
		ResolveType: path.ResolveType,
		Required:    path.Required,
		Details:     path.Details,
		Children:    ToPathNodes(path.Children),
	}
}

func ToPathNodes(paths []*machinemodel.PathNode) []*model.PathNode {
	nodes := make([]*model.PathNode, 0, len(paths))

	for idx := range paths {
		nodes = append(nodes, ToPathNode(paths[idx]))
	}

	return nodes
}
