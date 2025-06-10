package model

// TypeSpec defines specifications for value types
type TypeSpec struct {
	Type      string   `json:"type,omitempty" yaml:"type,omitempty"`
	Unit      *string  `json:"unit,omitempty" yaml:"unit,omitempty"`
	Precision *int     `json:"precision,omitempty" yaml:"precision,omitempty"`
	Min       *float64 `json:"min,omitempty" yaml:"min,omitempty"`
	Max       *float64 `json:"max,omitempty" yaml:"max,omitempty"`
}
