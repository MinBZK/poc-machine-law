# Law Comparison Tools

Dit directory bevat tools voor het analyseren en vergelijken van machine law implementaties.

## compare_laws.py

Een tool die twee sets YAML wetbestanden structureel vergelijkt.

### Functionaliteit

1. **Structurele Analyse** - Vergelijkt YAML structuur:
   - Metadata (namen, datums, UUIDs)
   - Definitions (constanten) met legal_basis
   - Inputs en outputs met legal_basis
   - Legal basis referenties voor alle wijzigingen

2. **File Set Matching**:
   - Accepteert directories, glob patterns, of enkele bestanden
   - Matched wetten automatisch op basis van service en law naam
   - Vergelijkt meerdere wetten tegelijk

3. **Legal Basis Tracking**:
   - Extraheert legal_basis (wet, artikel, lid) voor elke wijziging
   - Toont relevante wetgeving per definitie, input, en output
   - Formaat: *(Wet naam, Art. X, lid Y)*

### Gebruik

#### Basis - Twee enkele bestanden

```bash
uv run python tools/compare_laws.py \
  --set-a law/zorgtoeslagwet/TOESLAGEN-2024-01-01.yaml \
  --set-b law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml
```

#### Directories vergelijken

```bash
uv run python tools/compare_laws.py \
  --set-a law_2024/ \
  --set-b law_2025/
```

#### Glob patterns gebruiken

```bash
uv run python tools/compare_laws.py \
  --set-a "law/**/*-2024-*.yaml" \
  --set-b "law/**/*-2025-*.yaml"
```

#### Output naar bestand

```bash
uv run python tools/compare_laws.py \
  --set-a law/zorgtoeslagwet/TOESLAGEN-2024-01-01.yaml \
  --set-b law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml \
  --format markdown \
  --output comparison_report.md
```

### Opties

- `--set-a` - Pattern/directory voor eerste set van wetten (verplicht)
- `--set-b` - Pattern/directory voor tweede set van wetten (verplicht)
- `--format` - Output formaat: `markdown`, `json`, of `text` (default: markdown)
- `--output`, `-o` - Output bestand (default: stdout)
- `--verbose`, `-v` - Verbose logging

### Voorbeeldoutput

```markdown
# Law Set Comparison Report

**Set A**: law/zorgtoeslagwet/TOESLAGEN-2024-01-01.yaml
**Set B**: law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml
**Comparison Date**: 2025-10-10
**Laws Compared**: 1

## zorgtoeslagwet

**Service**: TOESLAGEN
**Files**: `TOESLAGEN-2024-01-01.yaml` vs `TOESLAGEN-2025-01-01.yaml`

### Legal Basis

**Set B**:
- Law: Zorgtoeslagwet
- Article: 2
- URL: https://wetten.overheid.nl/BWBR0018451/2025-01-01/0/Artikel2

### Metadata Changes
- **valid_from**: 2024-01-01 → 2025-01-01

### Definition Changes
- **DREMPELINKOMEN_ALLEENSTAANDE**: 3749600 → 3971900 *(Zorgtoeslagwet, Art. 2)*
- **AFBOUWPERCENTAGE_BOVEN_DREMPEL**: 0.0387 → 0.137 *(Zorgtoeslagwet, Art. 2)*

### Input Changes
**Added**:
- IS_VERZEKERDE *(Zorgtoeslagwet, Art. 1)*

**Removed**:
- HEEFT_VERZEKERING
- HEEFT_VERDRAGSVERZEKERING
```

## Voorbeeld: Zorgtoeslag 2024 vs 2025

De verschillen tussen de zorgtoeslagwet 2024 en 2025 zijn significant:

### Belangrijkste wijzigingen:

1. **Drempelinkomen verhoogd**:
   - Alleenstaanden: €37.496 → €39.719 (+5.9%)
   - Partners: €48.218 → €50.206 (+4.1%)

2. **Percentages aangepast**:
   - Basispremie % alleenstaanden: 4.86% → 1.896% (-61%)
   - Afbouwpercentage: 3.87% → 13.7% (+254%)

3. **Vereenvoudigde inputs**:
   - 4 aparte verzekeringsvelden vervangen door 1 veld `IS_VERZEKERDE`

Deze wijzigingen hebben grote impact op de berekening van de zorgtoeslag.

## Toekomstige verbeteringen

- [ ] Visuele grafieken van verschillen
- [ ] Export naar CSV voor verdere analyse
- [ ] Diff highlighting in YAML structure
- [ ] Detectie van semantische wijzigingen (hernoemen van velden)
- [ ] Versiebeheer tracking (git commit links)
