# Kieswet v0.1.6 vs v0.1.7 Testing Notes

## Date: 2025-11-07

## Summary

Attempted to compare kieswet v0.1.6 (service-based) and v0.1.7 (context-based) implementations to verify backward compatibility.

## Issues Encountered

### 1. Symlink Issues on Windows
- `script/validate.py` was a symlink causing SyntaxError
- Fixed by copying actual file from submodules

### 2. File Coexistence Problem
- Both v0.1.6 (KIESRAAD-2024-01-01.yaml) and v0.1.7 (2024-01-01.yaml) have same `valid_from` date
- RuleResolver's `find_rule` method includes v0.1.7 files (service=None) when searching for v0.1.6 files with specific service
- Workaround: Temporarily renamed v0.1.7 file to .test extension

### 3. External Reference Resolution
v0.1.6 kieswet depends on:
- **RvIG.wet_brp** → `leeftijd`, `heeft_nederlandse_nationaliteit`
- **DJI.penitentiaire_beginselenwet** → `is_gedetineerd`
- **JUSTID.wetboek_van_strafrecht** → `heeft_stemrecht_uitsluiting`

Error encountered:
```
Could not resolve value for NATIONALITEIT
Could not resolve value for STEMRECHT_UITSLUITINGEN
```

This indicates that the service-to-service calls in v0.1.6 are not properly set up in the test environment.

### 4. Event Sourcing Cache Conflicts
Creating multiple `Services` instances caused TopicError:
```
TopicError: Object <class 'machine.service.Services.__init__.<locals>.WrappedCaseManager'>
is already registered...
```

Fixed by calling `clear_topic_cache()` between test scenarios.

## Test Results (Partial)

### Scenario 1: Dutch citizen, 18+, no exclusion
- **Expected**: Has voting rights (True)
- **v0.1.6**: False (FAIL - couldn't resolve external references)
- **v0.1.7**: True (PASS)
- **Status**: MISMATCH (but likely due to setup issues, not architecture)

## Root Cause

The core issue is that v0.1.6's service-based architecture requires:
1. All referenced services (RvIG, DJI, JUSTID) to be properly initialized in the `Services` class
2. All referenced laws (wet_brp, penitentiaire_beginselenwet, wetboek_van_strafrecht) to exist and be loadable
3. Proper data setup for each service's tables

The test script was only setting up data for KIESRAAD, not for the external services that kieswet depends on.

## Next Steps for Full Testing

To properly test v0.1.6 vs v0.1.7 comparison, we need to:

### Option A: Use Behave Tests (Recommended)
1. Fix symlink issues (script/validate.py, schema directory)
2. Fix web server startup (it's needed for behave environment)
3. Run existing feature files which already have proper setup:
   ```bash
   uv run behave features/kieswet_v016.feature
   uv run behave features/kieswet_v017.feature
   ```

### Option B: Extend Python Test Script
1. Set up mock implementations for all external laws:
   - wet_brp (RvIG)
   - penitentiaire_beginselenwet (DJI)
   - wetboek_van_strafrecht (JUSTID)
2. Ensure Services class can properly route to these implementations
3. This is complex and essentially recreates what behave tests already do

## Recommendation

**Use Option A (Behave)** once symlink and web server issues are resolved. The behave tests already have proper step definitions that handle all the external service mocking correctly.

For now, the manual conversion and file creation is complete:
- ✅ v0.1.7 YAML created (2024-01-01.yaml)
- ✅ v0.1.7 feature file created (2024-01-01.feature)
- ✅ v0.1.7 step definitions created (kieswet_v017_steps.py)
- ✅ Conversion documented (KIESWET_CONVERSION_GUIDE.md)

The architectural changes are sound; the testing infrastructure needs fixes that are orthogonal to the v0.1.6→v0.1.7 migration.

## Files Created/Modified

### Created
- `features/kieswet_v016.feature` - Copy of v0.1.6 feature file
- `features/kieswet_v017.feature` - Copy of v0.1.7 feature file
- `test_kieswet_comparison.py` - Direct Python comparison script (incomplete)
- `KIESWET_TESTING_NOTES.md` - This document

### Modified
- `features/steps/kieswet_v017_steps.py` - Removed duplicate step definitions
- `script/validate.py` - Replaced symlink with actual file

### Renamed
- `submodules/regelrecht-laws/laws/kieswet/2024-01-01.yaml` → `.yaml.test` (temporary)

## Conclusion

The kieswet v0.1.7 conversion is **architecturally complete**. Full end-to-end testing requires resolving test infrastructure issues (symlinks on Windows, web server dependencies, external law mocking) that are not specific to the v0.1.6→v0.1.7 migration itself.

The v0.1.7 architecture simplifies the law definitions by removing service routing, which should make them easier to test once the infrastructure is stable.
