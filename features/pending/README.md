# Pending Features

This directory contains feature files that are work-in-progress and not yet ready for CI.

## Why Features Are Here

Features in this directory typically need one of the following:

1. **Missing step definitions** - The feature uses domain-specific steps that haven't been implemented
2. **Go engine parity** - Python steps exist but Go equivalents are missing
3. **Law logic incomplete** - The underlying YAML law definition needs work
4. **Refactoring needed** - Features need to be rewritten to use generic step patterns

## Moving Features Back to Main

To graduate a feature from `pending/` to the main directory:

1. Ensure all step definitions exist in both Python and Go
2. Rewrite domain-specific steps to use generic patterns:

   **Before (broken):**
   ```gherkin
   Given een archiefstuk met de volgende eigenschappen:
     | archiefstuk_id | aanmaakdatum |
     | DOC-001        | 2003-01-01   |
   Then is het veld "vergunning_vereist" gelijk aan "true"
   ```

   **After (working):**
   ```gherkin
   Given de volgende NATIONAAL_ARCHIEF archiefstukken gegevens:
     | archiefstuk_id | aanmaakdatum |
     | DOC-001        | 2003-01-01   |
   Then heeft de output "vergunning_vereist" waarde "true"
   ```

3. Run tests in both Python and Go:
   ```bash
   uv run behave features/pending/<file>.feature
   cd features && go test -v -run <scenario>
   ```

4. Move the file to `features/` (not `features/pending/`)
5. Verify CI passes

## Feature Status

| Feature | Issue | Priority |
|---------|-------|----------|
| zorgtoeslag-related | Missing service config | High |
| BELASTINGDIENST-* | Multiple missing steps | Medium |
| SVB-*, UWV-* | Service integration | Medium |
| burgerlijk_wetboek_* | Specialized domain | Low |
| kernenergiewet_* | Specialized domain | Low |
