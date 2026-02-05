# Feature Files

This directory contains Gherkin feature files for testing Dutch law implementations.

## Naming Convention

Feature files follow the pattern: `law_SERVICE-DATE.feature`

- **law**: The law or regulation being tested (e.g., `zorgtoeslagwet`, `werkloosheidswet`)
- **SERVICE**: The executing service in UPPER_CASE (e.g., `TOESLAGEN`, `UWV`, `SVB`)
- **DATE**: The reference date for the law version (e.g., `2025-01-01`)

Examples:
- `zorgtoeslagwet_TOESLAGEN-2025-01-01.feature`
- `werkloosheidswet_UWV-2025-01-01.feature`
- `algemene_ouderdomswet_SVB-2024-01-01.feature`

Cross-cutting test files (case management, integration tests) may omit the service/date suffix.

## Tags

- `@skip-go` - Feature runs only in Python (no Go step definitions yet)
- `@ui` - Requires Playwright browser installation; skipped by default in CI

## Running Tests

```bash
# Python (behave)
uv run behave features --no-capture -v

# Go (godog)
cd features && go test -v .
```

## Generic Step Patterns

Use these patterns for assertions:

```gherkin
# Input data
Given de volgende <SERVICE> <category> gegevens:
  | field1 | field2 |
  | value1 | value2 |

Given de datum is "2024-01-01"
Given een persoon met BSN "123456789"

# Execution
When de <law> wordt uitgevoerd door <SERVICE>

# Output assertions
Then heeft de output "<field>" waarde "<value>"
Then bevat de output "<field>" waarde "<value>"
Then bevat de output "<field>" niet de waarde "<value>"
Then is de output "<field>" leeg
Then is voldaan aan de voorwaarden
Then is niet voldaan aan de voorwaarden
```

## Directory Structure

```
features/
├── *.feature          # Active, passing feature files
├── steps/             # Python step definitions
├── godogs_test.go     # Go step definitions
└── README.md          # This file
```

## Adding New Features

1. Create the YAML law definition in `laws/`
2. Write a feature file following the naming convention above
3. Use generic step patterns where possible
4. Run both Python and Go tests to verify
5. Only commit if both engines pass (or add `@skip-go` if Go steps are missing)
