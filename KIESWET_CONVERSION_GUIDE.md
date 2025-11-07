# Kieswet Conversion to v0.1.7 Schema

## Date: 2025-11-07

## Overview

This document describes the conversion of the kieswet (Electoral Law) from v0.1.6 (service-based) to v0.1.7 (context-based) schema.

## Files Created

### YAML Files
1. **Original (v0.1.6)**: `submodules/regelrecht-laws/laws/kieswet/KIESRAAD-2024-01-01.yaml`
2. **New (v0.1.7)**: `submodules/regelrecht-laws/laws/kieswet/2024-01-01.yaml`

### Feature Files
1. **Original (v0.1.6)**: `submodules/regelrecht-laws/laws/kieswet/KIESRAAD-2024-01-01.feature`
2. **New (v0.1.7)**: `submodules/regelrecht-laws/laws/kieswet/2024-01-01.feature`

### Step Definitions
1. **Original (v0.1.6)**: Uses `features/steps/steps.py` (Services-based)
2. **New (v0.1.7)**: `features/steps/kieswet_v017_steps.py` (LawEvaluator-based)

## Key Changes

### 1. Schema Reference
```yaml
# v0.1.6
$id: https://.../schema/v0.1.6/schema.json

# v0.1.7
$id: https://.../schema/v0.1.7/schema.json
```

### 2. Service Field Removed
```yaml
# v0.1.6
service: "KIESRAAD"

# v0.1.7
# (no service field - context-based!)
```

### 3. service_reference → external_reference
```yaml
# v0.1.6
input:
  - name: "LEEFTIJD"
    service_reference:
      service: "RvIG"
      law: "wet_brp"
      field: "leeftijd"

# v0.1.7
input:
  - name: "LEEFTIJD"
    external_reference:
      law: "wet_brp"
      field: "leeftijd"
      # No service field!
```

### 4. Filename Convention
```
# v0.1.6
{SERVICE}-{YYYY-MM-DD}.yaml
KIESRAAD-2024-01-01.yaml

# v0.1.7
{YYYY-MM-DD}.yaml
2024-01-01.yaml
```

## Test Architecture Differences

### v0.1.6 Tests (Service-Based)

**Step Setup:**
```python
@given("de volgende KIESRAAD verkiezingen gegevens")
def step_impl(context, service, table):
    # Uses Services class
    context.services.set_source_dataframe("KIESRAAD", "verkiezingen", df)

@when("de kieswet wordt uitgevoerd door KIESRAAD")
def step_impl(context):
    # Calls Services.evaluate with service parameter
    result = context.services.evaluate(
        service="KIESRAAD",
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=context.date
    )
```

### v0.1.7 Tests (Context-Based)

**Step Setup:**
```python
@given("de volgende verkiezingen gegevens")
def step_impl(context):
    # Uses LawEvaluator with DataContext
    context.law_evaluator.data_context.add_source("KIESRAAD", "verkiezingen", df)
    # Note: Still uses "KIESRAAD" as source_name for data organization

@when("de kieswet v0.1.7 wordt uitgevoerd")
def step_impl(context):
    # Calls LawEvaluator.evaluate_law WITHOUT service parameter
    result = context.law_evaluator.evaluate_law(
        law="kieswet",
        parameters={"BSN": bsn},
        reference_date=context.date
    )
```

## External References in Kieswet

The kieswet references three external laws:

### 1. wet_brp (Basic Registration of Persons)
- **Fields**: `leeftijd`, `heeft_nederlandse_nationaliteit`
- **Provider**: RvIG
- **Purpose**: Get age and nationality

### 2. penitentiaire_beginselenwet (Prison Principles Act)
- **Field**: `is_gedetineerd`
- **Provider**: DJI
- **Purpose**: Check detention status (note: detention alone doesn't exclude voting rights)

### 3. wetboek_van_strafrecht (Criminal Code)
- **Field**: `heeft_stemrecht_uitsluiting`
- **Provider**: JUSTID
- **Purpose**: Check if voting rights were revoked by court

## Data Flow Comparison

### v0.1.6 (Service-Based)
```
User Input
  ↓
Services.evaluate(service="KIESRAAD", law="kieswet", ...)
  ↓
RuleService["KIESRAAD"].evaluate(law="kieswet", ...)
  ↓
RulesEngine.evaluate()
  ↓
ExecutionContext._resolve_from_service()
  ├─→ Services["RvIG"].evaluate(law="wet_brp", ...)  (for age/nationality)
  ├─→ Services["DJI"].evaluate(law="penitentiaire_beginselenwet", ...)  (for detention)
  └─→ Services["JUSTID"].evaluate(law="wetboek_van_strafrecht", ...)  (for exclusion)
  ↓
Result
```

### v0.1.7 (Context-Based)
```
User Input
  ↓
LawEvaluator.evaluate_law(law="kieswet", ...)
  ↓
RulesEngine.evaluate()
  ↓
ExecutionContext._resolve_from_external()
  ├─→ LawEvaluator.evaluate_law(law="wet_brp", ...)  (for age/nationality)
  ├─→ LawEvaluator.evaluate_law(law="penitentiaire_beginselenwet", ...)  (for detention)
  └─→ LawEvaluator.evaluate_law(law="wetboek_van_strafrecht", ...)  (for exclusion)
  ↓
Result
```

## Running Tests

### v0.1.6 Tests
```bash
uv run behave submodules/regelrecht-laws/laws/kieswet/KIESRAAD-2024-01-01.feature
```

### v0.1.7 Tests
```bash
uv run behave submodules/regelrecht-laws/laws/kieswet/2024-01-01.feature
```

### Compare Results
Run both and verify outputs are identical to confirm backward compatibility.

## Expected Behavior

Both versions should produce identical results:

| Scenario | Expected Result |
|----------|----------------|
| Dutch citizen, 18+, no exclusion | ✓ Has voting rights |
| Non-Dutch citizen | ✗ No voting rights |
| Under 18 years old | ✗ No voting rights |
| Court-ordered exclusion | ✗ No voting rights |
| Detained (no exclusion) | ✓ Has voting rights |

## Benefits of v0.1.7

1. **Simpler**: No service routing needed
2. **More flexible**: Data can come from any source in DataContext
3. **Clearer intent**: Law references law directly, not via service
4. **Easier to maintain**: One less dimension to track (service)
5. **Better testability**: Easier to mock external law calls

## Notes

- The v0.1.6 version remains functional (backward compatibility)
- Both versions can coexist during migration
- Test both versions to ensure identical behavior
- Once validated, v0.1.6 can be deprecated

## Next Steps

1. Run both feature tests
2. Compare outputs
3. If identical, mark conversion as successful
4. Document any differences found
5. Use as template for converting other laws
