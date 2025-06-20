package httpservice

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/hashicorp/go-retryablehttp"
	"github.com/oapi-codegen/runtime/types"

	contexter "github.com/minbzk/poc-machine-law/machinev2/machine/internal/context"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/typespec"
	"github.com/minbzk/poc-machine-law/machinev2/machine/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/minbzk/poc-machine-law/machinev2/machine/service/ruleservice/httpservice/api"
	"github.com/minbzk/poc-machine-law/machinev2/machine/serviceresolver"
)

type HTTPService struct {
	logger         logging.Logger
	service        string
	client         *api.ClientWithResponses
	services       contexter.ServiceProvider
	svcresolver    serviceresolver.ServiceSpec
	standaloneMode bool
}

func New(logger logging.Logger, service string, services contexter.ServiceProvider, svcresolver serviceresolver.ServiceSpec, standaloneMode bool) (*HTTPService, error) {
	logger.Warningf(context.Background(), "creating http ruleservice: %s @ %s", service, svcresolver.Endpoint)

	retryClient := retryablehttp.NewClient()
	retryClient.RetryMax = 10

	client, err := api.NewClientWithResponses(fmt.Sprintf("%s/v0", svcresolver.Endpoint), api.WithHTTPClient(retryClient.StandardClient()))
	if err != nil {
		return nil, fmt.Errorf("new client with responses: %w", err)
	}

	return &HTTPService{
		logger:         logger,
		service:        service,
		client:         client,
		services:       services,
		svcresolver:    svcresolver,
		standaloneMode: standaloneMode,
	}, nil
}

// Evaluate implements ruleservice.RuleServicer.
func (h *HTTPService) Evaluate(
	ctx context.Context,
	law string,
	referenceDate string,
	parameters map[string]any,
	overwriteInput map[string]map[string]any,
	requestedOutput string,
	approved bool,
) (*model.RuleResult, error) {
	date, err := time.Parse("2006-01-02", referenceDate)
	if err != nil {
		return nil, fmt.Errorf("reference date parse: %w", err)
	}

	h.logger.Debugf(ctx, "sending evaluate to: %s", h.svcresolver.Name)

	body := api.EvaluateJSONRequestBody{
		Data: api.Evaluate{
			Approved:   &approved,
			Date:       &types.Date{Time: date},
			Input:      &overwriteInput,
			Law:        law,
			Output:     &requestedOutput,
			Parameters: &parameters,
			Service:    h.service,
		},
	}

	response, err := h.client.EvaluateWithResponse(ctx, body)

	if err != nil {
		return nil, fmt.Errorf("evaluate: %w", err)
	}

	if response.StatusCode() != http.StatusCreated {
		return nil, fmt.Errorf("evaluete incorrect status code: %s", string(response.Body))
	}

	rulespec, err := h.services.GetRuleResolver().GetRuleSpec(law, referenceDate, h.service)
	if err != nil {
		return nil, fmt.Errorf("get rule resolver: %w", err)
	}

	rs := &model.RuleResult{
		Input:           response.JSON201.Data.Input,
		Output:          toOutput(response.JSON201.Data.Output, rulespec.Properties.Output),
		RequirementsMet: response.JSON201.Data.RequirementsMet,
		Path:            toPathNode(response.JSON201.Data.Path),
		MissingRequired: response.JSON201.Data.MissingRequired,
		RulespecUUID:    response.JSON201.Data.RulespecId,
	}

	h.logger.Debugf(ctx, "evaluate done: %#+v", rs)

	return rs, nil
}

// Reset implements ruleservice.RuleServicer.
func (h *HTTPService) Reset(ctx context.Context) error {
	if h.standaloneMode {
		return nil
	}

	resp, err := h.client.ResetEngineWithResponse(ctx)
	if err != nil {
		return fmt.Errorf("reset engine: %w", err)
	}

	if resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("incorrect status code: %s", string(resp.Body))
	}

	return nil
}

// SetSourceDataFrame implements ruleservice.RuleServicer.
func (h *HTTPService) SetSourceDataFrame(ctx context.Context, table string, df model.DataFrame) error {
	if h.standaloneMode {
		return nil
	}

	body := api.SetSourceDataFrameJSONRequestBody{
		Data: api.DataFrame{
			Data:    df.ToRecords(),
			Service: h.service,
			Table:   table,
		},
	}

	resp, err := h.client.SetSourceDataFrameWithResponse(ctx, body)

	if err != nil {
		return fmt.Errorf("set source dataframe with response: %w", err)
	}

	if resp.StatusCode() != http.StatusCreated {
		return fmt.Errorf("incorrect status code: %s", string(resp.Body))
	}

	return nil
}

func toPathNode(pathNode api.PathNode) *model.PathNode {
	var resolveType string
	if pathNode.ResolveType != nil {
		resolveType = *pathNode.ResolveType
	}

	var result any
	if pathNode.Result != nil {
		result = *pathNode.Result
	}

	var required bool
	if pathNode.Required != nil {
		required = *pathNode.Required
	}

	var children []*model.PathNode
	if pathNode.Children != nil {
		children = toPathNodes(*pathNode.Children)
	}

	var details map[string]any
	if pathNode.Details != nil {
		details = *pathNode.Details
	}

	return &model.PathNode{
		Children:    children,
		Details:     details,
		Name:        pathNode.Name,
		Required:    required,
		ResolveType: resolveType,
		Result:      result,
		Type:        pathNode.Type,
	}
}

func toPathNodes(pathNodes []api.PathNode) []*model.PathNode {
	nodes := make([]*model.PathNode, 0, len(pathNodes))

	for idx := range pathNodes {
		nodes = append(nodes, toPathNode(pathNodes[idx]))
	}

	return nodes
}

// Parse any types to there correct types based on the spec / TODO move to correct module
func toOutput(values map[string]any, outputs []ruleresolver.OutputField) map[string]any {
	for _, output := range outputs {
		value, ok := values[output.Name]
		if !ok {
			continue
		}

		if output.TypeSpec != nil {
			values[output.Name] = typespec.Enforce(model.TypeSpec(*output.TypeSpec), value)
		}
	}

	return values
}
