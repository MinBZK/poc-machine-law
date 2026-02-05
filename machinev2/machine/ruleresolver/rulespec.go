package ruleresolver

import (
	"fmt"
	"time"

	// "github.com/goccy/go-yaml"
	"github.com/looplab/eventhorizon/uuid"
	"gopkg.in/yaml.v3"
)

// ServiceDefinition represents the root Dutch Government Service Definition
type RuleSpec struct {
	UUID           uuid.UUID     `yaml:"uuid"`
	Name           string        `yaml:"name"`
	Law            string        `yaml:"law"`
	LawType        *string       `yaml:"law_type,omitempty"`
	LegalCharacter *string       `yaml:"legal_character,omitempty"`
	DecisionType   *string       `yaml:"decision_type,omitempty"`
	Discoverable   *string       `yaml:"discoverable,omitempty"`
	ValidFrom      time.Time     `yaml:"valid_from"`
	Service        string        `yaml:"service"`
	Description    string        `yaml:"description"`
	References     []Reference   `yaml:"references,omitempty"`
	Properties     Properties    `yaml:"properties"`
	Requirements   []Requirement `yaml:"requirements,omitempty"`
	Actions        []Action      `yaml:"actions,omitempty"`
	Path           string
}

// Reference represents a legal reference
type Reference struct {
	Law     string `yaml:"law"`
	Article string `yaml:"article"`
	URL     string `yaml:"url"`
}

// Properties contains the main service properties
type Properties struct {
	Parameters  []ParameterField `yaml:"parameters,omitempty"`
	Sources     []SourceField    `yaml:"sources,omitempty"`
	Input       []InputField     `yaml:"input,omitempty"`
	Output      []OutputField    `yaml:"output,omitempty"`
	Definitions map[string]any   `yaml:"definitions,omitempty"`
	Applies     []Apply          `yaml:"applies,omitempty"`
}

// Apply defines application rules for cases and events
type Apply struct {
	Name      string   `yaml:"name"`
	Aggregate string   `yaml:"aggregate"`
	Events    []Event  `yaml:"events,omitempty"`
	Update    []Update `yaml:"update,omitempty"`
}

// Event defines an event with type and filter
type Event struct {
	Type   string         `yaml:"type"`
	Filter map[string]any `yaml:"filter,omitempty"`
}

// Update defines update methods and mappings
type Update struct {
	Method  string            `yaml:"method"`
	Mapping map[string]string `yaml:"mapping,omitempty"`
}

// BaseField contains common field properties
type BaseField struct {
	Name        string    `yaml:"name"`
	Description string    `yaml:"description"`
	Type        string    `yaml:"type"`
	TypeSpec    *TypeSpec `yaml:"type_spec,omitempty"`
	Temporal    *Temporal `yaml:"temporal,omitempty"`
	Required    *bool     `yaml:"required,omitempty"`
}

// TypeSpec defines type specifications
type TypeSpec struct {
	Type      string   `yaml:"type,omitempty"`
	Unit      *string  `yaml:"unit,omitempty"`
	Precision *int     `yaml:"precision,omitempty"`
	Min       *float64 `yaml:"min,omitempty"`
	Max       *float64 `yaml:"max,omitempty"`
}

func (ts TypeSpec) ToMap() map[string]any {
	m := map[string]any{
		"type": ts.Type,
	}

	if ts.Unit != nil {
		m["unit"] = *ts.Unit
	}
	if ts.Precision != nil {
		m["precision"] = *ts.Precision
	}
	if ts.Min != nil {
		m["min"] = *ts.Min
	}
	if ts.Max != nil {
		m["max"] = *ts.Max
	}

	return m
}

// Temporal defines temporal properties
type Temporal struct {
	Type           string  `yaml:"type"`
	PeriodType     *string `yaml:"period_type,omitempty"`
	Reference      any     `yaml:"reference,omitempty"` // Can be string or VariableReference
	ImmutableAfter *string `yaml:"immutable_after,omitempty"`
}

// ParameterField extends BaseField for parameters
type ParameterField struct {
	BaseField `yaml:",inline"`
}

// SourceField extends BaseField for sources
type SourceField struct {
	BaseField        `yaml:",inline"`
	SourceReference  *SourceReference  `yaml:"source_reference,omitempty"`
	ServiceReference *ServiceReference `yaml:"service_reference,omitempty"`
}

// InputField extends BaseField for input
type InputField struct {
	BaseField        `yaml:",inline"`
	ServiceReference ServiceReference `yaml:"service_reference"`
}

// OutputField extends BaseField for output
type OutputField struct {
	BaseField        `yaml:",inline"`
	CitizenRelevance string `yaml:"citizen_relevance"`
}

type Field struct {
	Input  *InputField
	Source *SourceField
}

func (f Field) GetBase() BaseField {
	if f.Input != nil {
		return f.Input.BaseField
	} else if f.Source != nil {
		return f.Source.BaseField
	}

	return BaseField{}
}

// SourceReference defines how to reference a data source
type SourceReference struct {
	SourceType      string        `yaml:"source_type,omitempty"`
	Table           string        `yaml:"table,omitempty"`
	Field           *string       `yaml:"field,omitempty"`
	Fields          *[]string     `yaml:"fields,omitempty"`
	SelectOn        []SelectField `yaml:"select_on,omitempty"`
	WalletAttribute *string       `yaml:"wallet_attribute,omitempty"`
}

// SelectField defines selection criteria
type SelectField struct {
	Name        string      `yaml:"name"`
	Description string      `yaml:"description"`
	Type        string      `yaml:"type"`
	Value       ActionValue `yaml:"value"` // Can be string or ValueOperation
}

// ServiceReference defines a reference to another service
type ServiceReference struct {
	Service    string      `yaml:"service"`
	Field      string      `yaml:"field"`
	Law        string      `yaml:"law"`
	Parameters []Parameter `yaml:"parameters,omitempty"`
}

// Parameter defines a service parameter
type Parameter struct {
	Name      string `yaml:"name"`
	Reference string `yaml:"reference"`
}

// Action defines an action to be performed
type Action struct {
	Output     string        `yaml:"output"`
	Value      *ActionValue  `yaml:"value,omitempty"`
	Operation  *string       `yaml:"operation,omitempty"`
	Subject    *string       `yaml:"subject,omitempty"`
	Unit       *string       `yaml:"unit,omitempty"`
	Combine    *string       `yaml:"combine,omitempty"`
	Values     *ActionValues `yaml:"values,omitempty"`
	Conditions []Condition   `yaml:"conditions,omitempty"`
}

func (a Action) IsEmpty() bool {
	return a.Output == "" &&
		a.Value == nil &&
		a.Operation == nil &&
		a.Subject == nil &&
		a.Unit == nil &&
		a.Combine == nil &&
		a.Values == nil &&
		a.Conditions == nil
}

func (a Action) GetValue() any {
	if a.Value != nil {
		return a.Value.GetValue()
	} else if a.Values != nil {
		return a.Values.GetValue()
	}

	return nil
}

// ActionValue represents a value in an operation
type ActionValues struct {
	// This can be a variable reference, number, boolean, null, string, or nested operation
	// We'll use any and handle the unmarshaling appropriately
	Value        *any
	ActionValues *[]ActionValue
}

func (avs *ActionValues) GetValue() any {
	if avs.ActionValues != nil {
		avss := make([]any, 0, len(*avs.ActionValues))
		for _, av := range *avs.ActionValues {
			avss = append(avss, av.GetValue())
		}

		return avss
	} else if avs.Value != nil {
		return *avs.Value
	}

	return nil
}

// ActionValue represents a value in an operation
type ActionValue struct {
	// This can be a variable reference, number, boolean, null, string, or nested operation
	// We'll use any and handle the unmarshaling appropriately
	Value  *any
	Action *Action
}

func (av *ActionValue) GetValue() any {
	if av.Action != nil {
		return av.Action.GetValue()
	} else if av.Value != nil {
		return *av.Value
	}

	return nil
}

// UnmarshalYAML custom unmarshaler for OperationValue
func (ov *ActionValue) UnmarshalYAML(unmarshal func(any) error) error {
	var action Action
	if err := unmarshal(&action); err == nil {
		if !action.IsEmpty() {
			ov.Action = &action
			return nil
		}
	}

	var actions []Action
	if err := unmarshal(&actions); err == nil && len(actions) > 0 {
		action := actions[0]
		if !action.IsEmpty() {
			ov.Action = &action
			return nil
		}
	}

	// Try other types
	var val any
	if err := unmarshal(&val); err != nil {
		return err
	}

	ov.Value = &val
	return nil
}

// MarshalYAML custom marshaler for OperationValue
func (ov *ActionValue) MarshalYAML() ([]byte, error) {
	if ov.Action != nil {
		return yaml.Marshal(ov.Action)
	} else if ov.Value != nil {
		return yaml.Marshal(ov.Value)
	}

	return nil, fmt.Errorf("action value not set")
}

func (ov *ActionValues) UnmarshalYAML(unmarshal func(any) error) error {
	// Try to unmarshal as Operation first
	var req []ActionValue
	if err := unmarshal(&req); err == nil {
		ov.ActionValues = &req
		return nil
	}

	// Try other types
	var value any
	if err := unmarshal(&value); err != nil {
		return err
	}

	ov.Value = &value

	return nil
}

// MarshalYAML custom marshaler for OperationValue
func (ov *ActionValues) MarshalYAML() ([]byte, error) {
	if ov.ActionValues != nil {
		return yaml.Marshal(ov.ActionValues)
	}

	return yaml.Marshal(ov.Value)
}

// Condition defines a conditional logic
type Condition struct {
	Test *Action      `yaml:"test"`
	Then *ActionValue `yaml:"then"`
	Else *ActionValue `yaml:"else,omitempty"`
}

// Requirement defines requirements with logical operations
type Requirement struct {
	// Logical operators - only one should be set
	All *[]ActionRequirement `yaml:"all,omitempty"`
	Or  *[]ActionRequirement `yaml:"or,omitempty"`
	// Direct action requirement (when not wrapped in All/Or)
	Action *Action `yaml:"-"`
}

// UnmarshalYAML custom unmarshaler for Requirement
func (r *Requirement) UnmarshalYAML(unmarshal func(any) error) error {
	// First try to unmarshal as a structured requirement with all/or
	type requirementAlias Requirement
	var req requirementAlias
	if err := unmarshal(&req); err == nil {
		if req.All != nil || req.Or != nil {
			*r = Requirement(req)
			return nil
		}
	}

	// If not All/Or, try to unmarshal as a direct action
	var action Action
	if err := unmarshal(&action); err != nil {
		return err
	}

	r.Action = &action
	return nil
}

type ActionRequirement struct {
	Requirement *Requirement
	Action      *Action
}

// UnmarshalYAML custom unmarshaler for OperationValue
func (ov *ActionRequirement) UnmarshalYAML(unmarshal func(any) error) error {
	// Try to unmarshal as Operation first
	var req Requirement

	if err := unmarshal(&req); err == nil {
		if req.All != nil || req.Or != nil {
			ov.Requirement = &req
			return nil
		}
	}

	// Try other types
	var action Action
	if err := unmarshal(&action); err != nil {
		return err
	}

	ov.Action = &action

	return nil
}

// MarshalYAML custom marshaler for OperationValue
func (ov *ActionRequirement) MarshalYAML() ([]byte, error) {
	if ov.Requirement != nil {
		return yaml.Marshal(ov.Requirement)
	}
	return yaml.Marshal(ov.Action)
}

// Enums for type safety

// LawType enum
type LawType string

const (
	LawTypeFormeleWet LawType = "FORMELE_WET"
)

// LegalCharacter enum
type LegalCharacter string

const (
	LegalCharacterBeschikking                 LegalCharacter = "BESCHIKKING"
	LegalCharacterBesluitVanAlgemeneStrekking LegalCharacter = "BESLUIT_VAN_ALGEMENE_STREKKING"
)

// DecisionType enum
type DecisionType string

const (
	DecisionTypeToekenning                    DecisionType = "TOEKENNING"
	DecisionTypeAlgemeenVerbindendVoorschrift DecisionType = "ALGEMEEN_VERBINDEND_VOORSCHRIFT"
	DecisionTypeBeleidsregel                  DecisionType = "BELEIDSREGEL"
	DecisionTypeVoorbereidingsbesluit         DecisionType = "VOORBEREIDINGSBESLUIT"
	DecisionTypeAndereHandeling               DecisionType = "ANDERE_HANDELING"
	DecisionTypeAanslag                       DecisionType = "AANSLAG"
)

// Discoverable enum
type Discoverable string

const (
	DiscoverableCitizen Discoverable = "CITIZEN"
)

// FieldType enum
type FieldType string

const (
	FieldTypeString  FieldType = "string"
	FieldTypeNumber  FieldType = "number"
	FieldTypeBoolean FieldType = "boolean"
	FieldTypeAmount  FieldType = "amount"
	FieldTypeObject  FieldType = "object"
	FieldTypeArray   FieldType = "array"
	FieldTypeDate    FieldType = "date"
)

// Unit enum
type Unit string

const (
	UnitEurocent Unit = "eurocent"
	UnitYears    Unit = "years"
	UnitWeeks    Unit = "weeks"
	UnitMonths   Unit = "months"
)

// TemporalType enum
type TemporalType string

const (
	TemporalTypePeriod      TemporalType = "period"
	TemporalTypePointInTime TemporalType = "point_in_time"
)

// PeriodType enum
type PeriodType string

const (
	PeriodTypeYear       PeriodType = "year"
	PeriodTypeMonth      PeriodType = "month"
	PeriodTypeContinuous PeriodType = "continuous"
)

// OperationType enum
type OperationType string

const (
	OperationAdd            OperationType = "ADD"
	OperationSubtract       OperationType = "SUBTRACT"
	OperationMultiply       OperationType = "MULTIPLY"
	OperationDivide         OperationType = "DIVIDE"
	OperationMin            OperationType = "MIN"
	OperationMax            OperationType = "MAX"
	OperationAnd            OperationType = "AND"
	OperationOr             OperationType = "OR"
	OperationNot            OperationType = "NOT"
	OperationEquals         OperationType = "EQUALS"
	OperationNotEquals      OperationType = "NOT_EQUALS"
	OperationGreaterThan    OperationType = "GREATER_THAN"
	OperationLessThan       OperationType = "LESS_THAN"
	OperationGreaterOrEqual OperationType = "GREATER_OR_EQUAL"
	OperationLessOrEqual    OperationType = "LESS_OR_EQUAL"
	OperationIn             OperationType = "IN"
	OperationNotIn          OperationType = "NOT_IN"
	OperationConcat         OperationType = "CONCAT"
	OperationIf             OperationType = "IF"
	OperationForeach        OperationType = "FOREACH"
	OperationSubtractDate   OperationType = "SUBTRACT_DATE"
	OperationIsNull         OperationType = "IS_NULL"
	OperationNotNull        OperationType = "NOT_NULL"
)

// Helper functions for validation

// IsValidUUID checks if a string is a valid UUID v4
func IsValidUUID(uuid string) bool {
	// Basic regex check - you might want to use a proper UUID library
	return len(uuid) == 36 && uuid[8] == '-' && uuid[13] == '-' && uuid[18] == '-' && uuid[23] == '-'
}

// IsValidDate checks if a string is a valid date in YYYY-MM-DD format
func IsValidDate(date string) bool {
	_, err := time.Parse("2006-01-02", date)
	return err == nil
}

// IsValidVariableReference checks if a string is a valid variable reference
func IsValidVariableReference(ref string) bool {
	if len(ref) < 2 || ref[0] != '$' {
		return false
	}
	// Additional validation can be added here
	return true
}
