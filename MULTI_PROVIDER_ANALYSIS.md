# Multi-Provider YAML Analysis

## Date: 2025-11-07

## Overview

Analysis of multi-provider law YAML files to determine merge strategy for v0.1.7 migration.

## Files Analyzed

### 1. wet_inkomstenbelasting (Income Tax Law)

**Files:**
- `BELASTINGDIENST-2001-01-01.yaml` (41KB)
- `UWV-2020-01-01.yaml` (10KB)

**Analysis:**

| Aspect | BELASTINGDIENST | UWV |
|--------|-----------------|-----|
| **Service** | BELASTINGDIENST | UWV |
| **Valid From** | 2001-01-01 | 2020-01-01 |
| **Name** | "Inkomstenbelasting" | "Bepalen toetsingsinkomen" |
| **Purpose** | Full tax calculation | Calculate assessment income for benefits |
| **Primary Output** | `totale_belastingschuld` (total tax owed) | `inkomen` (toetsingsinkomen) |
| **Other Outputs** | box1/2/3 income, deductions, credits | `partner_inkomen` |
| **Size** | 41KB (comprehensive) | 10KB (simplified) |
| **Legal Basis** | Article 2.1 (tax levy) | Article 2.11 (assessment income) |

**Decision: KEEP SPLIT ✓**

**Rationale:**
1. **Different purposes**: Tax assessment vs benefits eligibility
2. **Different outputs**: Tax owed vs assessment income
3. **Different complexity**: Full calculation vs simplified assessment
4. **Different use cases**: Tax Office assessment vs UWV benefits determination
5. **Different legal basis**: Different articles within same law

**Action:** Update both files separately to v0.1.7 schema.

---

### 2. wet_brp/terugmelding (BRP Notification Obligation)

**Files:**
- `BELASTINGDIENST-2023-05-15.yaml`
- `TOESLAGEN-2023-05-15.yaml`
- `CJIB-2023-05-15.yaml`

**Analysis:**

| Aspect | BELASTINGDIENST | TOESLAGEN | CJIB |
|--------|-----------------|-----------|------|
| **Service** | BELASTINGDIENST | TOESLAGEN | CJIB |
| **Valid From** | 2023-05-15 | 2023-05-15 | 2023-05-15 |
| **Legal Basis** | Article 2.34 (same) | Article 2.34 (same) | Article 2.34 (same) |
| **Purpose** | Report address doubts | Report address doubts | Report address doubts |
| **Parameters** | BSN, ADRES | BSN, ADRES | BSN, ADRES |

**Key Questions to Answer:**

1. **Do they have different data sources?**
   - BELASTINGDIENST: Tax administration addresses
   - TOESLAGEN: Allowance recipient addresses
   - CJIB: Debtor addresses
   - ❓ Are these accessed differently in the code?

2. **Do they have different business logic?**
   - All implement same legal obligation (Article 2.34)
   - ❓ Are the conditions for "gerede twijfel" (reasonable doubt) different?

3. **Do they have different outputs?**
   - All output: notification to municipality via TMV
   - ❓ Are output structures identical?

4. **Are the differences only in the service label?**
   - Same law, same article, same date
   - ❓ Could this be one YAML with organization as parameter?

**Decision: ANALYSIS NEEDED ⏳**

**Next Steps:**
1. Compare full YAML structures side-by-side
2. Check if `sources` sections reference different tables
3. Check if `definitions` and business logic differ
4. Check if `output` structures are identical
5. Consult with domain experts if needed

**Possible Outcomes:**

**Option A: Merge if identical**
- If logic is truly identical, merge into single `wet_brp/terugmelding/2023-05-15.yaml`
- Remove service-specific distinctions
- Organization context comes from DataContext, not from separate files

**Option B: Keep split if different**
- If data sources or logic differ, keep separate
- Update each to v0.1.7 individually
- Document why they're separate (different data access patterns)

---

## Migration Strategy

### Phase 1: Keep As-Is (Current)
All files stay separate during initial v0.1.7 migration to maintain backward compatibility.

### Phase 2: Analyze (Next)
Deep dive into wet_brp/terugmelding to determine if merge is beneficial.

### Phase 3: Migrate
- wet_inkomstenbelasting: Update both files to v0.1.7 separately
- wet_brp/terugmelding: Update based on analysis (merge or keep split)

### Phase 4: Validate
Test that all dependent laws still work correctly.

---

## General Principle

**When to keep split:**
- Different purposes/outputs
- Different legal basis (articles)
- Different complexity levels
- Different organizational data sources
- Different business logic

**When to merge:**
- Identical logic
- Only difference is service label
- Same data access patterns
- Same outputs
- Service distinction is artificial

---

## Notes

Based on CLAUDE.md guidelines:
> "Splits wetten op als meerdere organisaties betrokken zijn"
> "Elke wet/regeling hoort bij de organisatie die deze uitvoert"

The files were correctly split according to organizational boundaries in v0.1.6. In v0.1.7 (context-based), we need to re-evaluate if those boundaries are still necessary or if they were artifacts of the service-based architecture.

---

**Status:**
- wet_inkomstenbelasting: Analysis complete ✓
- wet_brp/terugmelding: Analysis needed ⏳
