package ruleresolver_test

import (
	"fmt"
	"os"
	"testing"

	"github.com/gdexlab/go-render/render"
	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
	"github.com/stretchr/testify/require"

	// "github.com/goccy/go-yaml"
	"gopkg.in/yaml.v3"
)

func TestDecodeLaw(_ *testing.T) {
	data, err := os.ReadFile("test.yaml")
	if err != nil {
		fmt.Printf("Error reading file: %v\n", err)
	}

	fmt.Printf("string(data): %v\n", string(data))

	rule := ruleresolver.RuleSpec{}
	if err := yaml.Unmarshal(data, &rule); err != nil {
		fmt.Printf("Error parsing YAML from: %v\n", err)
	}

	render.Render(rule)
}

func TestRuleResolverActionValueUnmarshalling(t *testing.T) {
	data := `
sources:
  - name: "RESIDENCE_INSURED_YEARS"
    description: "Aantal verzekerde jaren voor AOW-opbouw op basis van woonperiodes"
    type: "number"
    type_spec:
      precision: 2
      min: 0
      max: 50
    temporal:
      type: "period"
      period_type: "continuous"
    source_reference:
      table: "verzekerde_tijdvakken"
      field: "woonperiodes"
      select_on:
        - name: "bsn"
          description: "Burgerservicenummer van de persoon"
          type: "string"
          value: "$BSN"
`

	var av struct {
		Sources []ruleresolver.SourceField `yaml:"sources"`
	}
	err := yaml.Unmarshal([]byte(data), &av)
	require.NoError(t, err)

	render.Render(av)
}

func TestRuleResolverDefinitions(t *testing.T) {
	data := `

properties:
  definitions:
    MINIMUM_AGE: 18
    BASE_AMOUNT_SINGLE_21_PLUS: 108900  # 1089 euro
    BASE_AMOUNT_PARTNERS_21_PLUS: 155600 # 1556 euro
    VALID_RESIDENCE_PERMITS:
      - "PERMANENT"
      - "EU"
      - "FAMILY_REUNIFICATION"
    ASSET_LIMIT_SINGLE: 750000  # 7500 euro
    ASSET_LIMIT_PARTNER: 1500000 # 15000 euro
    KOSTENDELERSNORM_FACTORS:
      1: 1.00
      2: 0.50
      3: 0.43
      4: 0.40
`

	var av struct {
		Properties ruleresolver.Properties `yaml:"properties"`
	}

	err := yaml.Unmarshal([]byte(data), &av)
	require.NoError(t, err)

	render.Render(av)
}
