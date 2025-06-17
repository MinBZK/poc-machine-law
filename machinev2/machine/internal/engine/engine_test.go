package engine

import (
	"testing"

	"github.com/minbzk/poc-machine-law/machinev2/machine/ruleresolver"
)

func TestAnalyzeDependencies(t *testing.T) {
	tests := []struct {
		name     string
		action   ruleresolver.Action
		expected map[string]struct{}
	}{
		{
			name: "empty action",
			action: ruleresolver.Action{
				Output: "test_output",
			},
			expected: map[string]struct{}{},
		},
		{
			name: "simple eligibility check (based on participatiewet)",
			action: ruleresolver.Action{
				Output: "is_eligible",
				Value: &ruleresolver.ActionValue{
					Value: anyPtr("$meets_age_requirement"),
				},
			},
			expected: map[string]struct{}{
				"meets_age_requirement": {},
			},
		},
		{
			name: "mixed case dependency - should ignore uppercase",
			action: ruleresolver.Action{
				Output: "test_output",
				Value: &ruleresolver.ActionValue{
					Value: anyPtr("$DependentOutput"),
				},
			},
			expected: map[string]struct{}{},
		},
		{
			name: "basic income calculation (zorgtoeslag pattern)",
			action: ruleresolver.Action{
				Output: "toetsingsinkomen",
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("ADD"),
						Values: &ruleresolver.ActionValues{
							ActionValues: &[]ruleresolver.ActionValue{
								{Value: anyPtr("$inkomen_persoon")},
								{Value: anyPtr("$inkomen_partner")},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"inkomen_persoon": {},
				"inkomen_partner": {},
			},
		},
		{
			name: "partner-dependent logic (realistic zorgtoeslag)",
			action: ruleresolver.Action{
				Output: "standaardpremie",
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("IF"),
						Conditions: []ruleresolver.Condition{
							{
								Test: &ruleresolver.Action{
									Operation: stringPtr("EQUALS"),
									Subject:   stringPtr("$heeft_partner"),
									Value: &ruleresolver.ActionValue{
										Value: anyPtr(true),
									},
								},
								Then: &ruleresolver.ActionValue{
									Value: anyPtr("$standaardpremie_partners"),
								},
								Else: &ruleresolver.ActionValue{
									Value: anyPtr("$standaardpremie_alleenstaand"),
								},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"heeft_partner":                {},
				"standaardpremie_partners":     {},
				"standaardpremie_alleenstaand": {},
			},
		},
		{
			name: "kinderopvang array processing",
			action: ruleresolver.Action{
				Output:    "yearly_childcare_allowance",
				Operation: stringPtr("FOREACH"),
				Subject:   stringPtr("$children_registered"),
				Combine:   stringPtr("ADD"),
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("MULTIPLY"),
						Values: &ruleresolver.ActionValues{
							ActionValues: &[]ruleresolver.ActionValue{
								{Value: anyPtr("$hours_per_child")},
								{Value: anyPtr("$hourly_rate")},
								{Value: anyPtr("$percentage_covered")},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"children_registered": {},
				"hours_per_child":     {},
				"hourly_rate":         {},
				"percentage_covered":  {},
			},
		},
		{
			name: "complex zorgtoeslag calculation (7-level nesting)",
			action: ruleresolver.Action{
				Output: "hoogte_toeslag",
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("IF"),
						Conditions: []ruleresolver.Condition{
							{
								Test: &ruleresolver.Action{
									Operation: stringPtr("GREATER_THAN"),
									Subject:   stringPtr("$toetsingsinkomen"),
									Value: &ruleresolver.ActionValue{
										Value: anyPtr("$inkomensgrens"),
									},
								},
								Then: &ruleresolver.ActionValue{
									Value: anyPtr(0),
								},
								Else: &ruleresolver.ActionValue{
									Action: &ruleresolver.Action{
										Operation: stringPtr("IF"),
										Conditions: []ruleresolver.Condition{
											{
												Test: &ruleresolver.Action{
													Operation: stringPtr("GREATER_THAN"),
													Subject:   stringPtr("$vermogen"),
													Value: &ruleresolver.ActionValue{
														Value: anyPtr("$vermogensgrens"),
													},
												},
												Then: &ruleresolver.ActionValue{
													Value: anyPtr(0),
												},
												Else: &ruleresolver.ActionValue{
													Action: &ruleresolver.Action{
														Operation: stringPtr("SUBTRACT"),
														Values: &ruleresolver.ActionValues{
															ActionValues: &[]ruleresolver.ActionValue{
																{Value: anyPtr("$standaardpremie")},
																{
																	Action: &ruleresolver.Action{
																		Operation: stringPtr("MULTIPLY"),
																		Values: &ruleresolver.ActionValues{
																			ActionValues: &[]ruleresolver.ActionValue{
																				{Value: anyPtr("$eigen_bijdrage_percentage")},
																				{Value: anyPtr("$toetsingsinkomen_boven_drempel")},
																			},
																		},
																	},
																},
															},
														},
													},
												},
											},
										},
									},
								},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"toetsingsinkomen":               {},
				"inkomensgrens":                  {},
				"vermogen":                       {},
				"vermogensgrens":                 {},
				"standaardpremie":                {},
				"eigen_bijdrage_percentage":      {},
				"toetsingsinkomen_boven_drempel": {},
			},
		},
		{
			name: "huurtoeslag household calculation",
			action: ruleresolver.Action{
				Output:    "total_household_income",
				Operation: stringPtr("FOREACH"),
				Subject:   stringPtr("$household_members"),
				Combine:   stringPtr("ADD"),
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("IF"),
						Conditions: []ruleresolver.Condition{
							{
								Test: &ruleresolver.Action{
									Operation: stringPtr("GREATER_OR_EQUAL"),
									Subject:   stringPtr("$member_age"),
									Value: &ruleresolver.ActionValue{
										Value: anyPtr(21),
									},
								},
								Then: &ruleresolver.ActionValue{
									Value: anyPtr("$member_income"),
								},
								Else: &ruleresolver.ActionValue{
									Value: anyPtr(0),
								},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"household_members": {},
				"member_age":        {},
				"member_income":     {},
			},
		},
		{
			name: "bijstand asset test with complex conditions",
			action: ruleresolver.Action{
				Output: "vermogen_uitsluiting",
				Value: &ruleresolver.ActionValue{
					Action: &ruleresolver.Action{
						Operation: stringPtr("OR"),
						Values: &ruleresolver.ActionValues{
							ActionValues: &[]ruleresolver.ActionValue{
								{
									Action: &ruleresolver.Action{
										Operation: stringPtr("GREATER_THAN"),
										Subject:   stringPtr("$totaal_vermogen"),
										Value: &ruleresolver.ActionValue{
											Value: anyPtr("$vermogensgrens_alleenstaand"),
										},
									},
								},
								{
									Action: &ruleresolver.Action{
										Operation: stringPtr("AND"),
										Values: &ruleresolver.ActionValues{
											ActionValues: &[]ruleresolver.ActionValue{
												{Value: anyPtr("$heeft_partner")},
												{
													Action: &ruleresolver.Action{
														Operation: stringPtr("GREATER_THAN"),
														Subject:   stringPtr("$totaal_vermogen"),
														Value: &ruleresolver.ActionValue{
															Value: anyPtr("$vermogensgrens_partners"),
														},
													},
												},
											},
										},
									},
								},
								{Value: anyPtr("$heeft_schuldsanering")},
							},
						},
					},
				},
			},
			expected: map[string]struct{}{
				"totaal_vermogen":             {},
				"vermogensgrens_alleenstaand": {},
				"heeft_partner":               {},
				"vermogensgrens_partners":     {},
				"heeft_schuldsanering":        {},
			},
		},
		{
			name: "non-dollar prefixed strings ignored",
			action: ruleresolver.Action{
				Output: "test_output",
				Value: &ruleresolver.ActionValue{
					Value: anyPtr("regular_string"),
				},
			},
			expected: map[string]struct{}{},
		},
		{
			name: "map with realistic law references",
			action: ruleresolver.Action{
				Output: "calculation_details",
				Value: &ruleresolver.ActionValue{
					Value: anyPtr(map[string]any{
						"basis_bedrag": "$standaardpremie",
						"inkomen": map[string]any{
							"persoon": "$inkomen_persoon",
							"partner": "$inkomen_partner",
							"totaal":  "$toetsingsinkomen",
						},
						"aftrek": "$eigen_bijdrage",
					}),
				},
			},
			expected: map[string]struct{}{
				"standaardpremie":  {},
				"inkomen_persoon":  {},
				"inkomen_partner":  {},
				"toetsingsinkomen": {},
				"eigen_bijdrage":   {},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := analyzeDependencies(tt.action)

			if len(result) != len(tt.expected) {
				t.Errorf("expected %d dependencies, got %d", len(tt.expected), len(result))
			}

			for expectedDep := range tt.expected {
				if _, found := result[expectedDep]; !found {
					t.Errorf("expected dependency %q not found in result", expectedDep)
				}
			}

			for actualDep := range result {
				if _, expected := tt.expected[actualDep]; !expected {
					t.Errorf("unexpected dependency %q found in result", actualDep)
				}
			}
		})
	}
}

// Helper functions for creating pointers to primitive types
func stringPtr(s string) *string {
	return &s
}

func anyPtr(v any) *any {
	return &v
}

func BenchmarkAnalyzeDependencies(b *testing.B) {
	// Level 1: Simple eligibility check (2 dependencies)
	// Based on participatiewet simple boolean logic
	simpleEligibilityAction := ruleresolver.Action{
		Output: "is_eligible",
		Value: &ruleresolver.ActionValue{
			Action: &ruleresolver.Action{
				Operation: stringPtr("AND"),
				Values: &ruleresolver.ActionValues{
					ActionValues: &[]ruleresolver.ActionValue{
						{Value: anyPtr("$meets_age_requirement")},
						{Value: anyPtr("$has_valid_residence")},
					},
				},
			},
		},
	}

	// Level 2: Basic income calculation (4 dependencies)
	// Based on zorgtoeslag toetsingsinkomen pattern
	basicIncomeAction := ruleresolver.Action{
		Output: "toetsingsinkomen",
		Value: &ruleresolver.ActionValue{
			Action: &ruleresolver.Action{
				Operation: stringPtr("ADD"),
				Values: &ruleresolver.ActionValues{
					ActionValues: &[]ruleresolver.ActionValue{
						{Value: anyPtr("$inkomen_persoon")},
						{Value: anyPtr("$inkomen_partner")},
						{Value: anyPtr("$inkomen_overig")},
						{Value: anyPtr("$vermogensbijtelling")},
					},
				},
			},
		},
	}

	// Level 3: Partner-dependent calculation (8 dependencies)
	// Based on realistic zorgtoeslag standaardpremie logic
	partnerDependentAction := ruleresolver.Action{
		Output: "hoogte_toeslag_basis",
		Value: &ruleresolver.ActionValue{
			Action: &ruleresolver.Action{
				Operation: stringPtr("IF"),
				Conditions: []ruleresolver.Condition{
					{
						Test: &ruleresolver.Action{
							Operation: stringPtr("AND"),
							Values: &ruleresolver.ActionValues{
								ActionValues: &[]ruleresolver.ActionValue{
									{Value: anyPtr("$heeft_partner")},
									{
										Action: &ruleresolver.Action{
											Operation: stringPtr("LESS_OR_EQUAL"),
											Subject:   stringPtr("$toetsingsinkomen"),
											Value: &ruleresolver.ActionValue{
												Value: anyPtr("$inkomensgrens_partners"),
											},
										},
									},
								},
							},
						},
						Then: &ruleresolver.ActionValue{
							Value: anyPtr("$standaardpremie_partners"),
						},
						Else: &ruleresolver.ActionValue{
							Action: &ruleresolver.Action{
								Operation: stringPtr("IF"),
								Conditions: []ruleresolver.Condition{
									{
										Test: &ruleresolver.Action{
											Operation: stringPtr("LESS_OR_EQUAL"),
											Subject:   stringPtr("$toetsingsinkomen"),
											Value: &ruleresolver.ActionValue{
												Value: anyPtr("$inkomensgrens_alleenstaand"),
											},
										},
										Then: &ruleresolver.ActionValue{
											Value: anyPtr("$standaardpremie_alleenstaand"),
										},
										Else: &ruleresolver.ActionValue{
											Value: anyPtr(0),
										},
									},
								},
							},
						},
					},
				},
			},
		},
	}

	// Level 4: Kinderopvang array processing (12 dependencies)
	// Based on realistic childcare allowance calculation
	kinderopvangArrayAction := ruleresolver.Action{
		Output:    "yearly_childcare_allowance",
		Operation: stringPtr("FOREACH"),
		Subject:   stringPtr("$children_registered"),
		Combine:   stringPtr("ADD"),
		Value: &ruleresolver.ActionValue{
			Action: &ruleresolver.Action{
				Operation: stringPtr("IF"),
				Conditions: []ruleresolver.Condition{
					{
						Test: &ruleresolver.Action{
							Operation: stringPtr("AND"),
							Values: &ruleresolver.ActionValues{
								ActionValues: &[]ruleresolver.ActionValue{
									{
										Action: &ruleresolver.Action{
											Operation: stringPtr("GREATER_OR_EQUAL"),
											Subject:   stringPtr("$child_age"),
											Value: &ruleresolver.ActionValue{
												Value: anyPtr(0),
											},
										},
									},
									{
										Action: &ruleresolver.Action{
											Operation: stringPtr("LESS_THAN"),
											Subject:   stringPtr("$child_age"),
											Value: &ruleresolver.ActionValue{
												Value: anyPtr("$max_age_childcare"),
											},
										},
									},
									{Value: anyPtr("$child_eligible_daycare")},
								},
							},
						},
						Then: &ruleresolver.ActionValue{
							Action: &ruleresolver.Action{
								Operation: stringPtr("MULTIPLY"),
								Values: &ruleresolver.ActionValues{
									ActionValues: &[]ruleresolver.ActionValue{
										{Value: anyPtr("$hours_per_child")},
										{Value: anyPtr("$hourly_rate")},
										{Value: anyPtr("$percentage_covered")},
										{Value: anyPtr("$income_adjustment_factor")},
									},
								},
							},
						},
						Else: &ruleresolver.ActionValue{
							Value: anyPtr(0),
						},
					},
				},
			},
		},
	}

	// Level 5: Maximum complexity zorgtoeslag (15+ dependencies, 7-level nesting)
	// Based on actual TOESLAGEN-2024-01-01.yaml structure
	maxComplexityZorgtoeslagAction := ruleresolver.Action{
		Output: "hoogte_toeslag_definitief",
		Value: &ruleresolver.ActionValue{
			Action: &ruleresolver.Action{
				Operation: stringPtr("IF"),
				Conditions: []ruleresolver.Condition{
					{
						Test: &ruleresolver.Action{
							Operation: stringPtr("OR"),
							Values: &ruleresolver.ActionValues{
								ActionValues: &[]ruleresolver.ActionValue{
									{Value: anyPtr("$uitgesloten_woning")},
									{Value: anyPtr("$uitgesloten_vermogen")},
									{Value: anyPtr("$uitgesloten_inkomen")},
									{Value: anyPtr("$uitgesloten_leeftijd")},
								},
							},
						},
						Then: &ruleresolver.ActionValue{
							Value: anyPtr(0),
						},
						Else: &ruleresolver.ActionValue{
							Action: &ruleresolver.Action{
								Operation: stringPtr("MAX"),
								Values: &ruleresolver.ActionValues{
									ActionValues: &[]ruleresolver.ActionValue{
										{Value: anyPtr(0)},
										{
											Action: &ruleresolver.Action{
												Operation: stringPtr("SUBTRACT"),
												Values: &ruleresolver.ActionValues{
													ActionValues: &[]ruleresolver.ActionValue{
														{Value: anyPtr("$standaardpremie")},
														{
															Action: &ruleresolver.Action{
																Operation: stringPtr("ADD"),
																Values: &ruleresolver.ActionValues{
																	ActionValues: &[]ruleresolver.ActionValue{
																		{
																			Action: &ruleresolver.Action{
																				Operation: stringPtr("MULTIPLY"),
																				Values: &ruleresolver.ActionValues{
																					ActionValues: &[]ruleresolver.ActionValue{
																						{Value: anyPtr("$eigen_bijdrage_percentage")},
																						{
																							Action: &ruleresolver.Action{
																								Operation: stringPtr("MAX"),
																								Values: &ruleresolver.ActionValues{
																									ActionValues: &[]ruleresolver.ActionValue{
																										{Value: anyPtr(0)},
																										{
																											Action: &ruleresolver.Action{
																												Operation: stringPtr("SUBTRACT"),
																												Values: &ruleresolver.ActionValues{
																													ActionValues: &[]ruleresolver.ActionValue{
																														{Value: anyPtr("$toetsingsinkomen")},
																														{Value: anyPtr("$drempelbedrag")},
																													},
																												},
																											},
																										},
																									},
																								},
																							},
																						},
																					},
																				},
																			},
																		},
																		{Value: anyPtr("$eigen_bijdrage_vast")},
																		{Value: anyPtr("$correctie_vorig_jaar")},
																	},
																},
															},
														},
													},
												},
											},
										},
									},
								},
							},
						},
					},
				},
			},
		},
	}

	// Benchmark individual complexity levels
	b.Run("Level1_SimpleEligibility", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = analyzeDependencies(simpleEligibilityAction)
		}
	})

	b.Run("Level2_BasicIncome", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = analyzeDependencies(basicIncomeAction)
		}
	})

	b.Run("Level3_PartnerDependent", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = analyzeDependencies(partnerDependentAction)
		}
	})

	b.Run("Level4_KinderopvangArray", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = analyzeDependencies(kinderopvangArrayAction)
		}
	})

	b.Run("Level5_MaxComplexityZorgtoeslag", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = analyzeDependencies(maxComplexityZorgtoeslagAction)
		}
	})

	// Realistic workflow simulation
	// Based on typical law processing patterns
	realisticWorkflow := []ruleresolver.Action{
		simpleEligibilityAction,        // Check eligibility first
		basicIncomeAction,              // Calculate base income
		partnerDependentAction,         // Apply partner logic
		kinderopvangArrayAction,        // Process array data
		maxComplexityZorgtoeslagAction, // Final complex calculation
	}

	b.Run("RealisticWorkflow", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			for _, action := range realisticWorkflow {
				_ = analyzeDependencies(action)
			}
		}
	})

	// Memory allocation benchmark
	b.Run("MemoryAllocation_ComplexAction", func(b *testing.B) {
		b.ReportAllocs()
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			deps := analyzeDependencies(maxComplexityZorgtoeslagAction)
			_ = len(deps) // Ensure result is used
		}
	})
}
