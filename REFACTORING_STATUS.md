# Context-Based Architecture Refactoring Status

## Overview

This document tracks the progress of refactoring from a service-based routing architecture to a context-based architecture. This is a **breaking change** that affects all law YAML files and the core evaluation engine.

## Completed ✅

### 1. Core Architecture Components

**DataContext** (`machine/data_context.py`)
- ✅ Created new class for managing all data sources
- ✅ Organizes data by source_name/table_name (e.g., `toeslagen/personen`, `brp/inschrijvingen`)
- ✅ Provides add/get/merge methods for data management
- ✅ Tracks data access for auditing

**LawEvaluator** (`machine/law_evaluator.py`)
- ✅ Created orchestrator for law evaluations
- ✅ Replaces Services/RuleService classes
- ✅ Manages shared DataContext
- ✅ Maintains law registry via RuleResolver
- ✅ Caches engines by (law, reference_date)
- ✅ Backward-compatible methods for event sourcing

**ExecutionContext** (`machine/context.py`)
- ✅ Renamed from RuleContext
- ✅ Added `law_evaluator` and `data_context` fields
- ✅ Removed `service_name` field (deprecated)
- ✅ Added `_resolve_from_external()` method for new external_reference
- ✅ Added `_resolve_from_service_via_evaluator()` for backward compat
- ✅ Added `service_provider` property for backward compatibility
- ✅ Supports both old service_reference and new external_reference

### 2. Engine Updates

**RulesEngine** (`machine/engine.py`)
- ✅ Accepts both `service_provider` (deprecated) and `law_evaluator` (new)
- ✅ Creates ExecutionContext with law_evaluator and data_context
- ✅ Supports reference_date alias for calculation_date
- ✅ Handles claims lookup without service parameter
- ✅ Full backward compatibility maintained

**RuleResolver** (`machine/utils.py`)
- ✅ Made `service` field optional in RuleSpec
- ✅ Updated `find_rule()` to handle service=None
- ✅ Supports both v0.1.6 (with service) and v0.1.7 (without service)
- ✅ Maps rules without service to "ALL" pseudo-service
- ✅ Updated rules_dataframe() to handle None service values

### 3. Schema

**Schema v0.1.7** (`submodules/regelrecht-laws/schema/v0.1.7/schema.json`)
- ✅ Removed `service` from required fields
- ✅ Renamed `serviceReference` to `externalReference`
- ✅ Removed `service` field from externalReference definition
- ✅ Title changed from "Dutch Government Service Definition" to "Dutch Government Law Definition"

### 4. Documentation

**Architecture Design** (`doc/architecture/context-based-refactor.md`)
- ✅ Complete design document with migration strategy
- ✅ Component responsibilities documented
- ✅ Data source naming conventions
- ✅ Migration path outlined

## Pending ⏳

### 5. YAML Files Migration

**Multi-Provider Laws** - Analysis and decisions:
- [ ] **wet_inkomstenbelasting**: KEEP SPLIT - BELASTINGDIENST (full tax calculation) vs UWV (toetsingsinkomen for benefits) serve different purposes. Update separately to v0.1.7.
- [ ] **wet_brp/terugmelding**: ANALYSIS NEEDED - Check if BELASTINGDIENST, TOESLAGEN, CJIB versions actually differ or if they're identical logic with different service labels. May be candidates for merging if identical.

**Schema Migration** - Update ~100 YAML files:
- [ ] Change `$id` to point to v0.1.7 schema
- [ ] Remove `service` field from root
- [ ] Rename `service_reference` to `external_reference`
- [ ] Remove `service` field from all references

### 6. Integration Points

**Web Interface** (`web/engines/factory.py`, etc.)
- [ ] Replace `Services` instantiation with `LawEvaluator`
- [ ] Update profile loading to populate DataContext
- [ ] Update HTTP engine integration

**Testing** (`features/steps/steps.py`, `simulate.py`)
- [ ] Update test fixtures to use LawEvaluator
- [ ] Update simulation scripts
- [ ] Fix law_parameter_config.py references

**Validation** (`submodules/regelrecht-laws/script/validate.py`)
- [ ] Update to check v0.1.7 schema compliance
- [ ] Validate external_reference correctness
- [ ] Ensure no service field exists

### 7. Testing & Verification

- [ ] Run behave tests
- [ ] Run DMN tests
- [ ] Run integration tests
- [ ] Validate all law files
- [ ] Performance testing

## Backward Compatibility

The refactoring maintains **full backward compatibility** during transition:

1. **ExecutionContext** has `service_provider` property that points to `law_evaluator`
2. **RuleContext** is aliased to `ExecutionContext`
3. **RulesEngine** accepts both `service_provider` and `law_evaluator`
4. **RuleResolver** handles both v0.1.6 (with service) and v0.1.7 (without service)
5. **Service references** are converted to external references transparently
6. Old **Services** class can coexist with new **LawEvaluator**

## Breaking Changes (When YAML migration completes)

1. **Schema version**: v0.1.6 → v0.1.7
2. **All YAML files** must be updated
3. **Service field** removed from law definitions
4. **service_reference** renamed to **external_reference**
5. **Multi-provider laws** consolidated

## Migration Commands

### Merge Multi-Provider YAMLs
```bash
# Wet inkomstenbelasting
# TODO: Create script to merge BELASTINGDIENST and UWV versions

# Wet BRP terugmelding
# TODO: Create script to merge BELASTINGDIENST, TOESLAGEN, CJIB versions
```

### Update All YAMLs to v0.1.7
```bash
# TODO: Create script to:
# 1. Change schema $id
# 2. Remove service field
# 3. Rename service_reference to external_reference
# 4. Remove service from references
```

### Validate
```bash
python submodules/regelrecht-laws/script/validate.py
```

## Testing Strategy

1. **Unit tests**: Test each new component in isolation
2. **Integration tests**: Test ExecutionContext with LawEvaluator
3. **Backward compat tests**: Ensure old code still works
4. **YAML migration tests**: Validate each migrated file
5. **End-to-end tests**: Run full behave test suite

## Rollback Plan

If issues arise:
1. Revert YAML files to v0.1.6
2. Continue using Services class
3. Keep new components (they don't break anything)
4. Address issues incrementally

## Key Benefits

1. **Simpler architecture**: No service routing layers
2. **Better separation**: Data, execution, orchestration are separate
3. **Easier to understand**: Context-based is more intuitive
4. **Flexible data access**: No organizational boundaries
5. **Reduced coupling**: Laws don't need to know service details

## Timeline Estimate

- ✅ **Week 1**: Core components (DataContext, LawEvaluator, ExecutionContext) - **COMPLETED**
- ✅ **Week 2**: Engine and resolver updates - **COMPLETED**
- ⏳ **Week 3**: YAML merging and migration - **IN PROGRESS**
- ⏳ **Week 4**: Integration points (web, tests, validation)
- ⏳ **Week 5**: Testing and bug fixes
- ⏳ **Week 6**: Documentation and cleanup

## Contact

For questions about this refactoring, see:
- Design doc: `doc/architecture/context-based-refactor.md`
- Schema: `submodules/regelrecht-laws/schema/v0.1.7/schema.json`
- Components: `machine/data_context.py`, `machine/law_evaluator.py`, `machine/context.py`
