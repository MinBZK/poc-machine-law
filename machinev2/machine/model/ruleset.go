package model

import (
	"github.com/google/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

type EvaluateActionResult struct {
	Value       any
	Type        string
	Description *string
	TypeSpec    *ruleresolver.TypeSpec
	Temporal    *ruleresolver.Temporal
}

type EvaluateResult struct {
	Input           map[string]any
	Output          map[string]EvaluateActionResult
	RequirementsMet bool
	Path            *PathNode
	MissingRequired bool
}

// RuleResult contains the results of a rule evaluation
type RuleResult struct {
	Input           map[string]any `json:"input"`
	Output          map[string]any `json:"output"`
	RequirementsMet bool           `json:"requirements_met"`
	Path            *PathNode      `json:"path,omitempty"`
	MissingRequired bool           `json:"missing_required"`
	RulespecUUID    uuid.UUID      `json:"rulespec_uuid"`
}

// NewRuleResult creates a new RuleResult from engine result
func NewRuleResult(result EvaluateResult, rulespecUUID uuid.UUID) *RuleResult {
	// Extract output
	output := make(map[string]any)
	for name, data := range result.Output {
		output[name] = data.Value
	}

	return &RuleResult{
		Output:          output,
		RequirementsMet: result.RequirementsMet,
		Input:           result.Input,
		RulespecUUID:    rulespecUUID,
		Path:            result.Path,
		MissingRequired: result.MissingRequired,
	}
}
