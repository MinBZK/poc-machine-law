# DMN Hierarchy for Zorgtoeslag (Healthcare Allowance)

## Dependency Graph

```
zorgtoeslag_toeslagen_2025.dmn (Main Decision)
│
├─→ standaardpremie_2025.dmn
│   └─ Provides: standaardpremie (€2,112 standard premium)
│   └─ Decision Service: decisionService_standaardpremie()
│   └─ Outputs: standaardpremie (number)
│
├─→ wet_brp_rvig.dmn (Population Register)
│   └─ Provides: Age and partnership status
│   └─ Decision Service: decisionService_brp(person, reference_date)
│   └─ Outputs:
│       • leeftijd (age in years)
│       • heeft_toeslagpartner (has partner for allowance purposes)
│
├─→ zvw_rvz.dmn (Health Insurance Law)
│   └─ Provides: Health insurance status
│   └─ Decision Service: decisionService_zvw(person)
│   └─ Outputs: verzekerd_voor_zvw (insured for health insurance)
│
├─→ wet_inkomstenbelasting_belastingdienst.dmn (Tax Service - Income)
│   └─ Provides: Collected income and wealth
│   └─ Decision Service: decisionService_belastingdienst(person, tax_data)
│   └─ Outputs:
│       • verzamelinkomen (collected income from box 1+2+3)
│       • vermogen (wealth)
│
└─→ wet_inkomstenbelasting_uwv.dmn (Benefits Service - Test Income)
    └─ Provides: Test income for benefits
    └─ Decision Service: decisionService_uwv(person, income_data)
    └─ Outputs: toetsingsinkomen (test income = work + benefits)
```

## Main Decision Flow (zorgtoeslag_toeslagen_2025.dmn)

### Input Data Required:
- `person` (birth_date, health_insurance_status, is_resident, partnership_status)
- `reference_date` (date for age calculation)
- `tax_data` (box1_inkomen, box2_inkomen, box3_inkomen, vermogen)
- `income_data` (work_income, unemployment_benefit, disability_benefit, pension, other_benefits)
- `partner_income_data` (optional, same structure as income_data)

### Internal Decisions (using imports):

1. **decision_standaardpremie**
   - Calls: `decisionService_standaardpremie()`
   - Returns: 211200 (€2,112 in eurocents)

2. **decision_leeftijd**
   - Calls: `decisionService_brp(person, reference_date).leeftijd`
   - Returns: Age in years

3. **decision_heeft_partner**
   - Calls: `decisionService_brp(person, reference_date).heeft_toeslagpartner`
   - Returns: Boolean (has partner?)

4. **decision_is_verzekerde**
   - Calls: `decisionService_zvw(person).verzekerd_voor_zvw`
   - Returns: Boolean (insured?)

5. **decision_toetsingsinkomen**
   - Calls: `decisionService_uwv(person, income_data).toetsingsinkomen`
   - Returns: Test income for applicant

6. **decision_partner_toetsingsinkomen**
   - Calls: `decisionService_uwv(person, partner_income_data).toetsingsinkomen`
   - Returns: Test income for partner (or 0 if no partner)

7. **decision_vermogen**
   - Calls: `decisionService_belastingdienst(person, tax_data).vermogen`
   - Returns: Wealth amount

### Eligibility Decisions:

8. **decision_is_verzekerde_zorgtoeslag** (Basic Eligibility)
   - Depends on: leeftijd, is_verzekerde
   - Logic: `leeftijd >= 18 AND is_verzekerde = true`
   - Returns: Boolean (meets basic criteria?)

### Intermediate Calculation Decisions:

9. **decision_gezamenlijk_inkomen** (Combined Income)
   - Depends on: heeft_partner, toetsingsinkomen, partner_toetsingsinkomen
   - Logic: If has partner, sum both incomes; otherwise just applicant's income
   - Returns: Number (combined income in eurocents)

10. **decision_applicable_drempelinkomen** (Applicable Income Threshold)
    - Depends on: heeft_partner
    - Logic: Select threshold based on partnership status
    - Returns: Number (€39,719 single / €50,206 partner)

11. **decision_applicable_vermogensgrens** (Applicable Wealth Limit)
    - Depends on: heeft_partner
    - Logic: Select limit based on partnership status
    - Returns: Number (€141,896 single / €179,429 partner)

12. **decision_inkomen_overschreden** (Income Exceeded)
    - Depends on: gezamenlijk_inkomen, applicable_drempelinkomen
    - Logic: Check if combined income exceeds threshold
    - Returns: Boolean

13. **decision_vermogen_overschreden** (Wealth Exceeded)
    - Depends on: vermogen, applicable_vermogensgrens
    - Logic: Check if wealth exceeds limit
    - Returns: Boolean

### Eligibility Scenario Determination:

14. **decision_eligibility_scenario** (Scenario Classification)
    - Depends on: is_verzekerde_zorgtoeslag, inkomen_overschreden, vermogen_overschreden, heeft_partner
    - Logic: Decision table with 5 rules:
      1. Not eligible → "not_eligible"
      2. Income too high → "income_too_high"
      3. Assets too high → "assets_too_high"
      4. Eligible single → "eligible_single"
      5. Eligible partner → "eligible_partner"
    - Returns: String (scenario classification)

### Benefit Calculation Decisions:

15. **decision_benefit_calculation_single** (Single Benefit)
    - Depends on: standaardpremie, toetsingsinkomen
    - Logic: `standaardpremie - normpremie_single(...)`
    - Returns: Number (benefit for single person)

16. **decision_benefit_calculation_partner** (Partner Benefit)
    - Depends on: standaardpremie, toetsingsinkomen, partner_toetsingsinkomen
    - Logic: `(2 × standaardpremie) - normpremie_partner(...)`
    - Returns: Number (benefit for person with partner)

17. **decision_benefit_calculation** (Final Calculation Selector)
    - Depends on: eligibility_scenario, benefit_calculation_single, benefit_calculation_partner
    - Logic: Select appropriate calculation based on scenario:
      - "eligible_single" → use benefit_calculation_single
      - "eligible_partner" → use benefit_calculation_partner
      - Otherwise → 0
    - Returns: Number (final benefit amount)

18. **decision_hoogte_toeslag** (Benefit Amount - Main Output)
    - Depends on: benefit_calculation
    - Logic: Simple reference to benefit_calculation
    - Returns: Benefit amount in eurocents

### Business Knowledge Models (BKMs):

- **constants()**: Returns all threshold values (income thresholds, wealth limits, percentages)
- **normpremie_single()**: Calculates norm premium for singles
  - Simplified expression: `if income > threshold then percentage_drempel * threshold + afbouwpercentage * (income - threshold) else percentage_drempel * income`
- **normpremie_partner()**: Calculates norm premium for couples
  - Simplified expression: `if income + partner_income > threshold then ... else ...`

### Refactoring Notes:

The decision logic was refactored from a single complex 828-character nested expression into:
- 5 intermediate decisions for threshold/limit calculations
- 1 decision table with 5 rules for eligibility scenario determination
- 2 separate calculation decisions (single vs partner)
- 1 selector decision that chooses the right calculation

This improves:
- **Readability**: Each decision has a clear, single purpose
- **Maintainability**: Changes to thresholds or logic are localized
- **Traceability**: Execution path shows each step of the decision process
- **Testability**: Each decision can be tested independently

## Execution Order

When evaluating `decision_hoogte_toeslag`:

```
1. Load zorgtoeslag_toeslagen_2025.dmn
   ├─ Load standaardpremie_2025.dmn
   ├─ Load wet_brp_rvig.dmn
   ├─ Load zvw_rvz.dmn
   ├─ Load wet_inkomstenbelasting_belastingdienst.dmn
   └─ Load wet_inkomstenbelasting_uwv.dmn

2. Evaluate decision_is_verzekerde_zorgtoeslag
   ├─ Evaluate decision_leeftijd
   │  └─ Call decisionService_brp() from wet_brp_rvig.dmn
   │     └─ Evaluate decision_leeftijd in wet_brp_rvig.dmn
   │        └─ Use years(person.birth_date, reference_date) FEEL function
   │
   └─ Evaluate decision_is_verzekerde
      └─ Call decisionService_zvw() from zvw_rvz.dmn
         └─ Evaluate decision_verzekerd_voor_zvw in zvw_rvz.dmn
            └─ Use decision table with insurance status rules

3. Evaluate decision_hoogte_toeslag
   └─ Evaluate decision_benefit_calculation
      ├─ Evaluate decision_eligibility_scenario (Decision Table)
      │  ├─ Use result from decision_is_verzekerde_zorgtoeslag
      │  ├─ Evaluate decision_inkomen_overschreden
      │  │  ├─ Evaluate decision_gezamenlijk_inkomen
      │  │  │  ├─ Evaluate decision_heeft_partner
      │  │  │  │  └─ Call decisionService_brp() [cached from step 2]
      │  │  │  ├─ Evaluate decision_toetsingsinkomen
      │  │  │  │  └─ Call decisionService_uwv() from wet_inkomstenbelasting_uwv.dmn
      │  │  │  │     └─ Calculate sum of income sources (work + benefits)
      │  │  │  └─ Evaluate decision_partner_toetsingsinkomen
      │  │  │     └─ Call decisionService_uwv() again with partner data
      │  │  └─ Evaluate decision_applicable_drempelinkomen
      │  │     └─ Use constants() BKM to get threshold
      │  ├─ Evaluate decision_vermogen_overschreden
      │  │  ├─ Evaluate decision_vermogen
      │  │  │  └─ Call decisionService_belastingdienst() from wet_inkomstenbelasting_belastingdienst.dmn
      │  │  │     └─ Extract vermogen from tax_data
      │  │  └─ Evaluate decision_applicable_vermogensgrens
      │  │     └─ Use constants() BKM to get limit
      │  └─ Apply decision table rules to determine scenario
      │
      ├─ Evaluate decision_benefit_calculation_single
      │  ├─ Evaluate decision_standaardpremie
      │  │  └─ Call decisionService_standaardpremie() from standaardpremie_2025.dmn
      │  └─ Call normpremie_single() BKM with constants
      │
      ├─ Evaluate decision_benefit_calculation_partner
      │  ├─ Use decision_standaardpremie [cached]
      │  └─ Call normpremie_partner() BKM with constants
      │
      └─ Select appropriate calculation based on eligibility_scenario:
         - "eligible_single" → return benefit_calculation_single
         - "eligible_partner" → return benefit_calculation_partner
         - Otherwise → return 0
```

## Layer Architecture

**Layer 1: Base Data DMNs** (no dependencies)
- standaardpremie_2025.dmn
- wet_brp_rvig.dmn
- zvw_rvz.dmn
- wet_inkomstenbelasting_belastingdienst.dmn
- wet_inkomstenbelasting_uwv.dmn

**Layer 2: Orchestration DMN** (depends on Layer 1)
- zorgtoeslag_toeslagen_2025.dmn

This creates a clean separation where:
- Base DMNs contain domain-specific rules (age, insurance, income)
- Orchestration DMN combines them into the final benefit calculation
