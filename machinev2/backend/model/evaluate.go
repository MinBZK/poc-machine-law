package model

import (
	"time"

	"github.com/google/uuid"
)

type Evaluate struct {
	// Approved only use approved claims, default to true
	Approved *bool

	// EffectiveDate Can be used to overwrite the date used by the service
	EffectiveDate *time.Time
	ReferenceDate *time.Time
	Input         *map[string]any

	// Law Specify the law that needs to be executed
	Law string

	// Output specify a requested output value
	Output     *string
	Parameters *map[string]any

	// Service Specify the service that needs to be executed
	Service string
}

type EvaluateResponse struct {
	Input map[string]any

	// MissingRequired Will be true when a required value is missing
	MissingRequired bool
	Output          map[string]any
	Path            *PathNode

	// RequirementsMet Will be true when all requirements where met
	RequirementsMet bool

	// RulespecId Identifier of the rulespec
	RulespecId uuid.UUID
}

// PathNode represents a node in the evaluation path
type PathNode struct {
	Type        string
	Name        string
	Result      any
	ResolveType string
	Required    bool
	Details     map[string]any
	Children    []*PathNode
}
