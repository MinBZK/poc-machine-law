---
name: law-machine-readable-interpreter
description: Interprets legal text and generates machine-executable law YAML files compatible with the poc-machine-law engine. Use when user wants to make a law executable, create a new law YAML, or interpret Dutch legal articles for computational execution.
allowed-tools: Read, Edit, Grep, Glob, Bash
---

# Law Machine-Readable Interpreter

Analyzes Dutch legal text and generates complete machine-executable law YAML files for the poc-machine-law engine.

## What This Skill Does

1. Reads Dutch law text (from wetten.overheid.nl or user-provided text)
2. Analyzes each article's legal text
3. Identifies computational elements:
   - Input parameters (BSN, dates, amounts)
   - Constants and definitions
   - Conditions and logic
   - Cross-references to other laws/articles
   - Output values
4. Generates a complete law YAML file with:
   - Top-level metadata (`uuid`, `name`, `law`, `service`, etc.)
   - `properties` section: `parameters`, `sources`, `input`, `output`, `definitions`
   - `requirements` section (eligibility checks)
   - `actions` section (computation logic)
5. Converts monetary amounts to eurocent (EUR 795,47 -> 79547)
6. Creates TODO comments for missing external law references
7. Uses aggressive AI interpretation (full automation)

## Important Principles

- **Aggressive interpretation**: Generate complete logic even if uncertain
- **Eurocent conversion**: Convert all monetary amounts (EUR X,XX -> eurocent integers)
- **Cross-references**: Detect references to other laws/articles via `service_reference`
- **TODOs for missing refs**: Add TODO comments when external laws are not yet available
- **legal_basis**: Add traceability to specific law text where applicable
- **All amounts in eurocent**: type `"amount"` with `type_spec: { unit: "eurocent", precision: 0 }`

## Schema Structure Overview

Each law is a single flat YAML file (NOT article-based). The top-level structure:

```yaml
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: "4d8c7237-b930-4f0f-aaa3-624ba035e449"   # UUID v4
name: "Zorgtoeslag"                              # Human-readable name
law: "zorgtoeslagwet"                            # Law identifier slug
law_type: "FORMELE_WET"
legal_character: "BESCHIKKING"
decision_type: "TOEKENNING"
discoverable: "CITIZEN"
valid_from: 2025-01-01
service: "TOESLAGEN"
description: >
  Description of what this law computes...

references:
  - law: "Wet op de zorgtoeslag"
    article: "2"
    url: "https://wetten.overheid.nl/..."

properties:
  parameters: [...]      # Caller-provided input
  sources: [...]         # Data from tables/databases
  input: [...]           # Data from other services/laws
  output: [...]          # Computed results
  definitions: {...}     # Constants

requirements: [...]      # Eligibility checks (AND/OR blocks)
actions: [...]           # Computation logic
```

## Step-by-Step Instructions

### Step 1: Identify Target Law

When user asks to "interpret" or "make executable" a law:

1. Determine which Dutch law is being referred to
2. Check `law/` directory for existing files
3. If the law already exists, read it and identify what needs updating
4. If creating a new law, gather the legal text

### Step 2: Define Top-Level Metadata

Generate a UUID v4 and fill in the metadata:

```yaml
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: "<generate-uuid-v4>"
name: "Human-readable name"
law: "law_identifier_slug"
law_type: "FORMELE_WET"           # or other type
legal_character: "BESCHIKKING"     # or BESLUIT_VAN_ALGEMENE_STREKKING
decision_type: "TOEKENNING"        # or AANSLAG, BELEIDSREGEL, etc.
discoverable: "CITIZEN"            # or "BUSINESS"
valid_from: 2025-01-01
service: "SVB"                     # Service provider code
description: >
  Dutch description of what this law computes...
```

**Service provider codes:** `SVB`, `TOESLAGEN`, `RVO`, `GEMEENTE_AMSTERDAM`, `KIESRAAD`, `UWV`, `BELASTINGDIENST`, `RvIG`, `ZORGINSTITUUT`, `SZW`, `DUO`

**Law types:** `FORMELE_WET`

**Legal characters:** `BESCHIKKING`, `BESLUIT_VAN_ALGEMENE_STREKKING`

**Decision types:** `TOEKENNING`, `AANSLAG`, `BELEIDSREGEL`, `ALGEMEEN_VERBINDEND_VOORSCHRIFT`, `VOORBEREIDINGSBESLUIT`, `ANDERE_HANDELING`

### Step 3: Add Legal References

```yaml
references:
  - law: "Wet op de zorgtoeslag"
    article: "2"
    url: "https://wetten.overheid.nl/BWBR0018451/2025-01-01#Artikel2"
```

### Step 4: Define Parameters

Parameters are values the caller must supply:

```yaml
properties:
  parameters:
    - name: "BSN"
      description: "Burgerservicenummer van de aanvrager"
      type: "string"
      required: true
```

**Common parameters:**
- `BSN` (string) - Citizen service number (always required)

**Convention:** UPPER_CASE names for parameters.

### Step 5: Define Input (Cross-Law References)

Inputs resolve data from other laws/services via `service_reference`:

```yaml
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
```

**Patterns to detect in legal text:**
- "ingevolge de [Law Name]" -> cross-law reference
- "bedoeld in artikel X" -> internal reference
- "genoemd in [regulation]" -> external reference

**If external law not yet available, add a TODO:**
```yaml
    - name: "IS_VERZEKERD"
      description: "Is verzekerd ingevolge de Zorgverzekeringswet"
      type: "boolean"
      # TODO: Implement zorgverzekeringswet service
      service_reference:
        service: "ZORGINSTITUUT"
        field: "is_verzekerd"
        law: "zorgverzekeringswet"
        parameters:
          - name: "BSN"
            reference: "$BSN"
```

### Step 6: Define Sources (Database/Table References)

Sources pull data from CSV/database tables:

```yaml
  sources:
    - name: "RESIDENCE_INSURED_YEARS"
      description: "Verzekerde jaren op basis van woonperiodes"
      type: "number"
      type_spec:
        precision: 2
        min: 0
        max: 50
      source_reference:
        table: "verzekerde_tijdvakken"
        field: "woonperiodes"
        select_on:
          - name: "bsn"
            description: "BSN van de persoon"
            type: "string"
            value: "$BSN"
```

### Step 7: Extract Constants and Definitions

Look for fixed values in the legal text:

```yaml
  definitions:
    STANDAARDPREMIE: 175800                    # EUR 1.758 in eurocent
    DREMPELINKOMEN_ALLEENSTAAND: 2588900       # EUR 25.889
    PERCENTAGE_DREMPEL_ALLEENSTAAND: 0.01896
```

Definitions can also include `legal_basis`:
```yaml
  definitions:
    drempelinkomen:
      value: 3971900
      legal_basis:
        law: "Wet op de zorgtoeslag"
        article: "2"
```

**Monetary Conversion Rules:**
- EUR 154.859 -> 15485900 (eurocent)
- EUR 2.112 -> 211200 (eurocent)
- EUR 795,47 -> 79547 (eurocent)
- Always use integer eurocent values

### Step 8: Define Outputs

```yaml
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
```

**Convention:** lowercase names for outputs.

**`citizen_relevance`:** `primary` (shown prominently) or `secondary`

### Step 9: Define Requirements (Eligibility Checks)

Requirements are evaluated BEFORE actions. If not met, no actions execute:

```yaml
requirements:
  - all:
      - subject: "$AGE"
        operation: GREATER_OR_EQUAL
        value: 18
      - subject: "$IS_VERZEKERD"
        operation: EQUALS
        value: true
```

Requirements support:
- `all: [...]` - all must be true (AND)
- `or: [...]` - at least one must be true (OR)
- Nesting: `all`/`or` blocks can contain other `all`/`or` blocks

### Step 10: Define Actions (Computation Logic)

Actions compute output values. The engine does topological sorting automatically.

**Direct value assignment:**
```yaml
actions:
  - output: "is_eligible"
    value: true
```

**Operation with values:**
```yaml
  - output: "accrual_percentage"
    operation: DIVIDE
    values:
      - operation: MIN
        values:
          - operation: ADD
            values:
              - "$RESIDENCE_INSURED_YEARS"
              - "$EMPLOYMENT_INSURED_YEARS"
          - "$YEARS_FOR_FULL_PENSION"
      - "$YEARS_FOR_FULL_PENSION"
```

**IF with conditions (test/then/else):**
```yaml
  - output: "base_amount"
    operation: IF
    conditions:
      - test:
          subject: "$HAS_PARTNER"
          operation: EQUALS
          value: true
        then: "$BASE_AMOUNT_SHARED"
      - else: "$BASE_AMOUNT_SINGLE"
```

**Direct subject assignment:**
```yaml
  - output: "partner_bsn"
    subject: "$PARTNER_BSN"
```

### Step 11: Add Legal Basis (Traceability)

For important computations, add `legal_basis` to definitions:
```yaml
definitions:
  DREMPELINKOMEN:
    value: 3971900
    legal_basis:
      law: "Wet op de zorgtoeslag"
      article: "2"
```

### Step 12: Validate File Structure

Before reporting, verify the YAML:

1. **Check file location:** Should be in `law/{law_name}/{SERVICE}-{YYYY-MM-DD}.yaml`
2. **Run linting:** `ruff check` and `ruff format` for any Python wrappers
3. **Validate schema:** Ensure all required fields are present
4. **Check YAML syntax:** Proper indentation (2 spaces), quoting, types

### Step 13: Reverse Validation (Hallucination Check)

Verify every element traces back to the original legal text:

1. **Definitions/Constants:** Is the value explicitly in the article text?
2. **Input fields:** Is the data source referenced in the text?
3. **Output fields:** Does the article actually produce this output?
4. **Actions/Operations:** Does the legal text contain this logic?
5. **Conditions:** Are conditions explicitly stated?

**Decision matrix:**

| Traceable in text? | Needed for logic? | Action |
|-------------------|-------------------|--------|
| YES | YES | Keep |
| YES | NO | Keep (informational) |
| NO | YES | Report as assumption |
| NO | NO | **Remove** |

### Step 14: Report Results

After successful creation:

```
Interpreted {LAW_NAME}

  Law file: law/{law_name}/{SERVICE}-{YYYY-MM-DD}.yaml
  Parameters: {count}
  Inputs: {count}
  Sources: {count}
  Outputs: {count}
  Requirements: {count} conditions
  Actions: {count}

  Assumptions (need review):
  - Added "calculation_date" parameter (implied but not stated)
  - Assumed "inkomen" refers to toetsingsinkomen

  TODOs remaining:
  - Implement service: {external_law_1}
  - Clarify calculation in article {X}

  The law is now executable via the engine!
```

## Common Patterns

### Pattern 1: Age Check (via service_reference)
```yaml
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

requirements:
  - all:
      - subject: "$AGE"
        operation: GREATER_OR_EQUAL
        value: 18
```

### Pattern 2: Income Threshold
```yaml
definitions:
  DREMPELINKOMEN: 2588900   # EUR 25.889 in eurocent

input:
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

actions:
  - output: "onder_drempel"
    operation: LESS_OR_EQUAL
    subject: "$TOETSINGSINKOMEN"
    value: "$DREMPELINKOMEN"
```

### Pattern 3: Multiple Conditions (AND via requirements)
```yaml
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
```

### Pattern 4: Calculation Chain
```yaml
actions:
  - output: "premie_basis"
    operation: MULTIPLY
    values:
      - "$STANDAARDPREMIE"
      - "$PERCENTAGE"

  - output: "premie_na_korting"
    operation: SUBTRACT
    values:
      - "$premie_basis"
      - "$KORTING"

  - output: "premie_finaal"
    operation: MAX
    values:
      - 0
      - "$premie_na_korting"
```

### Pattern 5: Conditional Value (IF/then/else)
```yaml
actions:
  - output: "base_amount"
    operation: IF
    conditions:
      - test:
          subject: "$HAS_PARTNER"
          operation: EQUALS
          value: true
        then: "$BASE_AMOUNT_SHARED"
      - else: "$BASE_AMOUNT_SINGLE"
```

### Pattern 6: FOREACH Iteration
```yaml
actions:
  - output: "total_amount"
    operation: FOREACH
    subject: "$ITEMS"
    value: "$current.amount"
    combine: "ADD"
    where:
      operation: EQUALS
      subject: "$current.active"
      value: true
```

### Pattern 7: Date Calculation
```yaml
actions:
  - output: "years_difference"
    operation: SUBTRACT_DATE
    values:
      - "$calculation_date"
      - "$BIRTH_DATE"
    unit: "years"
```

## Tips for Success

1. **Be aggressive**: Generate complete logic even if uncertain
2. **Use UPPER_CASE**: For parameters, sources, input, definitions
3. **Use lowercase**: For output names
4. **Always eurocent**: Never use decimal euro amounts
5. **Check for existing laws**: Use Glob to search `law/`
6. **Break down complex logic**: Multiple simple actions > one complex action
7. **Add descriptions**: Help future readers understand the logic
8. **Mark TODOs clearly**: Use `# TODO:` comments for missing refs
9. **Validate types**: Ensure type consistency
10. **Use `$` prefix**: All variable references must start with `$`

## Error Handling

**If legal text is ambiguous:**
- Make best guess with TODO comment
- Explain uncertainty to user
- Suggest manual review

**If external law not found:**
- Create service_reference with TODO comment
- Add to list of missing dependencies
- Continue with other parts

**If operation unclear:**
- Use simpler operations
- Break into multiple steps
- Add explanatory comments
