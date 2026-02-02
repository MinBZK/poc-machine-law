# Law Machine-Readable Interpreter - Technical Reference

## Complete YAML Structure

```yaml
# --- Top-level metadata ---
$id: https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json
uuid: string                    # UUID v4
name: string                    # Human-readable law name
law: string                     # Law identifier slug (e.g., "zorgtoeslagwet")
law_type: string                # "FORMELE_WET"
legal_character: string         # "BESCHIKKING" | "BESLUIT_VAN_ALGEMENE_STREKKING"
decision_type: string           # "TOEKENNING" | "AANSLAG" | "BELEIDSREGEL" | ...
discoverable: string            # "CITIZEN" | "BUSINESS"
valid_from: date                # YYYY-MM-DD
service: string                 # Service provider code
description: string             # Multi-line Dutch description

# --- Legal references ---
references:
  - law: string                 # Official law name
    article: string             # Article number
    url: string                 # wetten.overheid.nl URL

# --- Properties ---
properties:
  parameters:                   # Caller-provided inputs
    - name: string              # UPPER_CASE
      description: string       # Dutch description
      type: string              # "string" | "number" | "boolean" | "date" | "amount"
      required: boolean
      type_spec: TypeSpec        # Optional
      temporal: Temporal         # Optional

  sources:                      # Data from tables/databases
    - name: string              # UPPER_CASE
      description: string
      type: string
      type_spec: TypeSpec
      temporal: Temporal
      source_reference:
        source_type: string     # Optional: "laws" | "events"
        table: string           # Table name
        field: string           # Single field to extract
        fields: string[]        # Multiple fields (returns list of dicts)
        select_on:              # Filter criteria
          - name: string
            description: string
            type: string
            value: string       # "$VARIABLE" or literal
        wallet_attribute: string # Optional

  input:                        # Data from other services/laws
    - name: string              # UPPER_CASE
      description: string
      type: string
      service_reference:
        service: string         # Service code (RvIG, SVB, etc.)
        field: string           # Output field from target law
        law: string             # Law identifier of target
        parameters:             # Parameters to pass
          - name: string
            reference: string   # "$VARIABLE"
      type_spec: TypeSpec
      temporal: Temporal

  output:                       # Computed results
    - name: string              # lowercase
      description: string
      type: string
      type_spec: TypeSpec
      temporal: Temporal
      citizen_relevance: string # "primary" | "secondary"

  definitions:                  # Constants
    CONSTANT_NAME: value        # Simple form
    CONSTANT_NAME:              # Extended form
      value: any
      legal_basis:
        law: string
        article: string

# --- Requirements (eligibility gates) ---
requirements:
  - all:                        # AND: all must be true
      - subject: string
        operation: string
        value: any
      - or:                     # Nesting supported
          - subject: string
            operation: string
            value: any

# --- Actions (computation logic) ---
actions:
  - output: string              # Which output to compute
    # One of: value, operation+values, operation+conditions, subject
    value: any                  # Direct assignment
    operation: string           # Operation type
    values: any[]               # Operands
    conditions: Condition[]     # For IF
    subject: string             # Direct variable assignment
    legal_basis:                # Optional traceability
      law: string
      article: string
```

## TypeSpec Reference

```yaml
type_spec:
  unit: string          # "eurocent" | "years" | "weeks" | "months" | "days"
  precision: number     # Decimal places (rounds output)
  min: number           # Minimum value (clamps output)
  max: number           # Maximum value (clamps output)
```

## Temporal Reference

```yaml
temporal:
  type: string          # "point_in_time" | "period"
  period_type: string   # "year" | "month" | "continuous" (for period type)
  reference: string     # "$calculation_date" | "$january_first" | "$prev_january_first"
```

## Operation Types

### Arithmetic Operations

Use `values` array for operands.

**ADD** - Sum all values
```yaml
operation: ADD
values:
  - "$a"
  - "$b"
  - "$c"
```

**SUBTRACT** - First value minus rest
```yaml
operation: SUBTRACT
values:
  - "$total"
  - "$deduction"
```

**MULTIPLY** - Product of all values
```yaml
operation: MULTIPLY
values:
  - "$base"
  - "$rate"
```

**DIVIDE** - First value divided by rest
```yaml
operation: DIVIDE
values:
  - "$amount"
  - "$divisor"
```

**MIN** - Minimum of values
```yaml
operation: MIN
values:
  - "$a"
  - "$b"
```

**MAX** - Maximum of values
```yaml
operation: MAX
values:
  - 0
  - "$calculated_amount"
```

### Comparison Operations

Use `subject`/`value` or `values: [left, right]`.

**EQUALS**
```yaml
operation: EQUALS
subject: "$variable"
value: "expected"
```

**NOT_EQUALS**
```yaml
operation: NOT_EQUALS
subject: "$status"
value: "inactive"
```

**GREATER_THAN**
```yaml
operation: GREATER_THAN
subject: "$income"
value: 0
```

**GREATER_OR_EQUAL**
```yaml
operation: GREATER_OR_EQUAL
subject: "$AGE"
value: 18
```

**LESS_THAN**
```yaml
operation: LESS_THAN
subject: "$amount"
value: "$MAXIMUM"
```

**LESS_OR_EQUAL**
```yaml
operation: LESS_OR_EQUAL
subject: "$VERMOGEN"
value: "$VERMOGENSGRENS"
```

**Values-style comparison (alternative):**
```yaml
operation: GREATER_THAN
values:
  - "$income"
  - 0
```

### Logical Operations

Use `values` array.

**AND** - All values must be truthy (short-circuits on false)
```yaml
operation: AND
values:
  - operation: EQUALS
    subject: "$IS_VERZEKERD"
    value: true
  - operation: GREATER_OR_EQUAL
    subject: "$AGE"
    value: 18
```

**OR** - At least one value must be truthy (short-circuits on true)
```yaml
operation: OR
values:
  - operation: EQUALS
    subject: "$status"
    value: "actief"
  - operation: EQUALS
    subject: "$status"
    value: "rustend"
```

### Membership Operations

**IN** - Subject is in values list
```yaml
operation: IN
subject: "$status"
values: ["actief", "rustend"]
```

**NOT_IN** - Subject is not in values list
```yaml
operation: NOT_IN
subject: "$land"
values: ["XX", "YY"]
```

### Null Check Operations

**IS_NULL** - Subject is None
```yaml
operation: IS_NULL
subject: "$PARTNER_BSN"
```

**NOT_NULL** - Subject is not None
```yaml
operation: NOT_NULL
subject: "$INCOME"
```

**EXISTS** - Subject is not None and not empty
```yaml
operation: EXISTS
subject: "$REGISTRATION"
```

### Conditional - IF with `conditions`

The IF operation uses a `conditions` array of `test`/`then`/`else` blocks. Evaluated top to bottom; returns first matching `then`.

**Simple if/else:**
```yaml
operation: IF
conditions:
  - test:
      subject: "$HAS_PARTNER"
      operation: EQUALS
      value: true
    then: "$BASE_AMOUNT_SHARED"
  - else: "$BASE_AMOUNT_SINGLE"
```

**Multiple branches (if/elif/else):**
```yaml
operation: IF
conditions:
  - test:
      subject: "$HOUSEHOLD_TYPE"
      operation: EQUALS
      value: "single"
    then: "$AMOUNT_SINGLE"
  - test:
      subject: "$HOUSEHOLD_TYPE"
      operation: EQUALS
      value: "couple"
    then: "$AMOUNT_COUPLE"
  - else: "$AMOUNT_OTHER"
```

**Nested operation in then/else:**
```yaml
operation: IF
conditions:
  - test:
      subject: "$HAS_PARTNER"
      operation: EQUALS
      value: true
    then:
      operation: MULTIPLY
      values:
        - "$BASE_AMOUNT"
        - 2
  - else: "$BASE_AMOUNT"
```

### Date Operations

**SUBTRACT_DATE** - Difference between two dates
```yaml
operation: SUBTRACT_DATE
values:
  - "$calculation_date"   # end date
  - "$BIRTH_DATE"         # start date
unit: "years"             # "years" | "months" | "days"
```

### Iteration - FOREACH

```yaml
operation: FOREACH
subject: "$ITEMS"              # Array to iterate over
value: "$current.amount"       # Expression per item
combine: "ADD"                 # Aggregation: ADD, MIN, MAX, MULTIPLY
where:                         # Optional filter
  operation: EQUALS
  subject: "$current.active"
  value: true
```

- `$current` refers to the current item
- `$current_0`, `$current_1` for nested FOREACH
- Without `combine`, returns an array

### String Operations

**CONCAT** - String concatenation
```yaml
operation: CONCAT
values:
  - "$first_name"
  - " "
  - "$last_name"
```

### Other Operations

**COALESCE** - First non-null value
```yaml
operation: COALESCE
values:
  - "$PREFERRED_VALUE"
  - "$FALLBACK_VALUE"
  - 0
```

**GET** - Dictionary lookup
```yaml
operation: GET
subject: "key_name"
values:
  key_a: 100
  key_b: 200
```

## Variable Reference Syntax

All variables use `$` prefix. Resolution order:

1. **Local scope** (inside FOREACH: `$current`, `$current.field`)
2. **Overwrite definitions** (runtime overrides)
3. **Definitions** (constants from `properties.definitions`)
4. **Parameters** (caller-provided: `$BSN`)
5. **Previous outputs** (computed by earlier actions: `$is_eligible`)
6. **Overwrite input** (runtime service overrides)
7. **Sources** (from `source_reference`: `$RESIDENCE_INSURED_YEARS`)
8. **Services** (from `service_reference`: `$AGE`, triggers cross-law evaluation)

### Special Date Variables

| Variable | Description |
|----------|-------------|
| `$calculation_date` | Reference date passed to the engine |
| `$january_first` | January 1st of the calculation year |
| `$prev_january_first` | January 1st of the previous year |
| `$year` | Calculation year as string |

### Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Parameters | UPPER_CASE | `$BSN`, `$PEILDATUM` |
| Sources | UPPER_CASE | `$RESIDENCE_INSURED_YEARS` |
| Input | UPPER_CASE | `$AGE`, `$TOETSINGSINKOMEN` |
| Definitions | UPPER_CASE | `$STANDAARDPREMIE`, `$DREMPELINKOMEN` |
| Outputs | lowercase | `$is_eligible`, `$hoogte_toeslag` |

### Literal Values

```yaml
value: 18           # Integer
value: 175800       # Eurocent amount
value: 0.01896      # Percentage
value: "ACTIEF"     # String
value: true         # Boolean
value: false        # Boolean
```

## service_reference Format

For cross-law data (input from other services):

```yaml
service_reference:
  service: "RvIG"                # Service provider code
  field: "age"                   # Output field from target law
  law: "wet_brp"                 # Law identifier slug
  parameters:                    # Parameters to pass to target
    - name: "BSN"
      reference: "$BSN"
```

**Common service references:**

| Service | Law | Common Fields |
|---------|-----|---------------|
| `RvIG` | `wet_brp` | `age`, `birth_date`, `woont_in_nederland` |
| `BELASTINGDIENST` | `wet_inkomstenbelasting` | `toetsingsinkomen` |
| `BELASTINGDIENST` | `algemene_wet_inkomensafhankelijke_regelingen` | `has_partner`, `toetsingsinkomen` |
| `ZORGINSTITUUT` | `zorgverzekeringswet` | `is_verzekerd` |
| `SVB` | `algemene_ouderdomswet` | `pension_amount`, `is_eligible` |
| `UWV` | `werkloosheidswet` | `has_ww_benefit` |

## source_reference Format

For data from tables/databases:

```yaml
source_reference:
  table: "verzekerde_tijdvakken"      # Table name
  field: "woonperiodes"               # Single field
  select_on:                          # Filter criteria
    - name: "bsn"
      description: "BSN van de persoon"
      type: "string"
      value: "$BSN"
```

**With multiple fields:**
```yaml
source_reference:
  table: "income_records"
  fields:
    - "amount"
    - "year"
  select_on:
    - name: "bsn"
      type: "string"
      value: "$BSN"
```

**With source_type:**
```yaml
source_reference:
  source_type: "laws"         # "laws" (rules dataframe) or "events" (event store)
  table: "rules_table"
  field: "threshold"
```

## Eurocent Conversion Table

| Written Amount | Eurocent Value | Calculation |
|----------------|----------------|-------------|
| EUR 1 | 100 | 1 x 100 |
| EUR 10 | 1000 | 10 x 100 |
| EUR 100 | 10000 | 100 x 100 |
| EUR 795,47 | 79547 | 795.47 x 100 |
| EUR 1.758 | 175800 | 1758 x 100 |
| EUR 2.112 | 211200 | 2112 x 100 |
| EUR 25.889 | 2588900 | 25889 x 100 |
| EUR 39.719 | 3971900 | 39719 x 100 |
| EUR 79.547 | 7954700 | 79547 x 100 |
| EUR 154.859 | 15485900 | 154859 x 100 |
| EUR 1.000.000 | 100000000 | 1000000 x 100 |

**Conversion rules:**
1. Remove currency symbol
2. Remove thousands separators (`.` in Dutch notation)
3. Replace decimal comma (`,`) with decimal point
4. Multiply by 100
5. Result must be integer

**Dutch number format:**
- `.` = thousands separator (EUR 1.758 = one thousand seven hundred fifty-eight)
- `,` = decimal separator (EUR 795,47 = seven hundred ninety-five and 47 cents)

## Dutch Legal Phrases to Operations

| Dutch Legal Phrase | Operation |
|-------------------|-----------|
| "heeft bereikt de leeftijd van X jaar" | `GREATER_OR_EQUAL`, value: X |
| "ten minste X" / "minimaal X" | `GREATER_OR_EQUAL`, value: X |
| "niet meer dan X" / "ten hoogste X" | `LESS_OR_EQUAL`, value: X |
| "minder dan X" | `LESS_THAN`, value: X |
| "meer dan X" | `GREATER_THAN`, value: X |
| "gelijk aan X" | `EQUALS`, value: X |
| "vermenigvuldigd met" | `MULTIPLY` |
| "gedeeld door" | `DIVIDE` |
| "vermeerderd met" | `ADD` |
| "verminderd met" | `SUBTRACT` |
| "indien ... en ..." | `all` block or `AND` operation |
| "indien ... of ..." | `or` block or `OR` operation |
| "tenzij" / "behalve indien" | Negated condition |
| "ingevolge" / "krachtens" | Cross-law `service_reference` |
| "bedoeld in artikel X" | Reference to another part of the law |
| "voor zover" | Conditional (IF with conditions) |
| "naar rato van" | `DIVIDE` or proportional calculation |
| "het verschil tussen" | `SUBTRACT` |
| "het laagste van" | `MIN` |
| "het hoogste van" | `MAX` |

## Data Type Mapping

### Common Parameter Types

| Legal Concept | Name | Type |
|--------------|------|------|
| Citizen ID | `BSN` | `string` |
| Reference date | Use `$calculation_date` | (special variable) |

### Common Input Types

| Legal Concept | Name | Type | Service |
|--------------|------|------|---------|
| Age | `AGE` | `number` | RvIG / wet_brp |
| Birth date | `BIRTH_DATE` | `date` | RvIG / wet_brp |
| Insured status | `IS_VERZEKERD` | `boolean` | ZORGINSTITUUT / zorgverzekeringswet |
| Residence | `WOONT_IN_NEDERLAND` | `boolean` | RvIG / wet_brp |
| Partner status | `HAS_PARTNER` | `boolean` | BELASTINGDIENST / awir |
| Test income | `TOETSINGSINKOMEN` | `amount` | BELASTINGDIENST |
| Assets | `VERMOGEN` | `amount` | BELASTINGDIENST |

### Common Output Types

| Legal Concept | Name | Type | citizen_relevance |
|--------------|------|------|-------------------|
| Eligibility | `is_eligible` | `boolean` | `secondary` |
| Benefit amount | `hoogte_toeslag` | `amount` | `primary` |
| Pension amount | `pension_amount` | `amount` | `primary` |
| Below threshold | `onder_grens` | `boolean` | `secondary` |
| Percentage | `percentage` | `number` | `secondary` |

## Requirements vs Actions

**Requirements** are eligibility gates evaluated first:
- If ANY requirement fails, ALL outputs are empty
- Use for hard preconditions (age, insurance, residence)
- Support `all`/`or` nesting

**Actions** compute output values:
- Only execute if all requirements pass
- Engine auto-sorts by dependency order
- Support nested operations, IF, FOREACH

**Rule of thumb:**
- "heeft recht indien..." -> requirements
- "het bedrag bedraagt..." -> actions
- "komt in aanmerking als..." -> requirements
- "wordt berekend door..." -> actions

## File Location Convention

```
law/
  {law_name}/
    {SERVICE}-{YYYY-MM-DD}.yaml
```

Examples:
- `law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml`
- `law/algemene_ouderdomswet/SVB-2024-01-01.yaml`
- `law/participatiewet/bijstand/SZW-2023-01-01.yaml`
- `law/wet_brp/RvIG-2024-01-01.yaml`
