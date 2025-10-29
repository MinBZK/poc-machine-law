# Machtigingen & Vertegenwoordiging - Implementatieplan

**Document Versie:** 1.2
**Datum:** 2025-10-28
**Status:** Week 1-4 Complete (72/72 tests passing)
**Branch:** `feature/machtigingen-architectuur`

---

## Executive Summary

Dit document beschrijft de concrete implementatie van het machtigingen- en vertegenwoordigingssysteem in RegelRecht. ALLE business logic wordt gemodelleerd in YAML law files volgens het RegelRecht schema, volledig afgeleid van Nederlandse wet- en regelgeving.

**Doel**: Digitaal kunnen vaststellen of persoon A gemachtigd is om te handelen namens persoon/organisatie B, met volledige juridische traceerbaarheid.

**Aanpak**: Gefaseerde implementatie in 8 weken, startend met eenvoudige wetten (ouderlijk gezag, KVK) en opschalen naar complexere scenario's (curatele, volmacht, bewindvoering, mentorschap). Python orchestration met discovery metadata - GEEN meta-wetten.

**Status Update 2025-10-28**:
- ✅ **Week 1-4 COMPLETE** - All 6 authorization laws implemented
- ✅ **72/72 tests passing** (100% coverage)
- ✅ Discovery metadata added to all laws for automatic role detection
- ❌ **Meta-law approach rejected** - Using actual Dutch laws only, Python orchestration for session-based authorization

---

## 📊 Voortgang Overzicht

### Week 1-2: Foundation (Fase 1) - ✅ **COMPLETE**
- [x] Directory structuur aangemaakt
- [x] Ouderlijk Gezag law geïmplementeerd
- [x] Test data aangemaakt
- [x] Behavior tests Ouderlijk Gezag (9/9 scenarios passing, 100%)
- [x] KVK Vertegenwoordiging law geïmplementeerd
- [x] Behavior tests KVK Vertegenwoordiging (17/17 scenarios passing, 100%)

### Week 3-4: Complexere Wetten (Fase 2) - ✅ **COMPLETE**
- [x] Curatele law + tests (12/12 scenarios passing, 100%)
- [x] Bewindvoering law + tests (8/8 scenarios passing, 100%)
- [x] Mentorschap law + tests (8/8 scenarios passing, 100%)
- [x] Volmacht law + tests (18/18 scenarios passing, 100%)

### Week 5-6: Integration (Fase 3)
- [x] ~~Authorization Resolver meta-law~~ ❌ **REJECTED** - No meta-laws, use actual Dutch laws only
- [ ] Integration met bestaande wetten (zorgtoeslag)
- [ ] Cross-law authorization tests
- [ ] UI integration - verify roles appear in role selector

### Week 7: Test & Validation (Fase 4)
- [x] All tests passing (72/72 = 100% coverage!)
- [ ] Schema validation
- [ ] Performance testing

### Week 8: Web UI & API (Fase 5)
- [ ] Web UI authorization check page
- [ ] API endpoints
- [ ] MCP tool integration
- [ ] Documentation

---

## 📁 Bestands Structuur

```
law/
├── burgerlijk_wetboek/
│   ├── ouderlijk_gezag/
│   │   └── RvIG-2025-01-01.yaml                     ✅ DONE (9/9 tests)
│   ├── curatele/
│   │   └── RECHTSPRAAK-2025-01-01.yaml              ✅ DONE (12/12 tests)
│   ├── bewindvoering/
│   │   └── RECHTSPRAAK-2025-01-01.yaml              ✅ DONE (8/8 tests)
│   ├── mentorschap/
│   │   └── RECHTSPRAAK-2025-01-01.yaml              ✅ DONE (8/8 tests)
│   └── volmacht/
│       └── ALGEMEEN-2025-01-01.yaml                 ✅ DONE (18/18 tests)
├── handelsregisterwet/
│   └── vertegenwoordiging/
│       └── KVK-2025-01-01.yaml                      ✅ DONE (17/17 tests)
└── authorization/
    └── resolver/
        └── ALGEMEEN-2025-01-01.yaml                 ❌ REJECTED (no meta-laws)

data/
└── authorization_test_profiles.yaml                  ✅ DONE (used in tests)

features/burgerlijk_wetboek/
├── ouderlijk_gezag.feature                          ✅ DONE (9/9 scenarios)
├── curatele.feature                                 ✅ DONE (12/12 scenarios)
├── volmacht.feature                                 ✅ DONE (18/18 scenarios)
├── bewindvoering.feature                            ✅ DONE (8/8 scenarios)
└── mentorschap.feature                              ✅ DONE (8/8 scenarios)

features/handelsregisterwet/
└── kvk_vertegenwoordiging.feature                   ✅ DONE (17/17 scenarios)

features/authorization/ (TODO)
└── authorization_resolver.feature                   ⏳ TODO

web/
├── routes/
│   └── authorization.py                             ⏳ TODO (NEW)
└── templates/
    └── authorization_check.html                     ⏳ TODO (NEW)

docs/
├── implementation/
│   └── machtigingen-implementatie-plan.md           ✅ THIS FILE
└── research/
    └── machtigingen-en-vertegenwoordiging.md        ✅ DONE (earlier)
```

---

## 📋 Gedetailleerde Implementatie Per Wet

### 1. Ouderlijk Gezag (BW 1:245) - ✅ DONE

**Status**: Geïmplementeerd
**File**: `law/burgerlijk_wetboek/ouderlijk_gezag/RvIG-2025-01-01.yaml`

**Juridische Basis**:
- **BW 1:245 lid 1**: "De ouders vertegenwoordigen hun minderjarige kinderen"
- **BW 1:233**: Minderjarigheid eindigt op 18 jaar
- **BW 1:251**: Regels over wie het ouderlijk gezag heeft
- **BW 1:266**: Ontzetting uit ouderlijk gezag

**Parameters**:
- `BSN_OUDER`: BSN van de ouder die wil handelen
- `BSN_KIND`: BSN van het kind

**Sources** (externe data):
- `OUDER_KIND_RELATIE` (RvIG/BRP): Is er een geregistreerde ouder-kind relatie?
- `LEEFTIJD_KIND` (RvIG/BRP): Leeftijd van het kind
- `HEEFT_OUDERLIJK_GEZAG` (RvIG/BRP): Heeft ouder het gezag?
- `GEZAG_ONTZEGD` (RECHTSPRAAK): Is gezag ontzegd door rechter?

**Output**:
- `mag_vertegenwoordigen` (boolean): Hoofdresultaat
- `vertegenwoordigings_grondslag` (string): Juridische grondslag

**Requirements** (AND):
1. Ouder-kind relatie bestaat
2. Kind is minderjarig (< 18 jaar)
3. Ouder heeft ouderlijk gezag
4. Gezag is niet ontzegd

**Actions**:
- Als alle requirements = true → `mag_vertegenwoordigen = true`

**Test Scenarios** (✅ 9/9 PASSING):
1. ✅ Ouder → eigen minderjarig kind (17 jaar) - PASSING
2. ✅ Ouder → meerderjarig kind (18+ jaar) - PASSING (blocked)
3. ✅ Niet-ouder → kind - PASSING (blocked)
4. ✅ Ouder met ontzet ouderlijk gezag → kind - PASSING (blocked)
5. ✅ Moeder → kind (gezamenlijk gezag met vader) - PASSING
6. ✅ Ex-partner zonder gezag → kind van ex - PASSING (blocked)
7. ✅ Stiefouder met gezamenlijk gezag → stiefkind - PASSING
8. ✅ Opa/oma → kleinkind (zonder voogdij) - PASSING (blocked)
9. ✅ Voogd → kind (adoptie scenario) - PASSING

---

### 2. KVK Vertegenwoordiging (Handelsregisterwet Art 10) - ✅ DONE

**Status**: Geïmplementeerd
**File**: `law/handelsregisterwet/vertegenwoordiging/KVK-2025-01-01.yaml`

**Juridische Basis**:
- **Handelsregisterwet Art 10**: Vertegenwoordigingsbevoegdheid
- **BW Boek 2**: Regels per rechtsvorm (BV, NV, VOF, etc.)

**Parameters**:
- `BSN_PERSOON`: BSN van persoon die wil handelen
- `RSIN`: RSIN van bedrijf (alternatief: `KVK_NUMMER`)

**Sources**:
- `FUNCTIE_IN_BEDRIJF` (KVK): Alle functies van persoon in bedrijf
  - Fields: `functie`, `bevoegdheid`, `status`, `ingangsdatum`, `einddatum`
- `RECHTSVORM` (KVK): Rechtsvorm van bedrijf (BV, NV, VOF, etc.)

**Definitions**:
```yaml
VERTEGENWOORDIGINGSBEVOEGDE_FUNCTIES:
  - BESTUURDER
  - DIRECTEUR
  - ENIG_AANDEELHOUDER_BESTUURDER
  - VENNOOT  # Voor VOF/Maatschap
  - BEHEREND_VENNOOT  # Voor CV
  - ZAAKVOERDER
  - MANAGING_DIRECTOR
  - ALGEMEEN_DIRECTEUR
  - EIGENAAR  # Voor eenmanszaak
  - PROCURATIEHOUDER  # Voor NV/BV met beperkte bevoegdheid

ACTIEVE_STATUSSEN:
  - ACTIEF
  - IN_FUNCTIE
```

**Output**:
- `mag_vertegenwoordigen` (boolean)
- `bevoegdheid` (string): ZELFSTANDIG / GEZAMENLIJK / BEPERKT
- `functie` (string): Welke functie?

**Requirements** (AND):
1. Functie is in lijst van vertegenwoordigingsbevoegde functies
2. Status is actief
3. Geen einddatum OF einddatum in toekomst (ANY block with IS_NULL or GREATER_THAN)

**Test Scenarios** (✅ 17/17 PASSING):
1. ✅ Directeur-grootaandeelhouder → eigen BV (zelfstandig bevoegd) - PASSING
2. ✅ Bestuurder → stichting - PASSING
3. ✅ Vennoot → VOF (gezamenlijk bevoegd) - PASSING
4. ✅ Ex-bestuurder (einddatum = vorig jaar) → BV - PASSING (blocked)
5. ✅ Aandeelhouder zonder bestuursfunctie → BV - PASSING (blocked)
6. ✅ Bestuurder met beperkte bevoegdheid → BV (mag niet zelfstandig) - PASSING
7. ✅ Enig bestuurder NV → NV - PASSING
8. ✅ Commissaris → NV (toezicht, geen vertegenwoordiging) - PASSING (blocked)
9. ✅ Beherend vennoot → CV - PASSING
10. ✅ Stille vennoot → CV (geen vertegenwoordiging) - PASSING (blocked)
11. ✅ Zaakvoerder → Maatschap - PASSING
12. ✅ Gewezen functionaris (status = BEËINDIGD) → BV - PASSING (blocked)
13. ✅ Eigenaar eenmanszaak → eigen bedrijf - PASSING
14. ✅ Procuratiehouder → NV - PASSING
15. ✅ Bestuurder (einddatum in toekomst) → BV - PASSING
16. ✅ Managing Director → internationale BV - PASSING
17. ✅ Algemeen Directeur → grote onderneming - PASSING

---

### 3. Curatele (BW 1:378) - ✅ DONE

**Status**: Geïmplementeerd
**File**: `law/burgerlijk_wetboek/curatele/RECHTSPRAAK-2025-01-01.yaml`

**Juridische Basis**:
- **BW 1:378**: Curator vertegenwoordigt curandus in alle rechtsbetrekkingen
- **BW 1:381**: Beperkte curatele mogelijk

**Parameters**:
- `BSN_CURATOR`: BSN van curator
- `BSN_CURANDUS`: BSN van persoon onder curatele

**Sources**:
- `CURATELE_UITSPRAAK` (RECHTSPRAAK): Rechterlijke uitspraak
  - Fields: `curator_bsn`, `curandus_bsn`, `type_curatele`, `ingangsdatum`, `einddatum`, `beperkingen`
- `TYPE_CURATELE` (RECHTSPRAAK): VOLLEDIG / BEPERKT
- `BEPERKINGEN` (RECHTSPRAAK): Array van beperkingen (bijv. ["financieel", "medisch"])

**Key Complexity**:
- Tijdelijke curatele (einddatum kan bestaan)
- Beperkte curatele (alleen specifieke handelingen)
- Co-curatoren (meerdere curatoren tegelijk, gezamenlijk bevoegd)

**Output**:
- `mag_vertegenwoordigen` (boolean)
- `type_curatele` (string)
- `beperkingen` (array): Evt. beperkingen

**Test Scenarios** (✅ 12/12 PASSING):
1. ✅ Curator → curandus (volledige curatele) - PASSING
2. ✅ Curator → curandus (beperkte curatele, financieel) - PASSING
3. ✅ Curator → curandus (beperkte curatele, financieel) voor medische beslissing - PASSING (blocked)
4. ✅ Ex-curator (curatele beëindigd) → ex-curandus - PASSING (blocked)
5. ✅ Co-curator 1 → curandus (gezamenlijk met co-curator 2) - PASSING
6. ✅ Niet-curator → curandus - PASSING (blocked)
7. ✅ Curator → curandus (tijdelijke curatele, nog niet verlopen) - PASSING
8. ✅ Curator → curandus (tijdelijke curatele, verlopen) - PASSING (blocked)
9. ✅ Curator → curandus (beperkte curatele, meerdere beperkingen) - PASSING
10. ✅ Niet-geregistreerde persoon → curandus - PASSING (blocked)
11. ✅ Curator → curandus (volledige curatele, medische beslissing) - PASSING
12. ✅ Curator → andere persoon (niet curandus) - PASSING (blocked)

---

### 4. Bewindvoering (BW 1:431) - ✅ DONE

**Status**: ✅ Geïmplementeerd (8/8 tests passing)
**File**: `law/burgerlijk_wetboek/bewindvoering/RECHTSPRAAK-2025-01-01.yaml`
**Test File**: `features/burgerlijk_wetboek/bewindvoering.feature`

**Juridische Basis**:
- **BW 1:431**: Bewindvoerder beheert vermogen van rechthebbende
- **BW 1:436**: Beperkingen aan bewindvoering

**Key Difference vs Curatele**:
- Bewindvoering = ALLEEN financieel (vermogensbeheer)
- Curatele = financieel + persoonlijk
- Rechthebbende blijft juridisch handelingsbekwaam voor NIET-financiële zaken

**Parameters**:
- `BSN_BEWINDVOERDER`: BSN van bewindvoerder
- `BSN_RECHTHEBBENDE`: BSN van persoon onder bewind

**Sources** (via source_reference):
- `BEWIND_UITSPRAAK_EXISTS` (RECHTSPRAAK): Boolean - rechterlijke uitspraak bestaat
- `BEWINDVOERDER_BSN_MATCH` (RECHTSPRAAK): Boolean - BSN komt overeen
- `TYPE_BEWIND` (RECHTSPRAAK): VOLLEDIG_BEWIND / BEPERKT_BEWIND
- `IS_ACTIEF` (RECHTSPRAAK): Boolean - bewind nog actief

**Output**:
- `mag_vertegenwoordigen` (boolean)
- `type_bewind` (string)
- `scope` (string): "financieel_alleen"
- `vertegenwoordigings_grondslag` (string): "bewindvoering_artikel_431_bw"

**Discovery Metadata**:
- `purpose`: "authorization"
- `scope`: "financial"
- `display_name`: "Bewindvoering (BW 1:431)"

**Test Scenarios** (✅ 8/8 PASSING):
1. ✅ Bewindvoerder → rechthebbende (financiële handeling) - PASSING
2. ✅ Bewindvoerder → rechthebbende (medische beslissing) - PASSING (scope check shows financial only)
3. ✅ Ex-bewindvoerder (bewind opgeheven) → ex-rechthebbende - PASSING (blocked)
4. ✅ Bewindvoerder → rechthebbende (banktransactie) - PASSING
5. ✅ Bewindvoerder → rechthebbende (belastingaangifte) - PASSING
6. ✅ Bewindvoerder → rechthebbende (huwelijkstoestemming) - PASSING (scope check shows financial only)
7. ✅ Bewindvoerder → rechthebbende (beperkt bewind, nog actief) - PASSING
8. ✅ Niet-bewindvoerder → persoon onder bewind - PASSING (blocked)

---

### 5. Mentorschap (BW 1:450) - ✅ DONE

**Status**: ✅ Geïmplementeerd (8/8 tests passing)
**File**: `law/burgerlijk_wetboek/mentorschap/RECHTSPRAAK-2025-01-01.yaml`
**Test File**: `features/burgerlijk_wetboek/mentorschap.feature`

**Juridische Basis**:
- **BW 1:450**: Mentor vertegenwoordigt in persoonlijke aangelegenheden
- **BW 1:452**: Beperkingen mentorschap

**Key Difference vs Bewindvoering**:
- Mentorschap = ALLEEN persoonlijk (medisch, zorg, wonen)
- Bewindvoering = alleen financieel
- Complement van elkaar: samen dekken ze curatele af

**Parameters**:
- `BSN_MENTOR`: BSN van mentor
- `BSN_BETROKKENE`: BSN van persoon met mentorschap

**Sources** (via source_reference):
- `UITSPRAAK_EXISTS` (RECHTSPRAAK): Boolean - rechterlijke uitspraak bestaat
- `MENTOR_BSN_MATCH` (RECHTSPRAAK): Boolean - BSN komt overeen
- `MENTORSCHAP_ACTIEF` (RECHTSPRAAK): Boolean - mentorschap nog actief
- `BEVOEGDHEDEN` (RECHTSPRAAK): Array van bevoegdheden (["medisch", "zorg", "wonen"])
- `HEEFT_BEVOEGDHEDEN` (RECHTSPRAAK): Boolean - heeft bevoegdheden

**Output**:
- `mag_vertegenwoordigen` (boolean)
- `bevoegdheden` (array): Welke bevoegdheden?
- `scope` (string): "persoonlijk_alleen"
- `vertegenwoordigings_grondslag` (string): "mentorschap_artikel_450_bw"

**Discovery Metadata**:
- `purpose`: "authorization"
- `scope`: "personal"
- `display_name`: "Mentorschap (BW 1:450)"

**Test Scenarios** (✅ 8/8 PASSING):
1. ✅ Mentor → betrokkene (medische beslissing) - PASSING
2. ✅ Mentor → betrokkene (zorginstelling kiezen) - PASSING
3. ✅ Mentor → betrokkene (financiële transactie) - PASSING (scope check shows personal only)
4. ✅ Ex-mentor (mentorschap beëindigd) → ex-betrokkene - PASSING (blocked)
5. ✅ Mentor → betrokkene (woonplaats bepalen) - PASSING
6. ✅ Mentor → betrokkene (belastingaangifte) - PASSING (scope check shows personal only)
7. ✅ Mentor → betrokkene (toestemming medische behandeling) - PASSING
8. ✅ Niet-mentor → persoon met mentorschap - PASSING (blocked)

---

### 6. Volmacht (BW 3:60) - ✅ DONE

**Status**: Geïmplementeerd
**File**: `law/burgerlijk_wetboek/volmacht/ALGEMEEN-2025-01-01.yaml`

**Juridische Basis**:
- **BW 3:60**: Volmacht is een aan een ander verleende bevoegdheid
- **BW 3:61**: Volmacht kan worden ingetrokken
- **BW 3:69**: Algemene en bijzondere volmacht

**Key Complexity**:
- Vrijwillig (geen rechter nodig)
- Kan specifiek zijn (bijv. alleen belastingaangifte) of algemeen
- Kan elk moment ingetrokken worden
- **Probleem**: Geen centraal volmachtenregister in NL!

**Pragmatische Oplossing voor Pilot**:
- Mock volmachtenregister (voor pilot)
- In productie: notarissen als trusted issuers
- Toekomst: Verifiable Credentials (zie advanced architectuur)

**Parameters**:
- `BSN_GEVOLMACHTIGDE`: BSN van gevolmachtigde
- `BSN_VOLMACHTGEVER`: BSN van volmachtgever (of `RSIN_VOLMACHTGEVER`)
- `ACTIE` (optional): Specifieke actie (bijv. "belasting_aangifte")

**Sources**:
- `VOLMACHT_REGISTRATIE` (NOTARIS): Volmachtregistratie
  - Fields: `gevolmachtigde_bsn`, `volmachtgever_bsn`, `type_volmacht`, `scope`, `ingangsdatum`, `herroepen`, `herroepingsdatum`
- `TYPE_VOLMACHT` (NOTARIS): ALGEMEEN / BIJZONDER / PROCURATIE
- `SCOPE` (NOTARIS): Array van toegestane acties (["belasting_aangifte", "bankzaken", "rechtszaken"])

**Output**:
- `mag_vertegenwoordigen` (boolean)
- `type_volmacht` (string)
- `scope` (array): Voor welke acties?
- `beperkingen` (array): Evt. beperkingen

**Requirements** (AND):
1. Volmacht is geregistreerd
2. Volmacht is niet herroepen
3. Als specifieke ACTIE gegeven: actie moet in scope zitten
4. Geen einddatum (of einddatum in toekomst)

**Test Scenarios** (✅ 18/18 PASSING):
1. ✅ Gevolmachtigde (algemene volmacht) → volmachtgever - PASSING
2. ✅ Gevolmachtigde (bijzondere volmacht, belastingaangifte) → volmachtgever (voor belastingaangifte) - PASSING
3. ✅ Gevolmachtigde (bijzondere volmacht, belastingaangifte) → volmachtgever (voor bankzaken) - PASSING (blocked)
4. ✅ Gevolmachtigde (herroepen volmacht) → ex-volmachtgever - PASSING (blocked)
5. ✅ Procuratiehouder → bedrijf (procuratie voor handelingen) - PASSING
6. ✅ Niet-gevolmachtigde → persoon - PASSING (blocked)
7. ✅ Accountant (volmacht) → cliënt (belastingaangifte) - PASSING
8. ✅ Ex-accountant (volmacht herroepen) → ex-cliënt - PASSING (blocked)
9. ✅ Partner (volmacht) → partner (bankzaken) - PASSING
10. ✅ Gevolmachtigde (tijdelijke volmacht, verlopen) → volmachtgever - PASSING (blocked)
11. ✅ Gevolmachtigde (bijzondere volmacht, meerdere acties) - PASSING
12. ✅ Gevolmachtigde (volmacht voor toekomstige actie) - PASSING
13. ✅ Gevolmachtigde (algemene volmacht, alle acties toegestaan) - PASSING
14. ✅ Gevolmachtigde (beperkte volmacht met einddatum in toekomst) - PASSING
15. ✅ Gevolmachtigde (bedrijfsvolmacht, KVK-geregistreerd) - PASSING
16. ✅ Gevolmachtigde (notariële volmacht) - PASSING
17. ✅ Gevolmachtigde (tijdelijke volmacht, nog actief) - PASSING
18. ✅ Niet-geregistreerde gevolmachtigde - PASSING (blocked)

---

### 7. Authorization Resolver (Meta-Wet) - ⏳ TODO

**Status**: Te implementeren
**File**: `law/authorization/resolver/ALGEMEEN-2025-01-01.yaml`

**Purpose**: Meta-wet die ALLE authorization checks combineert

**Key Concept**:
- Roept alle individuele authorization wetten aan
- Combineert resultaten met OR logic (als ÉÉN check true → geautoriseerd)
- Verzamelt juridische grondslagen van alle applicable wetten

**Parameters**:
- `BSN_ACTOR`: Wie wil handelen?
- `TARGET_TYPE`: Voor wie? (PERSON / ORGANIZATION)
- `TARGET_ID`: BSN of RSIN
- `ACTION` (optional): Specifieke actie (bijv. "belasting_aangifte")

**Sources** (external law calls):
1. `OUDERLIJK_GEZAG_CHECK` → burgerlijk_wetboek/ouderlijk_gezag
2. `CURATOR_CHECK` → burgerlijk_wetboek/curatele
3. `BEWINDVOERDER_CHECK` → burgerlijk_wetboek/bewindvoering
4. `MENTOR_CHECK` → burgerlijk_wetboek/mentorschap
5. `VOLMACHT_CHECK` → burgerlijk_wetboek/volmacht
6. `KVK_CHECK` → handelsregisterwet/vertegenwoordiging

**Logic**:
```yaml
# Conditional calls based on TARGET_TYPE
- If TARGET_TYPE == PERSON:
    call: ouderlijk_gezag, curatele, bewindvoering, mentorschap, volmacht
- If TARGET_TYPE == ORGANIZATION:
    call: kvk_vertegenwoordiging, volmacht
```

**Output**:
- `is_geautoriseerd` (boolean): Hoofdresultaat
- `autorisatie_grondslagen` (array): Alle juridische grondslagen
  ```json
  [
    {
      "type": "ouderlijk_gezag",
      "law": "BW 1:245",
      "article": "245",
      "role": "ouder",
      "scope": "volledig"
    }
  ]
  ```
- `primary_grondslag` (object): Primaire juridische grondslag
- `beperkingen` (array): Evt. beperkingen op machtiging

**Actions**:
```yaml
- output: is_geautoriseerd
  operation: OR
  values:
    - $OUDERLIJK_GEZAG_CHECK.mag_vertegenwoordigen
    - $CURATOR_CHECK.mag_vertegenwoordigen
    - $BEWINDVOERDER_CHECK.mag_vertegenwoordigen
    - $MENTOR_CHECK.mag_vertegenwoordigen
    - $VOLMACHT_CHECK.mag_vertegenwoordigen
    - $KVK_CHECK.mag_vertegenwoordigen

- output: autorisatie_grondslagen
  operation: CONCAT
  values:
    - operation: IF
      condition: $OUDERLIJK_GEZAG_CHECK.mag_vertegenwoordigen
      then:
        type: ouderlijk_gezag
        law: "BW 1:245"
        role: ouder
    # ... etc for all checks
```

**Test Scenarios** (20+ edge cases):
1. ✅ Ouder → kind (via ouderlijk gezag)
2. ✅ Curator → curandus (via curatele)
3. ✅ Bewindvoerder → rechthebbende (financiële actie)
4. ❌ Bewindvoerder → rechthebbende (medische actie)
5. ✅ Mentor → betrokkene (medische actie)
6. ❌ Mentor → betrokkene (financiële actie)
7. ✅ Gevolmachtigde → volmachtgever
8. ✅ Directeur → BV
9. ❌ Willekeurige persoon → ander persoon (geen relatie)
10. ✅ Ouder + curator (beide rollen tegelijk) → kind onder curatele
11. ⚠️ Conflicterende machtigingen (ouder vs curator)
12. ✅ Bewindvoerder + mentor (samen dekken volledige vertegenwoordiging)
13. ❌ Ex-bestuurder → ex-BV
14. ✅ Accountant met volmacht → cliënt (belastingaangifte)
15. ❌ Accountant met volmacht → cliënt (medische beslissing)
16. ✅ Ouder → meerderjarig kind (indien volmacht gegeven)
17. ❌ Ouder → meerderjarig kind (zonder volmacht)
18. ✅ Vennoot → VOF (via KVK)
19. ✅ Zaakvoerder → Maatschap (via KVK)
20. ❌ Commissaris → NV (toezicht, geen vertegenwoordiging)

---

## 🧪 Test Data Structure

### File: `data/authorization_test_profiles.yaml`

```yaml
# ===== FAMILIES (Ouderlijk Gezag) =====
families:
  - family_id: FAM001
    description: "Normaal gezin met minderjarig kind"
    members:
      - bsn: "100000001"
        naam: "Jan Jansen"
        geboortedatum: "1985-03-15"
        leeftijd: 39
      - bsn: "100000002"
        naam: "Maria Jansen"
        geboortedatum: "1987-06-20"
        leeftijd: 37
      - bsn: "100000003"
        naam: "Piet Jansen"
        geboortedatum: "2015-09-10"
        leeftijd: 9
    relations:
      - type: ouderlijk_gezag
        ouder_bsn: "100000001"
        kind_bsn: "100000003"
        heeft_gezag: true
        gezag_ontzegd: false
      - type: ouderlijk_gezag
        ouder_bsn: "100000002"
        kind_bsn: "100000003"
        heeft_gezag: true
        gezag_ontzegd: false

  - family_id: FAM002
    description: "Gescheiden ouders, één met gezag"
    members:
      - bsn: "100000011"
        naam: "Kees de Vries"
        geboortedatum: "1980-07-22"
      - bsn: "100000012"
        naam: "Sophie de Vries"
        geboortedatum: "1982-11-30"
      - bsn: "100000013"
        naam: "Emma de Vries"
        geboortedatum: "2012-05-18"
        leeftijd: 12
    relations:
      - type: ouderlijk_gezag
        ouder_bsn: "100000011"
        kind_bsn: "100000013"
        heeft_gezag: true
        gezag_ontzegd: false
      - type: ouderlijk_gezag
        ouder_bsn: "100000012"
        kind_bsn: "100000013"
        heeft_gezag: false  # Gescheiden, zonder gezag
        gezag_ontzegd: false

  - family_id: FAM003
    description: "Ouder met ontzet ouderlijk gezag"
    members:
      - bsn: "100000021"
        naam: "Peter Bakker"
        geboortedatum: "1975-02-14"
      - bsn: "100000023"
        naam: "Lisa Bakker"
        geboortedatum: "2010-08-25"
        leeftijd: 14
    relations:
      - type: ouderlijk_gezag
        ouder_bsn: "100000021"
        kind_bsn: "100000023"
        heeft_gezag: false
        gezag_ontzegd: true  # Rechter heeft gezag ontzegd
        ontzetting_datum: "2020-06-15"

# ===== CURATELE CASES =====
curatele_cases:
  - case_id: CUR001
    description: "Volledige curatele"
    curator_bsn: "200000001"
    curator_naam: "Mr. A. Advocaat"
    curandus_bsn: "200000002"
    curandus_naam: "B. Betrokkene"
    type_curatele: "VOLLEDIG"
    ingangsdatum: "2023-01-15"
    einddatum: null
    rechtbank: "Rechtbank Amsterdam"
    beperkingen: []

  - case_id: CUR002
    description: "Beperkte curatele (alleen financieel)"
    curator_bsn: "200000011"
    curator_naam: "Mr. C. Curator"
    curandus_bsn: "200000012"
    curandus_naam: "D. Derde"
    type_curatele: "BEPERKT"
    ingangsdatum: "2024-03-01"
    einddatum: null
    rechtbank: "Rechtbank Rotterdam"
    beperkingen: ["financieel"]  # Alleen financieel, niet medisch

  - case_id: CUR003
    description: "Tijdelijke curatele (verlopen)"
    curator_bsn: "200000021"
    curator_naam: "Mr. E. Edelaar"
    curandus_bsn: "200000022"
    curandus_naam: "F. Fractal"
    type_curatele: "VOLLEDIG"
    ingangsdatum: "2022-01-01"
    einddatum: "2024-01-01"  # Verlopen
    rechtbank: "Rechtbank Den Haag"
    beperkingen: []

# ===== BEWINDVOERING CASES =====
bewindvoering_cases:
  - case_id: BEW001
    description: "Beschermingsbewind"
    bewindvoerder_bsn: "210000001"
    bewindvoerder_naam: "Bewindvoerder Stichting"
    rechthebbende_bsn: "210000002"
    rechthebbende_naam: "G. Geldgebrek"
    type_bewind: "VOLLEDIG_BEWIND"
    ingangsdatum: "2023-06-01"
    einddatum: null
    rechtbank: "Rechtbank Utrecht"

# ===== MENTORSCHAP CASES =====
mentorschap_cases:
  - case_id: MEN001
    description: "Mentorschap voor persoonlijke aangelegenheden"
    mentor_bsn: "220000001"
    mentor_naam: "H. Helper"
    betrokkene_bsn: "220000002"
    betrokkene_naam: "I. Incapabel"
    ingangsdatum: "2024-01-01"
    einddatum: null
    rechtbank: "Rechtbank Arnhem"
    bevoegdheden: ["medisch", "zorg", "wonen"]

# ===== VOLMACHT CASES =====
volmacht_cases:
  - case_id: VOL001
    description: "Algemene volmacht"
    gevolmachtigde_bsn: "230000001"
    gevolmachtigde_naam: "J. Jurist"
    volmachtgever_bsn: "230000002"
    volmachtgever_naam: "K. Klant"
    type_volmacht: "ALGEMEEN"
    scope: ["*"]  # Alle handelingen
    ingangsdatum: "2024-01-01"
    herroepen: false
    herroepingsdatum: null

  - case_id: VOL002
    description: "Bijzondere volmacht (alleen belastingaangifte)"
    gevolmachtigde_bsn: "230000011"
    gevolmachtigde_naam: "L. Accountant"
    volmachtgever_bsn: "230000012"
    volmachtgever_naam: "M. Meneer"
    type_volmacht: "BIJZONDER"
    scope: ["belasting_aangifte", "belasting_bezwaar"]
    ingangsdatum: "2023-01-01"
    herroepen: false
    herroepingsdatum: null

  - case_id: VOL003
    description: "Herroepen volmacht"
    gevolmachtigde_bsn: "230000021"
    gevolmachtigde_naam: "N. Notaris"
    volmachtgever_bsn: "230000022"
    volmachtgever_naam: "O. Opdrachtgever"
    type_volmacht: "ALGEMEEN"
    scope: ["*"]
    ingangsdatum: "2022-01-01"
    herroepen: true
    herroepingsdatum: "2024-06-01"

# ===== BEDRIJVEN (KVK) =====
bedrijven:
  - kvk_nummer: "12345678"
    rsin: "001234567"
    naam: "Jansen BV"
    rechtsvorm: "BV"
    status: "ACTIEF"
    functionarissen:
      - bsn: "100000001"  # Jan Jansen
        naam: "Jan Jansen"
        functie: "BESTUURDER"
        bevoegdheid: "ZELFSTANDIG"
        status: "ACTIEF"
        ingangsdatum: "2020-01-01"
        einddatum: null

  - kvk_nummer: "23456789"
    rsin: "002345678"
    naam: "De Vries VOF"
    rechtsvorm: "VOF"
    status: "ACTIEF"
    functionarissen:
      - bsn: "100000011"  # Kees de Vries
        naam: "Kees de Vries"
        functie: "VENNOOT"
        bevoegdheid: "GEZAMENLIJK"
        status: "ACTIEF"
        ingangsdatum: "2019-06-01"
        einddatum: null
      - bsn: "300000001"
        naam: "Piet Partner"
        functie: "VENNOOT"
        bevoegdheid: "GEZAMENLIJK"
        status: "ACTIEF"
        ingangsdatum: "2019-06-01"
        einddatum: null

  - kvk_nummer: "34567890"
    rsin: "003456789"
    naam: "Stichting Hulp"
    rechtsvorm: "STICHTING"
    status: "ACTIEF"
    functionarissen:
      - bsn: "200000001"  # Mr. A. Advocaat
        naam: "Mr. A. Advocaat"
        functie: "BESTUURDER"
        bevoegdheid: "ZELFSTANDIG"
        status: "ACTIEF"
        ingangsdatum: "2018-01-01"
        einddatum: null

  - kvk_nummer: "45678901"
    rsin: "004567890"
    naam: "Ex-Bedrijf BV"
    rechtsvorm: "BV"
    status: "ACTIEF"
    functionarissen:
      - bsn: "300000011"
        naam: "Q. Quit"
        functie: "BESTUURDER"
        bevoegdheid: "ZELFSTANDIG"
        status: "BEËINDIGD"
        ingangsdatum: "2020-01-01"
        einddatum: "2023-12-31"  # Niet meer actief
      - bsn: "300000012"
        naam: "R. Replace"
        functie: "BESTUURDER"
        bevoegdheid: "ZELFSTANDIG"
        status: "ACTIEF"
        ingangsdatum: "2024-01-01"
        einddatum: null

  - kvk_nummer: "56789012"
    rsin: "005678901"
    naam: "Commissaris Testen NV"
    rechtsvorm: "NV"
    status: "ACTIEF"
    functionarissen:
      - bsn: "300000021"
        naam: "S. Supervisor"
        functie: "COMMISSARIS"  # Toezicht, geen vertegenwoordiging
        bevoegdheid: "GEEN"
        status: "ACTIEF"
        ingangsdatum: "2021-01-01"
        einddatum: null
      - bsn: "300000022"
        naam: "T. Topman"
        functie: "DIRECTEUR"
        bevoegdheid: "ZELFSTANDIG"
        status: "ACTIEF"
        ingangsdatum: "2021-01-01"
        einddatum: null
```

---

## 🌐 Web UI Implementatie

### Nieuwe Route: `/authorization-check`

**File**: `web/routes/authorization.py`

**Functionaliteit**:
1. Input form:
   - BSN actor (wie wil handelen?)
   - Target type (persoon / organisatie)
   - Target ID (BSN of RSIN)
   - Optionele actie (bijv. "belasting_aangifte")

2. Backend logic:
   - Roept `authorization/resolver` wet aan
   - Verzamelt alle grondslagen
   - Format output voor UI

3. Output weergave:
   - ✅/❌ Geautoriseerd status
   - Juridische grondslagen (met wetsartikelen)
   - Rol (ouder, curator, directeur, etc.)
   - Beperkingen (indien van toepassing)
   - Link naar volledige wettekst

**UI Mockup**:
```
┌──────────────────────────────────────────────────────────┐
│  Machtigingscheck                                         │
│  Controleer of iemand gemachtigd is om te handelen       │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Wie wil handelen?                                       │
│  ┌────────────────────────────────────────┐             │
│  │ BSN: [100000001        ]  [Zoek Persoon]│             │
│  └────────────────────────────────────────┘             │
│  👤 Jan Jansen (geb. 15-03-1985)                         │
│                                                           │
│  Voor wie wil deze persoon handelen?                     │
│  ○ Natuurlijk persoon    ● Organisatie                   │
│                                                           │
│  ┌────────────────────────────────────────┐             │
│  │ RSIN: [001234567       ]  [Zoek Bedrijf]│             │
│  └────────────────────────────────────────┘             │
│  🏢 Jansen BV (KvK: 12345678)                            │
│                                                           │
│  Specifieke actie (optioneel):                          │
│  ┌────────────────────────────────────────┐             │
│  │ [belasting_aangifte ▼]                  │             │
│  └────────────────────────────────────────┘             │
│                                                           │
│            [✓ Controleer Machtiging]                     │
│                                                           │
├──────────────────────────────────────────────────────────┤
│  RESULTAAT                                               │
│                                                           │
│  ✅ JAN JANSEN MAG HANDELEN NAMENS JANSEN BV             │
│                                                           │
│  📋 Juridische Grondslag:                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Handelsregisterwet Artikel 10                       │ │
│  │ BW Boek 2: Vertegenwoordigingsbevoegdheid          │ │
│  │                                                     │ │
│  │ Functie: Bestuurder                                 │ │
│  │ Bevoegdheid: Zelfstandig bevoegd                   │ │
│  │ Status: Actief sinds 01-01-2020                    │ │
│  │                                                     │ │
│  │ [📄 Bekijk volledige wettekst]                      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  ⚠️ Beperkingen: Geen                                    │
│                                                           │
│  ℹ️  Deze machtiging is geldig op: 16-10-2025           │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

**Negative Example**:
```
┌──────────────────────────────────────────────────────────┐
│  RESULTAAT                                               │
│                                                           │
│  ❌ KEES DE VRIES MAG NIET HANDELEN NAMENS JANSEN BV     │
│                                                           │
│  ⛔ Reden: Geen vertegenwoordigingsbevoegdheid           │
│                                                           │
│  Gecontroleerd:                                          │
│  • KVK Handelsregister: Geen actieve functie gevonden   │
│  • Volmachtenregister: Geen volmacht geregistreerd      │
│                                                           │
│  💡 Tip: Om namens Jansen BV te kunnen handelen moet    │
│     Kees de Vries:                                       │
│     • Een bestuursfunctie krijgen (via KVK), of         │
│     • Een volmacht krijgen van de huidige bestuurder    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

### Integratie in Bestaande Web Interface

**Navigation Update**:

Add to `web/templates/base.html`:
```html
<nav>
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/profile">Mijn Profiel</a></li>
    <li><a href="/authorization-check">Machtigingscheck</a></li>  <!-- NEW -->
    <li><a href="/admin">Admin</a></li>
  </ul>
</nav>
```

**Profile Page Enhancement**:

Add section to profile page showing authorization relationships:
```html
<section class="authorizations">
  <h3>Voor wie mag ik handelen?</h3>
  <ul>
    <li>
      👶 Piet Jansen (kind)
      <span class="badge">Ouderlijk gezag</span>
      <a href="/authorization-check?actor={{ user.bsn }}&target={{ child.bsn }}&type=person">Details</a>
    </li>
    <li>
      🏢 Jansen BV
      <span class="badge">Bestuurder</span>
      <a href="/authorization-check?actor={{ user.bsn }}&target=001234567&type=organization">Details</a>
    </li>
  </ul>

  <h3>Wie mag voor mij handelen?</h3>
  <ul>
    <li>
      👤 Maria Jansen (partner)
      <span class="badge">Volmacht</span>
      <a href="/authorization-check?actor={{ partner.bsn }}&target={{ user.bsn }}&type=person">Details</a>
    </li>
  </ul>
</section>
```

---

## 🔌 API Endpoints

**New Endpoint**: `POST /api/authorization/check`

**Request**:
```json
{
  "actor_bsn": "100000001",
  "target_type": "ORGANIZATION",
  "target_id": "001234567",
  "action": "belasting_aangifte",
  "reference_date": "2025-10-16"
}
```

**Response** (authorized):
```json
{
  "is_geautoriseerd": true,
  "grondslagen": [
    {
      "type": "kvk_vertegenwoordiging",
      "law": "Handelsregisterwet",
      "article": "10",
      "bwb_id": "BWBR0021777",
      "url": "https://wetten.overheid.nl/BWBR0021777/2025-01-01#Artikel10",
      "role": "bestuurder",
      "functie": "BESTUURDER",
      "bevoegdheid": "ZELFSTANDIG",
      "status": "ACTIEF",
      "ingangsdatum": "2020-01-01",
      "einddatum": null
    }
  ],
  "primary_grondslag": {
    "type": "kvk_vertegenwoordiging",
    "law": "Handelsregisterwet",
    "article": "10"
  },
  "beperkingen": [],
  "checked_at": "2025-10-16T14:30:00Z"
}
```

**Response** (not authorized):
```json
{
  "is_geautoriseerd": false,
  "grondslagen": [],
  "primary_grondslag": null,
  "beperkingen": null,
  "reason": "Geen vertegenwoordigingsbevoegdheid gevonden",
  "checked_laws": [
    "burgerlijk_wetboek/ouderlijk_gezag",
    "burgerlijk_wetboek/curatele",
    "burgerlijk_wetboek/bewindvoering",
    "burgerlijk_wetboek/mentorschap",
    "burgerlijk_wetboek/volmacht",
    "handelsregisterwet/vertegenwoordiging"
  ],
  "checked_at": "2025-10-16T14:30:00Z"
}
```

---

## 🤖 MCP Tool Extension

**File**: `law_mcp/server.py`

**New Tool**:
```python
@mcp.tool()
async def check_authorization(
    actor_bsn: str,
    target_type: Literal["PERSON", "ORGANIZATION"],
    target_id: str,
    action: Optional[str] = None,
    reference_date: Optional[str] = None,
) -> dict:
    """
    Check of een persoon gemachtigd is om te handelen namens een ander persoon of organisatie.

    Args:
        actor_bsn: BSN van de persoon die wil handelen
        target_type: Type van de target (PERSON of ORGANIZATION)
        target_id: BSN (voor persoon) of RSIN (voor organisatie)
        action: Optionele specifieke actie (bijv. "belasting_aangifte")
        reference_date: Datum waarop machtiging gecontroleerd wordt (default: vandaag)

    Returns:
        dict met is_geautoriseerd, grondslagen, en beperkingen

    Example:
        check_authorization(
            actor_bsn="100000001",
            target_type="ORGANIZATION",
            target_id="001234567"
        )
    """
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    result = await execute_law(
        service="ALGEMEEN",
        law="authorization/resolver",
        parameters={
            "BSN_ACTOR": actor_bsn,
            "TARGET_TYPE": target_type,
            "TARGET_ID": target_id,
            "ACTION": action,
        },
        reference_date=reference_date,
    )

    return {
        "is_geautoriseerd": result["is_geautoriseerd"],
        "grondslagen": result.get("autorisatie_grondslagen", []),
        "primary_grondslag": result.get("primary_grondslag"),
        "beperkingen": result.get("beperkingen", []),
        "checked_at": datetime.now().isoformat(),
    }
```

---

## 📊 Success Metrics & Testing

### Coverage Targets:
- **Unit tests** (YAML syntax): 100%
- **Behavior tests** (scenarios): 90%+
- **Integration tests**: 80%+
- **Web UI tests**: 70%+

### Test Commands:
```bash
# Run all authorization behavior tests
uv run behave features/authorization --no-capture -v

# Run specific law tests
uv run behave features/authorization/ouderlijk_gezag.feature
uv run behave features/authorization/kvk_vertegenwoordiging.feature

# Validate YAML schemas
./script/validate

# Run linting
ruff check law/
ruff format law/

# Run web UI tests
script/test-ui
```

### Performance Targets:
- Authorization check < 100ms (single law)
- Authorization resolver < 500ms (all laws)
- Web UI page load < 1s

---

## 🚀 Next Steps After Pilot

### Phase 6: RVO Subsidies (Week 9-10)
- Extend authorization to RVO subsidy applications
- Who can apply for which subsidies?
- Delegation from company to external advisor

### Phase 7: Belastingdienst Machtigingen (Week 11-12)
- Tax representative authorization
- Accountant mandates
- Integration with Belastingdienst APIs

### Phase 8: Verifiable Credentials Integration (Week 13-16)
- Replace mock registers with VC verification
- KVK as VC issuer (pilot)
- EU Digital Identity Wallet integration
- See `docs/research/machtigingen-en-vertegenwoordiging.md` for full SSI architecture

---

## ⚠️ Known Limitations & Workarounds

### 1. Volmachtenregister bestaat niet
**Probleem**: Nederland heeft geen centraal volmachtenregister
**Pilot workaround**: Mock register met test data
**Toekomst**: Notarissen als VC issuers, blockchain-based registry

### 2. KVK API met BSN niet beschikbaar
**Probleem**: KVK API geeft geen BSN's terug (privacy)
**Pilot workaround**: Mock KVK data in test files
**Toekomst**: Government API access met BSN fields, of BSN-RSIN lookup service

### 3. Real-time updates
**Probleem**: Mock data is statisch
**Pilot workaround**: Manual test data updates
**Toekomst**: Real-time webhooks from KVK/BRP, revocation lists

### 4. Cross-border (EU burgers)
**Probleem**: Alleen NL BSN ondersteund
**Pilot workaround**: Not in scope
**Toekomst**: eIDAS identifiers, EUDI wallet integration

### 5. Conflicting authorizations
**Probleem**: Wat als ouder EN curator (conflict)?
**Pilot workaround**: OR logic (beide mogen)
**Toekomst**: Priority hierarchy, conflict resolution rules

---

## 📝 Documentation To-Do

- [x] Implementation plan (this document)
- [ ] API documentation (OpenAPI spec)
- [ ] Law YAML documentation (per wet)
- [ ] Integration guide (for other developers)
- [ ] User guide (web UI)
- [ ] Admin guide (test data management)

---

## 👥 Team & Effort Estimate

**Total Effort**: 8 weken (320 uur)
**Developer**: 1 full-time
**Risk Level**: Laag (pure YAML, geen infrastructure changes)
**Business Value**: Hoog (basis voor SSI, direct bruikbaar voor toeslagen/subsidies)

---

## 📅 Timeline Summary

| Week | Focus | Deliverables | Status |
|------|-------|-------------|--------|
| 1-2 | Foundation | Ouderlijk Gezag + KVK + tests | ✅ DONE (26/26 tests) |
| 3-4 | Complex laws | Curatele + Bewindvoering + Mentorschap + Volmacht | ✅ DONE (46/46 tests) |
| 5-6 | Integration | ~~Authorization Resolver~~ + zorgtoeslag integration | ⏳ IN PROGRESS |
| 7 | Testing | All tests passing, schema validation | ✅ DONE (72/72 tests) |
| 8 | Web UI | Authorization check page, API, MCP tool | ⏳ TODO |

**Target Completion**: 8 weken vanaf 2025-10-16 = **2025-12-11**
**Actual Progress**: Week 1-4 complete (2025-10-28), ahead of schedule

---

_Document wordt live bijgewerkt tijdens implementatie._
