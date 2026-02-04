# Laws Directory

This directory contains law definitions imported from the regelrecht-laws repository.

**Source**: https://github.com/MinBZK/regelrecht-laws
**Imported from**: origin/main branch
**Commit**: 3401c045b78cb2e3b4c61f1c887d043730febafa
**Import date**: 2026-02-04
**Status**: regelrecht-laws repository is archived; laws are now maintained in this repository

## Contents

This directory contains 50+ law definitions organized by topic, including:
- Zorgtoeslagwet (healthcare allowance)
- Wet op de huurtoeslag (housing allowance)
- Wet kinderopvang (childcare)
- Pensioenwet (pension)
- And many more...

Each law definition includes:
- YAML files with versioned definitions (e.g., TOESLAGEN-2025-01-01.yaml)
- Feature files (Gherkin format) for behavior-driven testing

## Schema

Law definitions follow the schema defined in the `/schema` directory (v0.1.7).
Use `/script/validate.py` to validate law YAML files against the schema.
