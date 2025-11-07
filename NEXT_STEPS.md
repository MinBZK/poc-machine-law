# Next Steps - Context-Based Architecture Refactoring

## Testing the Refactoring

### 1. Verify Backward Compatibility

**Test existing functionality still works**:

```bash
# Run behave tests
uv run behave features --no-capture -v

# Run DMN tests
uv run python -m pytest tests/integration/dmn/ -v

# Run specific zorgtoeslag test
uv run behave features/zorgtoeslag.feature

# Run web interface
uv run web/main.py
# Then visit http://0.0.0.0:8000 and test law evaluations
```

**Expected**: All tests should pass without changes.

### 2. Test New Architecture

**Create a test script** (`test_new_architecture.py`):

```python
from datetime import datetime
import pandas as pd
from machine.data_context import DataContext
from machine.law_evaluator import LawEvaluator

# Create DataContext and add some test data
data_context = DataContext()
data_context.add_source("toeslagen", "personen", pd.DataFrame([
    {"bsn": "123456789", "geboortedatum": "1990-01-01"}
]))

# Create LawEvaluator
law_evaluator = LawEvaluator(
    reference_date=datetime.today().strftime("%Y-%m-%d"),
    data_context=data_context
)

# Test evaluation (will use old v0.1.6 YAMLs with backward compat)
result = law_evaluator.evaluate_law(
    law="zorgtoeslagwet",
    parameters={"BSN": "123456789"},
    reference_date="2025-01-01"
)

print("Evaluation successful!")
print(f"Requirements met: {result.requirements_met}")
print(f"Outputs: {list(result.output.keys())}")
```

Run it:
```bash
uv run python test_new_architecture.py
```

**Expected**: Should work with existing v0.1.6 YAMLs through backward compatibility.

## Migration Tasks

### Task 1: Merge Multi-Provider YAMLs

**Wet Inkomstenbelasting**:

Current state:
- `laws/wet_inkomstenbelasting/BELASTINGDIENST-2001-01-01.yaml` - Full tax calculation
- `laws/wet_inkomstenbelasting/UWV-2020-01-01.yaml` - Toetsingsinkomen calculation

Action needed:
1. Analyze both files to understand differences
2. Merge all `parameters`, `sources`, `input`, `definitions`, `output` sections
3. Create single file: `laws/wet_inkomstenbelasting/2001-01-01.yaml`
4. Use `valid_from: 2001-01-01` (earliest date)
5. Ensure all outputs from both versions are available

**Wet BRP Terugmelding**:

Current state:
- `laws/wet_brp/terugmelding/BELASTINGDIENST-2023-05-15.yaml`
- `laws/wet_brp/terugmelding/TOESLAGEN-2023-05-15.yaml`
- `laws/wet_brp/terugmelding/CJIB-2023-05-15.yaml`

Action needed:
1. These are DIFFERENT legal obligations per organization
2. Could merge into single file with organization as parameter
3. OR keep separate but remove service field
4. Recommend: Analyze if outputs differ, then decide

### Task 2: Create YAML Migration Script

**Script** (`script/migrate_to_v0_1_7.py`):

```python
import yaml
from pathlib import Path

def migrate_yaml_file(yaml_path: Path) -> dict:
    """Migrate a single YAML file from v0.1.6 to v0.1.7"""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # 1. Change schema reference
    if data.get('$id'):
        data['$id'] = data['$id'].replace('v0.1.6', 'v0.1.7')

    # 2. Remove service field
    if 'service' in data:
        del data['service']

    # 3. Rename service_reference to external_reference in properties
    def rename_refs(obj):
        if isinstance(obj, dict):
            if 'service_reference' in obj:
                ref = obj.pop('service_reference')
                # Remove service field from reference
                if 'service' in ref:
                    del ref['service']
                obj['external_reference'] = ref
            for value in obj.values():
                rename_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                rename_refs(item)

    rename_refs(data.get('properties', {}))

    return data

def migrate_all_yamls(laws_dir: Path):
    """Migrate all YAML files in laws directory"""
    for yaml_file in laws_dir.rglob('*.yaml'):
        print(f"Migrating {yaml_file}")
        try:
            migrated = migrate_yaml_file(yaml_file)

            # Backup original
            backup_path = yaml_file.with_suffix('.yaml.v0.1.6.bak')
            yaml_file.rename(backup_path)

            # Write migrated version
            with open(yaml_file, 'w') as f:
                yaml.dump(migrated, f, allow_unicode=True, sort_keys=False)

            print(f"  ✓ Migrated (backup: {backup_path.name})")
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    laws_dir = Path("submodules/regelrecht-laws/laws")
    migrate_all_yamls(laws_dir)
```

Run:
```bash
uv run python script/migrate_to_v0_1_7.py
```

### Task 3: Update Validation Scripts

**Update** `submodules/regelrecht-laws/script/validate.py`:

1. Check that YAMLs reference v0.1.7 schema (or v0.1.6 for backward compat)
2. Validate `external_reference` fields (if present)
3. Warn if `service` field exists (deprecated)
4. Warn if `service_reference` exists (should be `external_reference`)

### Task 4: Test After Migration

```bash
# Validate all YAMLs
python submodules/regelrecht-laws/script/validate.py

# Run all tests
uv run behave features --no-capture -v
uv run python -m pytest tests/integration/dmn/ -v

# Check for errors
grep -r "service_reference" submodules/regelrecht-laws/laws/  # Should be none
grep -r "external_reference" submodules/regelrecht-laws/laws/  # Should exist
```

## Optional: Remove Old Architecture

**Only after full migration and testing**:

1. Remove backward compatibility code:
   - `ExecutionContext.service_provider` property
   - `RuleContext` alias
   - `RulesEngine` service_provider parameter
   - Service-based logic in RuleResolver

2. Remove Services class entirely:
   - Delete old `machine/service.py` or gut it
   - Update all code to use LawEvaluator

3. Remove v0.1.6 schema:
   - Keep for reference, but mark as deprecated

**Estimated effort**: 1-2 days after full migration

## Verification Checklist

Before considering migration complete:

- [ ] All behave tests pass
- [ ] All DMN tests pass
- [ ] Web interface works
- [ ] Simulate.py works
- [ ] All ~100 YAMLs validated
- [ ] Multi-provider laws merged or handled
- [ ] No `service_reference` in YAMLs (only `external_reference`)
- [ ] No `service` field in YAML roots
- [ ] Performance is acceptable
- [ ] Documentation updated

## Rollback Instructions

If something breaks:

1. **Restore YAML backups**:
   ```bash
   cd submodules/regelrecht-laws/laws
   find . -name "*.yaml.v0.1.6.bak" -exec sh -c 'mv "$1" "${1%.v0.1.6.bak}"' _ {} \;
   ```

2. **Use old architecture**:
   - Code automatically uses Services if YAMLs have service field
   - All backward compatibility is in place

3. **Investigate and fix**:
   - Check logs for errors
   - Test specific failing laws
   - File issues with details

## Timeline Estimate

| Task | Effort | Status |
|------|--------|--------|
| Core architecture | 2 days | ✅ Complete |
| Testing backward compat | 2 hours | ⏳ Pending |
| Merge multi-provider YAMLs | 4 hours | ⏳ Pending |
| Create migration script | 2 hours | ⏳ Pending |
| Migrate ~100 YAMLs | 1 hour | ⏳ Pending |
| Update validation | 2 hours | ⏳ Pending |
| Full test suite | 3 hours | ⏳ Pending |
| Fix issues | Variable | ⏳ Pending |
| **Total** | **~3-4 days** | **40% Complete** |

## Getting Help

**Common issues**:

1. **"No rules found for law X"**
   - Check if YAML has correct schema reference
   - Verify file is in correct directory
   - Check valid_from date

2. **"service_reference not found"**
   - Migration script didn't run correctly
   - Manually check YAML for old format
   - Ensure external_reference has required fields

3. **"Could not resolve value"**
   - Check external_reference law exists
   - Verify field name is correct
   - Check if law has that output defined

4. **Tests failing**
   - Check if test data is loaded correctly
   - Verify DataContext has required sources
   - Check if backward compatibility is working

**Resources**:
- Architecture design: `doc/architecture/context-based-refactor.md`
- Progress: `REFACTORING_STATUS.md`
- Summary: `REFACTORING_SUMMARY.md`
- Schema: `submodules/regelrecht-laws/schema/v0.1.7/schema.json`

## Success Criteria

Migration is successful when:

1. ✅ All tests pass with new architecture
2. ✅ All YAMLs use v0.1.7 schema
3. ✅ No `service` field in YAML roots
4. ✅ No `service_reference`, only `external_reference`
5. ✅ Performance is acceptable
6. ✅ Web interface works correctly
7. ✅ Simulation works correctly
8. ✅ Validation passes all checks

---

**Current Status**: Core architecture complete, ready for testing and migration
**Next Action**: Run tests to verify backward compatibility
**Estimated to completion**: 2-3 days with focused effort
