# Law Comparison Report

**Law A**: TOESLAGEN-2024-01-01.yaml
**Law B**: TOESLAGEN-2025-01-01.yaml
**Comparison Date**: 2025-10-10

## Legal Basis

### Law B
- **Law**: Zorgtoeslagwet
- **Article**: 2
- **URL**: https://wetten.overheid.nl/BWBR0018451/2025-01-01/0/Artikel2
- **Explanation**: Artikel 2 stelt de algemene regels voor de zorgtoeslag vast: recht op toeslag wanneer de normpremie lager is dan de standaardpremie

## Structural Differences

### Metadata Changes
- **valid_from**: 2024-01-01 → 2025-01-01
- **uuid**: 5be9dbe7-f565-40e2-8931-da82825dcf21 → 60e71675-38bc-4297-87ac-0c145613e481

### Modified Definitions
- **PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND**: 0.0486 → 0.01896
- **VERMOGENSGRENS_ALLEENSTAANDE**: 14193900 → 14189600
- **PERCENTAGE_DREMPELINKOMEN_MET_PARTNER**: 0.0486 → 0.04273
- **DREMPELINKOMEN_ALLEENSTAANDE**: 3749600 → 3971900
- **DREMPELINKOMEN_TOESLAGPARTNER**: 4821800 → 5020600
- **AFBOUWPERCENTAGE_MINIMUM**: 0.1367 → 0.137
- **AFBOUWPERCENTAGE_BOVEN_DREMPEL**: 0.0387 → 0.137

### Input Changes
- **Added**: IS_VERZEKERDE
- **Removed**: HEEFT_VERZEKERING, HEEFT_VERDRAGSVERZEKERING, IS_GEDETINEERD, IS_FORENSISCH
- **Modified**: HEEFT_PARTNER, LEEFTIJD, INKOMEN, VERMOGEN, STANDAARDPREMIE, PARTNER_INKOMEN, GEZAMENLIJK_VERMOGEN

### Output Changes
- **Modified**: hoogte_toeslag, is_verzekerde_zorgtoeslag
