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

### Final Decisions:

8. **decision_is_verzekerde_zorgtoeslag** (Eligibility)
   - Depends on: leeftijd, is_verzekerde
   - Logic: `leeftijd >= 18 AND is_verzekerde = true`
   - Returns: Boolean (eligible?)

9. **decision_hoogte_toeslag** (Benefit Amount)
   - Depends on: ALL above decisions + BKMs
   - Logic: Complex calculation based on:
     - If not eligible → 0
     - If single person:
       - Check income threshold (€39,719)
       - Check wealth threshold (€141,896)
       - Calculate: standaardpremie - normpremie
     - If with partner:
       - Check combined income threshold (€50,206)
       - Check wealth threshold (€179,429)
       - Calculate: (2 × standaardpremie) - normpremie
   - Returns: Benefit amount in eurocents

### Business Knowledge Models (BKMs):

- **constants()**: Returns all threshold values
- **calculate_normpremie_single()**: Calculates norm premium for singles
- **calculate_normpremie_partner()**: Calculates norm premium for couples

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
   ├─ Use result from decision_is_verzekerde_zorgtoeslag
   ├─ Evaluate decision_heeft_partner
   │  └─ Call decisionService_brp() [cached from step 2]
   ├─ Evaluate decision_standaardpremie
   │  └─ Call decisionService_standaardpremie() from standaardpremie_2025.dmn
   ├─ Evaluate decision_toetsingsinkomen
   │  └─ Call decisionService_uwv() from wet_inkomstenbelasting_uwv.dmn
   │     └─ Evaluate decision_toetsingsinkomen (sum of income sources)
   ├─ Evaluate decision_partner_toetsingsinkomen
   │  └─ Call decisionService_uwv() again with partner data
   ├─ Evaluate decision_vermogen
   │  └─ Call decisionService_belastingdienst() from wet_inkomstenbelasting_belastingdienst.dmn
   │     └─ Evaluate decisions:
   │        ├─ decision_verzamelinkomen (calls BKM)
   │        └─ decision_vermogen (extracts from tax_data)
   │
   └─ Execute complex if-then-else expression with:
      ├─ Call constants() BKM for threshold values
      └─ Call calculate_normpremie_single() or calculate_normpremie_partner() BKM
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
