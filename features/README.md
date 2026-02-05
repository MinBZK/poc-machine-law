# Feature Files

This directory contains Gherkin feature files for testing Dutch law implementations.

## Convention

- All features in `features/` **MUST pass** without skip tags
- Use generic step patterns (see below)
- Use `@skip-go` tag for features that only work in Python (no Go step definitions)
- Before merging: ensure tests pass in BOTH Python and Go (or use `@skip-go`)

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
2. Write a feature file using generic step patterns
3. Run both Python and Go tests to verify
4. Only commit if both engines pass
