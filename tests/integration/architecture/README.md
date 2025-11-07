# Architecture Integration Tests

This directory contains pytest integration tests for the context-based architecture refactoring.

## Test Structure

- `test_data_context.py` - Tests for DataContext functionality (7 tests)
- `test_law_evaluator.py` - Tests for LawEvaluator functionality (9 tests)
- `test_backward_compatibility.py` - Tests for backward compatibility with Services (9 tests)
- `test_rule_resolver.py` - Tests for RuleResolver functionality (12 tests)

## Running Tests

Run all architecture tests:
```bash
uv run python -m pytest tests/integration/architecture/ -v
```

Run specific test file:
```bash
uv run python -m pytest tests/integration/architecture/test_data_context.py -v
```

Run specific test:
```bash
uv run python -m pytest tests/integration/architecture/test_data_context.py::TestDataContext::test_data_context_creation -v
```

## Test Coverage

### DataContext (7 tests)
- Creation and initialization
- Adding and retrieving data sources
- Access tracking
- Non-existent source handling
- Merging sources
- Checking source existence
- Multiple services management

### LawEvaluator (9 tests)
- Creation and initialization
- DataContext integration
- Simple law evaluation
- Engine caching
- Different dates/different engines
- Law not found error handling
- Input overrides
- Requested output
- Shared DataContext across evaluations

### Backward Compatibility (9 tests)
- Services class still works
- Services discovers laws correctly
- Services evaluate law (old architecture)
- Both architectures produce same results
- ExecutionContext has service_provider property
- RuleContext alias exists
- RulesEngine accepts both parameters
- v0.1.6 YAMLs still work
- RuleResolver handles optional service

### RuleResolver (12 tests)
- Loads rules from YAML files
- Discovers services
- Rules have required fields
- Find rule with service
- Find rule without service
- Non-existent rule handling
- Get rule spec returns dict
- Generate rules dataframe
- Service laws structure
- Discoverable laws tracking
- Windows symlink handling
- Multiple versions of same law

## Fixtures

See `tests/integration/conftest.py` for shared fixtures:
- `reference_date` - Default reference date (2025-01-01)
- `data_context` - Fresh DataContext for each test
- `law_evaluator` - Session-scoped LawEvaluator
- `services` - Session-scoped Services instance
- `sample_person_data` - Sample person dataframe
- `sample_brp_data` - Sample BRP registration dataframe

## Notes

- `law_evaluator` and `services` fixtures are session-scoped to avoid event sourcing TopicError
- Tests that use session-scoped fixtures should clear caches/data before use
- All tests are independent and can run in any order

## Test Results

All 37 tests pass successfully, confirming:
- New architecture components work correctly
- Backward compatibility is maintained
- Windows symlink issue is fixed
- Law evaluation produces correct results
