package main

// Input structures matching the YAML format
type Requirements struct {
	All []Requirement `yaml:"all,omitempty"`
}

type Requirement struct {
	Or        []Requirement `yaml:"or,omitempty"`
	Subject   string        `yaml:"subject"`
	Operation string        `yaml:"operation"`
	Value     any           `yaml:"value"`
	Values    []any         `yaml:"values,omitempty"` // cast to types: int, string or objects: Requirement
}

type Action struct {
	Output     string            `yaml:"output"`
	Value      any               `yaml:"value,omitempty"`
	Values     []any             `yaml:"values,omitempty"`
	Operation  string            `yaml:"operation,omitempty"`
	Conditions []ActionCondition `yaml:"conditions,omitempty"`
	Reference  *string           `yaml:"reference,omitempty"`
}

type ActionCondition struct {
	Test ActionConditionRequirement `yaml:"test"`
	Then any                        `yaml:"then"`           // cast to either types: int, string or object: ActionConditionRequirement
	Else any                        `yaml:"else,omitempty"` // cast to either types: int, string or object: ActionConditionRequirement
}

type ActionConditionRequirement struct {
	Operation  string
	Subject    string
	Conditions []ActionCondition
	Value      any
	Values     any // cast to types: int, string or object: Requirement
}

type RuleSet struct {
	UUID        string `yaml:"uuid"`
	Name        string `yaml:"name"`
	Subject     string
	Law         string `yaml:"law"`
	ValidFrom   string `yaml:"valid_from"`
	Service     string `yaml:"service"`
	Description string `yaml:"description"`
	Properties  struct {
		Output      []Property     `yaml:"output"`
		Input       []Property     `yaml:"input"`
		Definitions map[string]any `yaml:"definitions"` // Definitions can be improved by adding context and a user friendly name
	} `yaml:"properties"`
	Requirements   []Requirements `yaml:"requirements"`
	Actions        []Action       `yaml:"actions"`
	OutputMappings map[string]struct {
		RuleName    string
		Description string
	}
}

type Property struct {
	Name        string `yaml:"name"`
	Description string `yaml:"description"`
	Type        string `yaml:"type"`
	TypeSpec    *struct {
		Unit      string `yaml:"unit"`
		Precision int    `yaml:"precision"`
		Min       int    `yaml:"min"`
	} `yaml:"type_spec"`
	Temporal struct {
		Type          string `yaml:"type"`
		PeriodType    string `yaml:"period_type"`
		ReferenceDate string `yaml:"reference_date"`
	} `yaml:"temporal"`
	ServiceReference struct {
		Service string `yaml:"service"`
		Field   string `yaml:"field"`
		Law     string `yaml:"law"`
	} `yaml:"service_reference"`
}
