# Law Machine-Readable Interpreter - Usage Examples

## Example 1: Interpret a Complete Law (Zorgtoeslag)

**User Request:**
```
Interpret the Wet op de Zorgtoeslag
```

**Skill Actions:**

1. **Gather legal text** from wetten.overheid.nl or user-provided source
2. **Identify service provider**: TOESLAGEN (Belastingdienst/Toeslagen)
3. **Determine file location**: `law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml`
4. **Generate complete YAML:**

```yaml
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: "4d8c7237-b930-4f0f-aaa3-624ba035e449"
name: "Zorgtoeslag"
law: "zorgtoeslagwet"
law_type: "FORMELE_WET"
legal_character: "BESCHIKKING"
decision_type: "TOEKENNING"
discoverable: "CITIZEN"
valid_from: 2025-01-01
service: "TOESLAGEN"
description: >
  Berekening van het recht op en de hoogte van de zorgtoeslag
  op basis van de Wet op de zorgtoeslag.

references:
  - law: "Wet op de zorgtoeslag"
    article: "2"
    url: "https://wetten.overheid.nl/BWBR0018451/2025-01-01#Artikel2"

properties:
  parameters:
    - name: "BSN"
      description: "Burgerservicenummer van de aanvrager"
      type: "string"
      required: true

  input:
    - name: "AGE"
      description: "Leeftijd van de aanvrager"
      type: "number"
      service_reference:
        service: "RvIG"
        field: "age"
        law: "wet_brp"
        parameters:
          - name: "BSN"
            reference: "$BSN"
      type_spec:
        unit: "years"
        precision: 0
        min: 0
    - name: "IS_VERZEKERD"
      description: "Is de aanvrager verzekerd volgens Zvw"
      type: "boolean"
      service_reference:
        service: "ZORGINSTITUUT"
        field: "is_verzekerd"
        law: "zorgverzekeringswet"
        parameters:
          - name: "BSN"
            reference: "$BSN"
    - name: "TOETSINGSINKOMEN"
      description: "Verzamelinkomen"
      type: "amount"
      service_reference:
        service: "BELASTINGDIENST"
        field: "toetsingsinkomen"
        law: "wet_inkomstenbelasting"
        parameters:
          - name: "BSN"
            reference: "$BSN"
      type_spec:
        unit: "eurocent"
        precision: 0
        min: 0
    - name: "HAS_PARTNER"
      description: "Heeft de aanvrager een toeslagpartner"
      type: "boolean"
      service_reference:
        service: "BELASTINGDIENST"
        field: "has_partner"
        law: "algemene_wet_inkomensafhankelijke_regelingen"
        parameters:
          - name: "BSN"
            reference: "$BSN"

  output:
    - name: "is_eligible"
      description: "Heeft de persoon recht op zorgtoeslag"
      type: "boolean"
      citizen_relevance: secondary
    - name: "hoogte_toeslag"
      description: "Hoogte van de zorgtoeslag per maand"
      type: "amount"
      type_spec:
        unit: "eurocent"
        precision: 0
        min: 0
      temporal:
        type: "period"
        period_type: "month"
      citizen_relevance: primary

  definitions:
    STANDAARDPREMIE: 175800
    DREMPELINKOMEN_ALLEENSTAAND: 2588900
    DREMPELINKOMEN_PARTNER: 3536800
    PERCENTAGE_DREMPEL_ALLEENSTAAND: 0.01896
    PERCENTAGE_DREMPEL_PARTNER: 0.04273
    PERCENTAGE_TOETSINGSINKOMEN: 0.137

requirements:
  - all:
      - subject: "$AGE"
        operation: GREATER_OR_EQUAL
        value: 18
      - subject: "$IS_VERZEKERD"
        operation: EQUALS
        value: true

actions:
  - output: "is_eligible"
    value: true

  - output: "hoogte_toeslag"
    operation: MAX
    values:
      - 0
      - operation: SUBTRACT
        values:
          - "$STANDAARDPREMIE"
          - operation: ADD
            values:
              - operation: MULTIPLY
                values:
                  - operation: IF
                    conditions:
                      - test:
                          subject: "$HAS_PARTNER"
                          operation: EQUALS
                          value: true
                        then: "$DREMPELINKOMEN_PARTNER"
                      - else: "$DREMPELINKOMEN_ALLEENSTAAND"
                  - operation: IF
                    conditions:
                      - test:
                          subject: "$HAS_PARTNER"
                          operation: EQUALS
                          value: true
                        then: "$PERCENTAGE_DREMPEL_PARTNER"
                      - else: "$PERCENTAGE_DREMPEL_ALLEENSTAAND"
              - operation: MULTIPLY
                values:
                  - operation: MAX
                    values:
                      - 0
                      - operation: SUBTRACT
                        values:
                          - "$TOETSINGSINKOMEN"
                          - operation: IF
                            conditions:
                              - test:
                                  subject: "$HAS_PARTNER"
                                  operation: EQUALS
                                  value: true
                                then: "$DREMPELINKOMEN_PARTNER"
                              - else: "$DREMPELINKOMEN_ALLEENSTAAND"
                  - "$PERCENTAGE_TOETSINGSINKOMEN"
```

5. **Report:**
```
Interpreted Wet op de Zorgtoeslag

  File: law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml
  Parameters: 1 (BSN)
  Inputs: 4 (AGE, IS_VERZEKERD, TOETSINGSINKOMEN, HAS_PARTNER)
  Outputs: 2 (is_eligible, hoogte_toeslag)
  Requirements: 2 conditions (age >= 18, insured)
  Actions: 2

  TODOs remaining:
  - Implement: wet_brp (RvIG, for AGE)
  - Implement: zorgverzekeringswet (ZORGINSTITUUT, for IS_VERZEKERD)
  - Implement: wet_inkomstenbelasting (BELASTINGDIENST, for TOETSINGSINKOMEN)
  - Implement: algemene_wet_inkomensafhankelijke_regelingen (BELASTINGDIENST, for HAS_PARTNER)

  The law is now executable via the engine!
```

---

## Example 2: Before/After - Simple Constant Definition

**Legal text:**
```
De standaardpremie bedraagt EUR 1.758 per jaar.
```

**Before (no YAML):** Nothing exists yet.

**After (complete law YAML):**
```yaml
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
name: "Standaardpremie zorgverzekering"
law: "regeling_standaardpremie"
valid_from: 2025-01-01
service: "ZORGINSTITUUT"

properties:
  output:
    - name: "standaardpremie"
      description: "Standaardpremie zorgverzekering per jaar"
      type: "amount"
      type_spec:
        unit: "eurocent"
        precision: 0
      citizen_relevance: primary

  definitions:
    STANDAARDPREMIE: 175800  # EUR 1.758 in eurocent

actions:
  - output: "standaardpremie"
    value: "$STANDAARDPREMIE"
```

**Key points:**
- EUR 1.758 converted to 175800 eurocent
- Simple `value` assignment (no operation needed)
- Definition uses UPPER_CASE, output uses lowercase

---

## Example 3: Before/After - Eligibility Check with Requirements

**Legal text:**
```
Een persoon heeft recht op zorgtoeslag indien hij:
a. de leeftijd van 18 jaar heeft bereikt;
b. verzekerd is ingevolge de Zorgverzekeringswet;
c. in Nederland woont.
```

**After:**
```yaml
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: "b2c3d4e5-f6a7-8901-bcde-f12345678901"
name: "Recht op zorgtoeslag"
law: "zorgtoeslagwet"
law_type: "FORMELE_WET"
legal_character: "BESCHIKKING"
decision_type: "TOEKENNING"
discoverable: "CITIZEN"
valid_from: 2025-01-01
service: "TOESLAGEN"

references:
  - law: "Wet op de zorgtoeslag"
    article: "2"
    url: "https://wetten.overheid.nl/BWBR0018451/2025-01-01#Artikel2"

properties:
  parameters:
    - name: "BSN"
      description: "Burgerservicenummer van de aanvrager"
      type: "string"
      required: true

  input:
    - name: "AGE"
      description: "Leeftijd van de aanvrager"
      type: "number"
      service_reference:
        service: "RvIG"
        field: "age"
        law: "wet_brp"
        parameters:
          - name: "BSN"
            reference: "$BSN"
    - name: "IS_VERZEKERD"
      description: "Is verzekerd ingevolge de Zorgverzekeringswet"
      type: "boolean"
      service_reference:
        service: "ZORGINSTITUUT"
        field: "is_verzekerd"
        law: "zorgverzekeringswet"
        parameters:
          - name: "BSN"
            reference: "$BSN"
    - name: "WOONT_IN_NEDERLAND"
      description: "Woont in Nederland"
      type: "boolean"
      service_reference:
        service: "RvIG"
        field: "woont_in_nederland"
        law: "wet_brp"
        parameters:
          - name: "BSN"
            reference: "$BSN"

  output:
    - name: "is_eligible"
      description: "Heeft de persoon recht op zorgtoeslag"
      type: "boolean"
      citizen_relevance: primary

requirements:
  - all:
      - subject: "$AGE"
        operation: GREATER_OR_EQUAL
        value: 18
      - subject: "$IS_VERZEKERD"
        operation: EQUALS
        value: true
      - subject: "$WOONT_IN_NEDERLAND"
        operation: EQUALS
        value: true

actions:
  - output: "is_eligible"
    value: true
```

**Key points:**
- Three conditions mapped to `requirements` with `all` block
- "de leeftijd van 18 jaar heeft bereikt" -> `GREATER_OR_EQUAL`, value: 18
- "ingevolge de Zorgverzekeringswet" -> `service_reference` to ZORGINSTITUUT
- `is_eligible` is set to `true` only if all requirements pass
- Uses `GREATER_OR_EQUAL` (NOT `GREATER_THAN_OR_EQUAL`)

---

## Example 4: Before/After - Cross-Law Reference via service_reference

**Legal text:**
```
Het toetsingsinkomen, bedoeld in artikel 8 van de Algemene wet
inkomensafhankelijke regelingen, bedraagt niet meer dan EUR 39.719.
```

**After:**
```yaml
properties:
  parameters:
    - name: "BSN"
      description: "Burgerservicenummer"
      type: "string"
      required: true

  input:
    - name: "TOETSINGSINKOMEN"
      description: "Toetsingsinkomen bedoeld in art. 8 Awir"
      type: "amount"
      service_reference:
        service: "BELASTINGDIENST"
        field: "toetsingsinkomen"
        law: "algemene_wet_inkomensafhankelijke_regelingen"
        parameters:
          - name: "BSN"
            reference: "$BSN"
      type_spec:
        unit: "eurocent"
        precision: 0
        min: 0

  output:
    - name: "onder_inkomensgrens"
      description: "Toetsingsinkomen onder de inkomensgrens"
      type: "boolean"
      citizen_relevance: secondary

  definitions:
    INKOMENSGRENS: 3971900  # EUR 39.719 in eurocent

actions:
  - output: "onder_inkomensgrens"
    operation: LESS_OR_EQUAL
    subject: "$TOETSINGSINKOMEN"
    value: "$INKOMENSGRENS"
```

**Key points:**
- "bedoeld in artikel 8 van de Awir" -> `service_reference` with `law: "algemene_wet_inkomensafhankelijke_regelingen"`
- EUR 39.719 -> 3971900 eurocent
- Uses `LESS_OR_EQUAL` (NOT `LESS_THAN_OR_EQUAL`)
- `service_reference.parameters` uses array of `{name, reference}` objects

---

## Example 5: Before/After - Complex Calculation Chain

**Legal text:**
```
De zorgtoeslag bedraagt de standaardpremie, verminderd met de
normpremie. De normpremie is gelijk aan het drempelinkomen
vermenigvuldigd met het drempelpercentage, vermeerderd met het
toetsingsinkomen boven de drempel vermenigvuldigd met 13,7%.
```

**After:**
```yaml
properties:
  definitions:
    STANDAARDPREMIE: 175800
    DREMPELINKOMEN: 2588900
    PERCENTAGE_DREMPEL: 0.01896
    PERCENTAGE_BOVEN_DREMPEL: 0.137

actions:
  # Step 1: Calculate threshold component
  - output: "drempel_component"
    operation: MULTIPLY
    values:
      - "$DREMPELINKOMEN"
      - "$PERCENTAGE_DREMPEL"

  # Step 2: Calculate income above threshold (min 0)
  - output: "inkomen_boven_drempel"
    operation: MAX
    values:
      - 0
      - operation: SUBTRACT
        values:
          - "$TOETSINGSINKOMEN"
          - "$DREMPELINKOMEN"

  # Step 3: Calculate above-threshold component
  - output: "boven_drempel_component"
    operation: MULTIPLY
    values:
      - "$inkomen_boven_drempel"
      - "$PERCENTAGE_BOVEN_DREMPEL"

  # Step 4: Calculate total normpremie
  - output: "normpremie"
    operation: ADD
    values:
      - "$drempel_component"
      - "$boven_drempel_component"

  # Step 5: Calculate zorgtoeslag (min 0)
  - output: "hoogte_toeslag"
    operation: MAX
    values:
      - 0
      - operation: SUBTRACT
        values:
          - "$STANDAARDPREMIE"
          - "$normpremie"
```

**Key points:**
- Complex formula broken into 5 sequential steps
- "verminderd met" -> `SUBTRACT`
- "vermenigvuldigd met" -> `MULTIPLY`
- "vermeerderd met" -> `ADD`
- Non-negativity ensured with `MAX` (values: [0, ...])
- Intermediate outputs (lowercase) referenced by later actions
- Operations use `values` array (NOT `subject`/`value` for arithmetic)

---

## Example 6: Handling Ambiguity

**User Request:**
```
Interpret this text: "Het bedrag wordt jaarlijks bij ministeriele regeling aangepast."
```

**Response:**

This text is ambiguous. It references an adjustment without specifying:
- Which amount is adjusted?
- What is the adjustment formula?
- Which ministeriele regeling contains the specifics?

**Generated YAML with TODOs:**
```yaml
properties:
  parameters:
    - name: "BSN"
      description: "Burgerservicenummer"
      type: "string"
      required: true

  output:
    - name: "aangepast_bedrag"
      description: "Jaarlijks aangepast bedrag"
      type: "amount"
      type_spec:
        unit: "eurocent"
        precision: 0
      citizen_relevance: secondary

  # TODO: Amount and adjustment formula unclear
  # - Identify which ministeriele regeling specifies the adjustment
  # - Determine whether it's CPI-indexed, wage-indexed, or fixed
  # - Add source_reference to the regeling once identified
  definitions:
    AANGEPAST_BEDRAG: 0  # TODO: Replace with actual value from regeling

actions:
  - output: "aangepast_bedrag"
    value: "$AANGEPAST_BEDRAG"
```

**Report to user:**
```
Article interpretation incomplete

  The text references "jaarlijkse aanpassing bij ministeriele regeling"
  but lacks specific details.

  Manual review needed:
  - Identify which ministeriele regeling contains the amounts
  - Determine the adjustment formula
  - Replace placeholder definition with actual value

  Added TODO comments in the YAML.
```

---

## Example 7: Integration Workflow (End-to-End)

**Full workflow from legal text to execution:**

```
Step 1: Identify the law
User: "Make the AOW executable"
-> Identify: Algemene Ouderdomswet, service: SVB

Step 2: Generate law YAML
[law-machine-readable-interpreter skill]
-> Creates: law/algemene_ouderdomswet/SVB-2024-01-01.yaml

Step 3: Validate
-> Run schema validation
-> Run reverse validation (hallucination check)

Step 4: Identify missing dependencies
Skill reports:
  TODOs:
  - wet_brp (RvIG, for AGE, BIRTH_DATE)
  - verzekerde_tijdvakken (source_reference, for insured years)

Step 5: Implement dependencies
User: "Also interpret the relevant parts of wet_brp"
[law-machine-readable-interpreter skill]
-> Creates: law/wet_brp/RvIG-2024-01-01.yaml

Step 6: Add test data
-> Create CSV source files for source_reference tables

Step 7: Execute
User: "Test the AOW for BSN 999993653"
Engine evaluates:
  1. Resolves $BSN parameter
  2. Calls wet_brp via service_reference -> gets AGE
  3. Reads verzekerde_tijdvakken via source_reference -> gets insured years
  4. Evaluates requirements (age >= retirement age, insured years > 0)
  5. Computes actions (accrual percentage, pension amount)
  6. Returns outputs (is_eligible, pension_amount)
```

---

## Common Mistakes and Fixes

### Mistake 1: Wrong Comparison Operator Names
**Wrong (regelrecht-mvp style):**
```yaml
operation: GREATER_THAN_OR_EQUAL
```

**Correct (poc-machine-law style):**
```yaml
operation: GREATER_OR_EQUAL
```

Similarly: `LESS_OR_EQUAL` not `LESS_THAN_OR_EQUAL`

### Mistake 2: Wrong IF Syntax
**Wrong (regelrecht-mvp style):**
```yaml
operation: IF
when:
  subject: "$AGE"
  operation: GREATER_OR_EQUAL
  value: 18
then: true
else: false
```

**Correct (poc-machine-law style):**
```yaml
operation: IF
conditions:
  - test:
      subject: "$AGE"
      operation: GREATER_OR_EQUAL
      value: 18
    then: true
  - else: false
```

### Mistake 3: Wrong Cross-Reference Format
**Wrong (regelrecht-mvp style):**
```yaml
source:
  regulation: "zorgverzekeringswet"
  output: "is_verzekerd"
  parameters:
    bsn: "$BSN"
```

**Correct (poc-machine-law style):**
```yaml
service_reference:
  service: "ZORGINSTITUUT"
  field: "is_verzekerd"
  law: "zorgverzekeringswet"
  parameters:
    - name: "BSN"
      reference: "$BSN"
```

### Mistake 4: Forgetting Eurocent Conversion
**Wrong:**
```yaml
STANDAARDPREMIE: 1758.00  # Still in euros!
```

**Correct:**
```yaml
STANDAARDPREMIE: 175800  # EUR 1.758 in eurocent
```

### Mistake 5: Wrong Variable Casing
**Wrong:**
```yaml
parameters:
  - name: "bsn"       # Should be UPPER_CASE
output:
  - name: "IS_ELIGIBLE"  # Should be lowercase
```

**Correct:**
```yaml
parameters:
  - name: "BSN"        # UPPER_CASE for parameters
output:
  - name: "is_eligible"  # lowercase for outputs
```

### Mistake 6: Using Article-Based Nesting
**Wrong (regelrecht-mvp style):**
```yaml
articles:
  - number: "2"
    text: "..."
    machine_readable:
      execution:
        actions: [...]
```

**Correct (poc-machine-law flat style):**
```yaml
uuid: "..."
name: "..."
law: "..."
properties:
  ...
requirements: [...]
actions: [...]
```

### Mistake 7: Missing Variable Prefix
**Wrong:**
```yaml
subject: "TOETSINGSINKOMEN"  # Missing $ prefix
```

**Correct:**
```yaml
subject: "$TOETSINGSINKOMEN"  # Variable reference with $
```
