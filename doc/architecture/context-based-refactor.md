# Context-Based Architecture Refactor

## Overview

This document describes the refactoring from a service-based routing architecture to a context-based architecture.

## Current Architecture (v0.1.6)

```
User/API
  ↓
Services (router)
  ↓
RuleService (per service)
  ↓
RulesEngine
  ↓
RuleContext
  ├→ service_provider (calls back to Services)
  ├→ sources (local dataframes per service)
  └→ resolve_value()
      └→ _resolve_from_service() → Services.evaluate()
```

### Problems

1. **Tight coupling**: Laws must know which service executes another law
2. **Service routing complexity**: Multi-layer service routing (Services → RuleService → Engine)
3. **Multi-provider confusion**: Same law can have multiple service versions, requires explicit service selection
4. **Data fragmentation**: Data is split per service, not accessible globally

## New Architecture (v0.1.7)

```
User/API
  ↓
LawEvaluator (orchestrator)
  ├→ DataContext (shared data sources)
  └→ RuleResolver (law registry)
      ↓
      RulesEngine (per law)
        ↓
        ExecutionContext
          ├→ law_evaluator (references back to LawEvaluator)
          ├→ data_context (shared)
          └→ resolve_value()
              └→ _resolve_from_external() → LawEvaluator.evaluate_law()
```

### Benefits

1. **Loose coupling**: Laws reference other laws without knowing execution details
2. **Simplified routing**: Single orchestrator layer
3. **Unified data access**: All data available through shared DataContext
4. **Clear separation**: Data, execution state, and orchestration are separate

## Component Responsibilities

### DataContext

**Responsibility**: Manage all data sources

**Contains**:
- `sources: dict[str, dict[str, pd.DataFrame]]` - Keyed by source_name/table_name
- `claims: dict[str, Claim]` - Event sourcing claims
- Methods to fetch data on-demand

**Example**:
```python
data_context = DataContext()
data_context.add_source("belastingdienst", "personen", df_personen)
data_context.add_source("brp", "inschrijvingen", df_inschrijvingen)

# Access data
df = data_context.get_source("belastingdienst", "personen")
```

### LawEvaluator

**Responsibility**: Orchestrate law evaluations

**Contains**:
- `resolver: RuleResolver` - Law registry
- `data_context: DataContext` - Shared data
- `_engines: dict[str, dict[str, RulesEngine]]` - Cached engines
- Event sourcing managers (case_manager, claim_manager)

**Key method**:
```python
def evaluate_law(
    self,
    law: str,
    reference_date: str,
    parameters: dict[str, Any],
    requested_output: str | None = None,
    **kwargs
) -> LawResult:
    # Get or create engine for law
    engine = self._get_engine(law, reference_date)

    # Evaluate using shared data context
    return engine.evaluate(
        parameters=parameters,
        data_context=self.data_context,
        law_evaluator=self,
        requested_output=requested_output,
        **kwargs
    )
```

### ExecutionContext

**Responsibility**: Manage state for a single law execution

**Contains**:
- `definitions: dict` - Current law's definitions
- `parameters: dict` - Input parameters
- `outputs: dict` - Computed outputs
- `data_context: DataContext` - Reference to shared data
- `law_evaluator: LawEvaluator` - Reference to orchestrator
- `values_cache: dict` - Resolution cache
- `path: list[PathNode]` - Execution trace

**Key methods**:
```python
def resolve_value(self, path: str) -> Any:
    # Resolves $variables, including external_reference

def _resolve_from_external(self, path, external_ref, spec):
    # Calls law_evaluator.evaluate_law() for law-to-law references
```

## Migration Path

### Schema Changes (v0.1.6 → v0.1.7)

**Root level**:
- Remove `service` from required fields
- Remove `service` field entirely

**Property types**:
- Rename `service_reference` to `external_reference`
- Remove `service` field from `externalReference` definition

**Before** (v0.1.6):
```yaml
$id: .../schema/v0.1.6/schema.json
uuid: ...
name: "Zorgtoeslag"
law: zorgtoeslagwet
service: "TOESLAGEN"  # ← REMOVED
properties:
  input:
    - name: "INKOMEN"
      service_reference:  # ← RENAMED to external_reference
        service: "UWV"    # ← REMOVED
        law: "wet_inkomstenbelasting"
        field: "inkomen"
```

**After** (v0.1.7):
```yaml
$id: .../schema/v0.1.7/schema.json
uuid: ...
name: "Zorgtoeslag"
law: zorgtoeslagwet
# No service field
properties:
  input:
    - name: "INKOMEN"
      external_reference:  # ← RENAMED
        law: "wet_inkomstenbelasting"
        field: "inkomen"
        # No service field
```

### Multi-Provider Laws

Laws with multiple service versions will be merged:

**Before**:
```
laws/wet_inkomstenbelasting/
  BELASTINGDIENST-2001-01-01.yaml  # Full tax calculation
  UWV-2020-01-01.yaml              # Toetsingsinkomen calculation
```

**After**:
```
laws/wet_inkomstenbelasting/
  2001-01-01.yaml  # Contains both outputs, references appropriate data sources
```

**Merged content strategy**:
- Combine all `parameters`, `sources`, `input`, `definitions`, `output` sections
- Different outputs can reference different data sources in DataContext
- Use source_reference to specify which data source table to use

### Code Migration

**Phase 1: Create new components**
1. Create `DataContext` class
2. Create `LawEvaluator` class
3. Rename `RuleContext` → `ExecutionContext`

**Phase 2: Update core**
1. Update `RuleResolver` to work without service parameter
2. Update `RulesEngine` to use new architecture
3. Update `ExecutionContext._resolve_from_service` → `_resolve_from_external`

**Phase 3: Update YAMLs**
1. Create schema v0.1.7
2. Merge multi-provider YAMLs
3. Update all ~100 YAML files

**Phase 4: Update integrations**
1. Web interface factories
2. Test files
3. Simulation scripts
4. Validation scripts

**Phase 5: Testing**
1. Run behave tests
2. Run DMN tests
3. Fix failures
4. Validate all laws

## Data Source Naming

Organizations become data source prefixes in the context:

| Old Service Name | New Data Source Prefix | Example Tables |
|-----------------|------------------------|----------------|
| TOESLAGEN | toeslagen | personen, berekeningen |
| BELASTINGDIENST | belastingdienst | personen, aanslagen |
| UWV | uwv | personen, uitkeringen |
| RvIG | brp | inschrijvingen, addresses |
| KADASTER | bag | verblijfsobjecten, panden |

**Source reference example**:
```yaml
sources:
  - name: "GEBOORTEDATUM"
    type: "date"
    source_reference:
      table: "personen"  # Will look up in data_context
      field: "geboortedatum"
      select_on:
        - name: "bsn"
          value: "$BSN"
```

The DataContext will be populated with data keyed by source name, and the `source_reference` will specify which table to query from the available sources.

## Timeline

1. **Week 1**: Create new components (DataContext, LawEvaluator, ExecutionContext)
2. **Week 2**: Update core engine and resolver
3. **Week 3**: Create schema v0.1.7 and merge multi-provider YAMLs
4. **Week 4**: Update all YAML files (scripted)
5. **Week 5**: Update integrations and tests
6. **Week 6**: Testing and bug fixes

## Open Questions

1. **Data source discovery**: How should ExecutionContext know which data sources are available?
   - **Answer**: DataContext maintains registry of available sources

2. **Source reference validation**: Should we validate that source_reference tables exist in DataContext?
   - **Answer**: Yes, validate at evaluation time with helpful error messages

3. **Backward compatibility**: Do we need to support v0.1.6 YAMLs during transition?
   - **Answer**: No, breaking change - all YAMLs updated at once

4. **Performance**: Will shared DataContext impact performance vs per-service dataframes?
   - **Answer**: Should be faster - single lookup instead of service routing
