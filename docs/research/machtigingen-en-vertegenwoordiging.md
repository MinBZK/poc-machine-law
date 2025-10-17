# Machtigingen en Vertegenwoordiging in RegelRecht

**Onderzoeksdatum:** 16 oktober 2025
**Status:** Research & Architectuur Voorstel
**Auteur:** Research naar Nederlands vertegenwoordigingsrecht

---

## Inhoudsopgave

1. [Executive Summary](#executive-summary)
2. [Probleemstelling](#probleemstelling)
3. [Juridisch Kader](#juridisch-kader)
4. [Huidige Situatie: eHerkenning Problematiek](#huidige-situatie-eherkenning-problematiek)
5. [Voorgestelde Oplossing](#voorgestelde-oplossing)
6. [Implementatieplan](#implementatieplan)
7. [Open Vragen](#open-vragen)

---

## Executive Summary

### Kernbevinding

Het Nederlandse systeem van **eHerkenning voor bedrijven is onnodig complex en beveiligingsrisicovol**. Voor een overheidsapplicatie als RegelRecht kunnen we een **DigiD-centrisch model** implementeren waarbij:

- ✅ **Natuurlijke personen** altijd inloggen met DigiD (BSN-gebaseerd)
- ✅ **Rechtspersonen** worden vertegenwoordigd door natuurlijke personen via BSN ↔ RSIN koppeling
- ✅ **KVK Handelsregister** als bron van waarheid voor vertegenwoordigingsbevoegdheid
- ✅ **Eenmalige verificatie** per rol, daarna alleen DigiD nodig
- ❌ **Geen permanente eHerkenning-dependency** meer

### Voordelen

| Aspect | Huidig (eHerkenning) | Voorgesteld (DigiD-centrisch) |
|--------|---------------------|--------------------------------|
| **Beveiliging** | Accounts deelbaar (fraude-risico) | DigiD strikt persoonlijk |
| **Audit trail** | Account-gebaseerd | Persoon (BSN) altijd traceerbaar |
| **Gebruikservaring** | Complex (2 login-systemen) | Simpel (1 login voor alles) |
| **Kosten** | eHerkenning €€/jaar | DigiD gratis |
| **Privacy** | Via commerciële partijen | Direct overheid |

---

## Probleemstelling

### Wat willen we bereiken?

Een gebruiker moet na het inloggen **in één oogopslag** kunnen zien:

```
Welkom Jan de Vries (BSN: 200...001)

Je kunt handelen als:

👤 Jezelf
   └─ Bekijk je eigen uitkeringen en toeslagen

🛡️ Als bewindvoerder
   └─ Piet Jansen (BSN: 100...001)
       └─ Financiële zaken: zorgtoeslag, bijstand, belasting

🏢 Als bestuurder
   └─ Tech B.V. (KVK: 12345678)
       └─ Alle bedrijfswetten: WPM, RVO subsidies
```

### Huidige blokkades

1. **eHerkenning vereist** voor bedrijfshandelingen
2. **Geen uniform overzicht** van alle machtigingen
3. **Versnipperd** over verschillende systemen (Belastingdienst, RVO, etc.)
4. **Frauderisico** door deelbare eHerkenning-accounts

---

## Juridisch Kader

### 1. Vertegenwoordiging Natuurlijke Personen

#### A. Minderjarigen (BW Boek 1, art. 1:245+)

**Wie mag vertegenwoordigen:**
- Ouders met ouderlijk gezag
- Voogd (bij overleden/ontzette ouders)

**Bevoegdheid:**
- Volledige vertegenwoordiging in alle rechtshandelingen
- Beperking: handelingen die strikt persoonlijk zijn

**Databron:**
- **BRP (RvIG)** - Basisregistratie Personen
- Veld: `ouderlijk_gezag_door`

**Wettelijke basis:**
```
BW Boek 1, Titel 14: Ouderlijk gezag
Art. 1:245 lid 1: "De ouders die het gezag over een minderjarig kind
                   uitoefenen, vertegenwoordigen hem in burgerlijke
                   handelingen, zowel in als buiten rechte."
```

#### B. Curatele (BW Boek 1, art. 1:378+)

**Wie mag vertegenwoordigen:**
- Curator (benoemd door kantonrechter)

**Bevoegdheid:**
- **Volledig**: Zowel persoonlijke als financiële zaken
- Handelingsonbekwaamheid van gecureerde
- Kan: subsidies aanvragen, belastingaangifte doen, contracten sluiten

**Databron:**
- **Centraal Curatele Register** (beheerd door rechtspraak)
- Via rechterlijke beschikking

**Wettelijke basis:**
```
BW Boek 1, Titel 16: Curatele
Art. 1:381 lid 1: "De curator heeft het bestuur over het vermogen
                   van de onder curatele gestelde."
Art. 1:381 lid 3: "De curator vertegenwoordigt de onder curatele gestelde
                   in alle burgerlijke handelingen."
```

#### C. Bewindvoering (BW Boek 1, art. 1:431+)

**Wie mag vertegenwoordigen:**
- Bewindvoerder (benoemd door kantonrechter)

**Bevoegdheid:**
- **Alleen financieel**: Vermogensbeheer
- Kan: belastingaangifte, financiële subsidies, bankzaken
- Kan NIET: beslissingen over zorg, gezondheid, levenstestament

**Databron:**
- **Centraal Bewindregister** (beheerd door rechtspraak)

**Wettelijke basis:**
```
BW Boek 1, Titel 19: Bewind
Art. 1:438 lid 1: "De bewindvoerder heeft het bestuur over de goederen
                   die onder bewind zijn gesteld."
Art. 1:441: "Rechtshandelingen die de rechthebbende met betrekking
             tot onder bewind staande goederen verricht, zijn vernietigbaar."
```

**Belangrijk verschil met curatele:**
- Bewindvoering = alleen vermogen
- Curatele = vermogen + persoon (handelingsonbekwaamheid)

#### D. Mentorschap (BW Boek 1, art. 1:450+)

**Wie mag vertegenwoordigen:**
- Mentor (benoemd door kantonrechter)

**Bevoegdheid:**
- **Alleen persoonlijk**: Zorg, behandeling, opname
- Kan NIET: Financiële zaken beheren

**Databron:**
- **Mentorschapsregister** (bij rechtspraak)

**Wettelijke basis:**
```
BW Boek 1, Titel 20: Mentorschap
Art. 1:450: "De kantonrechter kan voor een meerderjarige ten behoeve van
             wie een bewindvoerder is benoemd, een mentor benoemen."
```

---

### 2. Vertegenwoordiging Rechtspersonen

#### A. Statutaire Vertegenwoordiging (BW Boek 2)

**Algemene regel (art. 2:240 BW - BV):**
```
Art. 2:240 lid 1: "Het bestuur vertegenwoordigt de vennootschap,
                   tenzij uit de wet anders voortvloeit."
```

**Voor verschillende rechtsvormen:**

| Rechtsvorm | Artikel | Vertegenwoordiger | Bevoegdheid |
|------------|---------|-------------------|-------------|
| **NV** | 2:132 | Bestuur | Gezamenlijk tenzij statuten anders bepalen |
| **BV** | 2:240 | Bestuur | Gezamenlijk tenzij statuten anders bepalen |
| **Vereniging** | 2:37 | Bestuur | Gezamenlijk tenzij statuten anders bepalen |
| **Stichting** | 2:292 | Bestuur | Gezamenlijk tenzij statuten anders bepalen |
| **Coöperatie** | 2:44 | Bestuur | Gezamenlijk tenzij statuten anders bepalen |

**Beperkingen werking (art. 2:6 BW):**
```
Art. 2:6 lid 2: "Een door de wet toegelaten beroep op statutaire
                 onbevoegdheid [...] kan tegen een wederpartij die
                 daarvan onkundig was, niet worden gedaan, indien de
                 beperking [...] niet [...] was openbaar gemaakt."
```

**Praktijk:** Beperkingen werken alleen als:
- In statuten vastgelegd
- Gepubliceerd in Handelsregister
- Wederpartij daarvan op de hoogte kon zijn

**Databron:**
- **KVK Handelsregister** (Handelsregisterwet art. 14)
- Velden: `functionarissen`, `tekenbevoegdheid`, `beperkingen`

#### B. Volmacht (publiekrechtelijke rechtspersonen)

**Registratie (Handelsregisterwet art. 16a):**
```
Art. 16a: "In het handelsregister worden de door een publiekrechtelijke
           rechtspersoon verleende volmachten opgenomen."
```

**Let op:** Artikel 25 (derdenwerking) is NIET van toepassing op deze volmachten.

---

### 3. Algemene Volmacht (BW Boek 3)

#### Definitie (art. 3:60 BW)

```
Art. 3:60 lid 1: "Volmacht is de bevoegdheid die een volmachtgever
                  verleent aan een gevolmachtigde om in zijn naam
                  rechtshandelingen te verrichten."
```

#### Ontstaan (art. 3:61 BW)

**Expliciet of impliciet:**
```
Art. 3:61 lid 1: "Een volmacht kan worden verleend door een daartoe
                  bestemde verklaring of door een andere rechtshandeling."
```

**Schijnvolmacht (derdenbescherming):**
```
Art. 3:61 lid 2: "Indien een rechtshandeling is verricht door iemand
                  die daartoe onbevoegd was, maar de wederpartij dit
                  op grond van een verklaring of gedraging van de
                  onbevoegde mocht geloven, wordt de rechtshandeling
                  geacht te zijn verricht door een vertegenwoordiger."
```

#### Werking (art. 3:66 BW)

```
Art. 3:66 lid 1: "Een rechtshandeling, verricht door een vertegenwoordiger
                  die daarbij te kennen geeft in naam van een ander te
                  handelen, bindt die ander."
```

**Gevolg:**
- Gevolmachtigde is NIET gebonden
- Volmachtgever WEL gebonden
- Direct effect

**Databron:**
- ❌ Geen centraal volmachtregister (nog niet)
- ⚠️ Notariële volmachten: bij notaris
- ⚠️ Praktijk: vaak ad-hoc en niet geregistreerd

---

### 4. Zaakwaarneming (BW Boek 6, art. 6:198)

#### Definitie

```
Art. 6:198: "Zaakwaarneming is het zich willens en wetens en op
             redelijke grond inlaten met de behartiging van eens
             anders belang, zonder de bevoegdheid daartoe aan een
             rechtshandeling [...] te ontlenen."
```

**Kenmerken:**
- Handelen zonder voorafgaande toestemming
- Op redelijke grond
- In belang van ander

#### Vertegenwoordigingsbevoegdheid (art. 6:201 BW)

```
Art. 6:201: "De zaakwaarnemer is bevoegd namens de belanghebbende
             rechtshandelingen te verrichten, voor zover de belangen
             daardoor behoorlijk worden gediend."
```

**Praktijk:**
- Noodsituaties (buurman in ziekenhuis, lekkage)
- Bedrijfsvoering bij plotselinge afwezigheid
- Geen formele machtiging vereist

**Databron:**
- ❌ Niet geregistreerd
- ⚠️ Alleen achteraf te bewijzen (getuigen, omstandigheden)

---

### 5. Erfrecht: Executeur-Testamentair (BW Boek 4, art. 4:142)

#### Benoeming

```
Art. 4:142 lid 1: "De erflater kan bij uiterste wil een of meer
                   executeurs benoemen."
```

#### Exclusieve bevoegdheid (art. 4:145 BW)

```
Art. 4:145: "Indien een executeur is benoemd, rust het beheer van
             de nalatenschap gedurende de executele bij hem. De
             erfgenamen kunnen gedurende de executele niet over de
             tot de nalatenschap behorende goederen beschikken."
```

**Gevolg:**
- Erfgenamen NIET bevoegd tijdens executele
- Executeur vertegenwoordigt erfgenamen
- In en buiten rechte

**Databron:**
- Testament (bij notaris)
- Verklaring van executele (vereist voor overheidsinstanties)

---

### 6. Insolventierechtrecht: Faillissementscurator (Faillissementswet)

#### Benoeming (art. 14 Fw)

Bij faillietverklaring wijst rechtbank curator aan.

#### Bevoegdheden (art. 68+ Fw)

**Vertegenwoordiging:**
- Neemt ALLE bevoegdheden bestuur over
- Vertegenwoordigt zowel gefailleerde als schuldeisers (dualiteit)

**Vergaande bevoegdheden:**
- Binnentreden zonder machtiging (art. 93a Fw)
- Voortzetten onderneming (mits machtiging rechter-commissaris, art. 98 Fw)
- Optreden tegen onregelmatigheden

**Databron:**
- **Centraal Insolventieregister** (rechtspraak)
- Faillissementsvonnis

---

### 7. Sectorspecifieke Machtigingen

#### A. Belastingdienst Intermediairs

**Wettelijke basis:**
- Algemene wet bestuursrecht (Awb) art. 2:1
- Wet op de omzetbelasting
- Wet inkomstenbelasting

**Systeem:**
```
Art. 2:1 lid 2 Awb: "Het bestuursorgaan kan van een gemachtigde
                     een schriftelijke machtiging verlangen."
```

**Praktijk (sinds 2021):**
- **Doorlopende machtigingen** per belastingmiddel
- Intermediairs: accountants, boekhouders, belastingadviseurs, bewindvoerders
- Geldig voor meerdere jaren (tenzij ingetrokken)

**Scope:**
- Inkomstenbelasting (IB)
- Vennootschapsbelasting (VPB)
- Omzetbelasting (BTW)
- Toeslagen
- Vooraf ingevulde aangiftes (VIA)

**Technisch:**
- **Logius Machtigingenregister Digipoort**
- Burger/bedrijf logt in met DigiD/eHerkenning
- Kan machtigingen zien en intrekken
- Portal: `machtigen.digipoort.logius.nl`

#### B. RVO Subsidies

**Voorwaarde:**
- Aanvrager moet **rechtspersoon** zijn (KVK-inschrijving vereist)
- Uitzondering: bepaalde regelingen staan natuurlijke personen toe

**Intermediairs:**
- Mogen aanvragen namens eigenaren
- Moeten geregistreerd bij KVK
- eHerkenning niveau 2+ met machtiging "RVO-diensten op niveau eH2+"

**Bijzonderheid:**
- Gemeenten kunnen namens burgers aanvragen (bijv. ISDE)
- Overeenkomst regelt bevoegdheden

**Wettelijke basis:**
- Awb art. 2:1 (algemene machtiging)
- Specifieke subsidiewetten (bijv. Besluit activiteiten leefomgeving voor WPM)

#### C. Algemene Wet Bestuursrecht (art. 2:1)

```
Art. 2:1 lid 1: "De aanvrager, belanghebbende, tot bezwaar of beroep
                 gerechtigde kan zich laten bijstaan of
                 vertegenwoordigen door een gemachtigde."

Art. 2:1 lid 2: "Het bestuursorgaan kan van een gemachtigde een
                 schriftelijke machtiging verlangen."
```

**Kenmerken:**
- Discretionair (bestuursorgaan niet verplicht te vragen)
- Mag in algemene bewoordingen
- Flexibel systeem

---

### 8. Digitale Identiteit & Authenticatie

#### A. DigiD - Wet algemene bepalingen burgerservicenummer (Wabb)

**Wettelijke verankering:**
```
Wabb (BWBR0022428)
Doel: Unieke identificatie van burgers in contact met overheid
Middel: BSN (burgerservicenummer)
Authenticatie: DigiD
```

**Voor overheidsorganisaties:**
- Mogen BSN gebruiken ZONDER aparte wettelijke grondslag
- Voor uitvoering publieke taak

**Voor private organisaties:**
- Alleen BSN gebruiken als SPECIFIEKE wettelijke grondslag bestaat

**DigiD Niveaus:**
- **Basis**: Gebruikersnaam + wachtwoord + SMS-code
- **Midden**: Basis + identiteitsbewijs controle
- **Substantieel**: App met SMS/NFC
- **Hoog**: App met rijbewijs/identiteitskaart NFC

#### B. eHerkenning - eIDAS implementatie

**GEEN aparte Nederlandse wet!**
- Implementatie van **eIDAS Verordening (EU) 910/2014**
- eHerkenning is een **afsprakenstelsel** (geen wettelijke verplichting)
- Beheerd door commerciële partijen (eHerkenning makelaars)

**Niveaus:**
- **EH1**: Gebruikersnaam + wachtwoord (verouderd)
- **EH2+**: Gebruikersnaam + wachtwoord + SMS
- **EH3**: Certificaat op device
- **EH4**: Smart card / hardware token

**Voor bedrijven:**
- Identificatie: **RSIN** (Rechtspersonen en Samenwerkingsverbanden Informatienummer)
- RSIN = BSN-equivalent voor rechtspersonen
- Bij KVK-inschrijving automatisch RSIN toegekend

**Machtigingensysteem:**
- Tekenbevoegde (uit KVK) kan machtigingen verlenen
- Machtigingenbeheerder kan worden aangewezen
- Machtigingen per dienst/service

**eIDAS 2.0 (vanaf 2024):**
- EU Digital Identity Wallet
- Nederland: publieke wallet ontwikkeld
- Cross-border authenticatie verplicht

---

## Huidige Situatie: eHerkenning Problematiek

### Waarom eHerkenning bestaat

**Probleem:**
```
Bedrijf heeft RSIN, geen BSN
→ Kan niet inloggen met DigiD (DigiD is BSN-gebonden)
→ Dus: hoe authenticeert een bedrijf zich?
```

**Gekozen oplossing:**
```
Persoon met BSN → krijgt eHerkenning
                → wordt gemachtigd namens bedrijf (RSIN)
                → kan nu inloggen "als bedrijf"
```

### Beveiligingsproblemen

#### 1. **Deelbaarheid (in theorie verboden, in praktijk moeilijk te handhaven)**

**Volgens de regels:**
- ✅ eHerkenning is **persoonlijk** en mag NIET gedeeld
- ✅ Elke medewerker moet eigen eHerkenning hebben
- ✅ Moet gemachtigd worden door tekenbevoegde

**In de praktijk:**
- ❌ Bedrijven hebben vaak ÉÉN eHerkenning-account
- ❌ Meerdere medewerkers gebruiken dezelfde credentials
- ❌ Moeilijk te handhaven (hoe bewijst overheid dat account gedeeld wordt?)

#### 2. **TVL-fraude (COVID-19 subsidies)**

**Feiten:**
- RVO deed **70 aangiften** voor fraude met TVL (Tegemoetkoming Vaste Lasten)
- Conclusie: "Fraudeurs vonden het kinderlijk eenvoudig om fraude te plegen"
- Oorzaak: "Zwakke controles en een gebrekkig inlogsysteem"

**Probleem:**
- eHerkenning-account kan door meerdere personen gebruikt worden
- Geen verificatie WIE exact handelt
- Alleen verificatie dat account gemachtigd is

#### 3. **Geen persoonlijke audit trail**

**Bij eHerkenning:**
```
Log: "eHerkenning-account '12345678-EH3' heeft subsidie aangevraagd"
```

**Vraag:** Wie exact heeft dit gedaan?
- Jan de Vries (directeur)?
- Marie Peters (financieel medewerker)?
- Onbekende derde (fraudeur met gestolen credentials)?

**Antwoord:** Onbekend! Alleen het account is bekend, niet de persoon.

**Bij DigiD-model:**
```
Log: "BSN 200000001 (Jan de Vries) heeft subsidie aangevraagd
      namens RSIN 001234567 (Tech B.V.)"
```

**Voordeel:** Altijd traceerbaar naar natuurlijke persoon.

#### 4. **Privacy via commerciële partijen**

**eHerkenning-flow:**
```
Burger → eHerkenning Makelaar (commercieel) → Overheid
         ↑
         Weet alles: wanneer, waar, wat
```

**DigiD-flow:**
```
Burger → DigiD (Logius, overheid) → Overheid
         ↑
         Onder overheidscont controle, geen commerciële tussenpersoon
```

#### 5. **Kosten**

- **eHerkenning**: €50-200 per jaar per account (afhankelijk van niveau)
- **DigiD**: Gratis voor burgers

Voor bedrijf met 10 medewerkers die moeten inloggen:
- eHerkenning: ~€1000/jaar
- DigiD-model: €0

---

## Voorgestelde Oplossing

### Kernprincipe: BSN/RSIN-centrisch model

**Alles draait om twee identifiers:**

```yaml
Natuurlijke personen:
  identifier: BSN (Burgerservicenummer)
  authenticatie: DigiD
  wettelijke basis: Wabb

Rechtspersonen:
  identifier: RSIN (Rechtspersonen Samenwerkingsverbanden Informatienummer)
  authenticatie: Via vertegenwoordiger (natuurlijke persoon met BSN)
  wettelijke basis: Handelsregisterwet

Eenmanszaak (speciaal):
  identifier: BSN van eigenaar (geen apart RSIN!)
  authenticatie: DigiD
  is_onderneming: true (uit KVK)
```

### Architectuur

```
┌─────────────────────────────────────────────────┐
│  AUTHENTICATION LAYER                           │
│  - DigiD (voor alle natuurlijke personen)      │
│  - OPTIONEEL: eHerkenning (eenmalig voor setup)│
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  IDENTITY RESOLVER                              │
│  Input: BSN (van ingelogde persoon)            │
│  Output: Alle rollen/mandaten                   │
│                                                 │
│  Bronnen:                                       │
│  - KVK API: Voor welke RSIN mag BSN handelen?  │
│  - Rechtspraak: Curator/bewindvoerder van wie? │
│  - Eigen DB: Expliciete machtigingen            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  AUTHORIZATION CHECKER                          │
│  Vraag: Mag BSN_actor handelen als             │
│         identifier_subject voor law_X?          │
│  Antwoord: true/false + scope                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  LAW EXECUTION ENGINE                           │
│  Execute wet voor identifier_subject            │
│  Log: executed_by = BSN_actor                   │
└─────────────────────────────────────────────────┘
```

### Data Model

```yaml
# Tabel: bsn_rsin_relations (voor bedrijfsvertegenwoordiging)
bsn_rsin_relations:
  - id: "uuid-1"
    bsn: "200000001"                    # Jan de Vries
    rsin: "001234567"                   # Tech B.V.
    kvk_nummer: "12345678"
    company_name: "Tech B.V."
    function: "BESTUURDER"              # uit KVK
    authority_type: "ZELFSTANDIG_BEVOEGD"
    verified_via: "KVK_API"             # of "MANUAL_VERIFICATION"
    verified_at: "2024-01-15T10:30:00Z"
    valid_from: "2023-06-01"
    valid_until: null                   # Geen einddatum
    source_reference: "KVK:12345678:FUNC:001"

# Tabel: authorizations (voor alle andere vertegenwoordiging)
authorizations:
  - id: "uuid-2"
    actor_bsn: "300000001"              # Marie Peters (bewindvoerder)
    subject_identifier: "100000001"     # Piet Jansen (BSN)
    subject_type: "NATUURLIJK_PERSOON"
    authority_type: "BEWINDVOERING"
    scope: "FINANCIEEL"
    verified_via: "RECHTSPRAAK"
    verified_at: "2024-01-01T09:00:00Z"
    valid_from: "2024-01-01"
    valid_until: null
    source_reference: "ECLI:NL:RBAMS:2024:1234"

  - id: "uuid-3"
    actor_bsn: "400000001"              # Accountant
    subject_identifier: "500000001"     # Cliënt (BSN)
    subject_type: "NATUURLIJK_PERSOON"
    authority_type: "BELASTINGDIENST_INTERMEDIAIR"
    scope: "INKOMSTENBELASTING"
    verified_via: "LOGIUS_MACHTIGINGENREGISTER"
    verified_at: "2024-06-01T14:20:00Z"
    valid_from: "2024-06-01"
    valid_until: "2025-12-31"           # Doorlopende machtiging met einddatum
    source_reference: "LOGIUS:IB:2024:567890"
```

### User Flow

```
╔═══════════════════════════════════════════════╗
║  STAP 1: INLOGGEN                            ║
╚═══════════════════════════════════════════════╝

Gebruiker → klikt "Inloggen"
         → Redirect naar DigiD
         → DigiD authenticatie
         → Retourneert BSN: "200000001"

╔═══════════════════════════════════════════════╗
║  STAP 2: ROLLEN OPHALEN                      ║
╚═══════════════════════════════════════════════╝

RegelRecht → Query: GET /api/identity/roles?bsn=200000001
           ↓
KVK API    → "BSN 200000001 is bestuurder van:"
           → - Tech B.V. (KVK 12345678, RSIN 001234567)
           → - Innovatie Stichting (KVK 87654321, RSIN 007654321)
           ↓
Rechtspraak → "BSN 200000001 is bewindvoerder van:"
(future)   → - Piet Jansen (BSN 100000001)
           ↓
Eigen DB   → "BSN 200000001 heeft machtigingen voor:"
           → - (leeg in dit voorbeeld)

╔═══════════════════════════════════════════════╗
║  STAP 3: ROLLEN TONEN                        ║
╚═══════════════════════════════════════════════╝

┌───────────────────────────────────────────────┐
│ Welkom Jan de Vries                           │
│                                               │
│ Handelen als:                                 │
│                                               │
│ ○ 👤 Mijzelf                                  │
│   Jan de Vries                                │
│   BSN: 200...001                              │
│                                               │
│ ○ 🏢 Bestuurder van:                          │
│   ├─ Tech B.V.                                │
│   │  KVK: 12345678                            │
│   │  Bevoegdheid: Zelfstandig                 │
│   │                                           │
│   └─ Innovatie Stichting                      │
│      KVK: 87654321                            │
│      Bevoegdheid: Gezamenlijk met mede-best.  │
│                                               │
│ ○ 🛡️ Bewindvoerder van:                      │
│   └─ Piet Jansen                              │
│      BSN: 100...001                           │
│      Scope: Financiële zaken                  │
│                                               │
│ [Doorgaan]                                    │
└───────────────────────────────────────────────┘

╔═══════════════════════════════════════════════╗
║  STAP 4: ROL SELECTIE                        ║
╚═══════════════════════════════════════════════╝

Gebruiker → selecteert "Tech B.V."
         → Context opgeslagen in sessie:
            {
              "actor_bsn": "200000001",
              "acting_as_identifier": "001234567",
              "acting_as_type": "RECHTSPERSOON",
              "acting_as_name": "Tech B.V."
            }

╔═══════════════════════════════════════════════╗
║  STAP 5: WETTEN UITVOEREN                    ║
╚═══════════════════════════════════════════════╝

Gebruiker → Navigeert naar "WPM Rapportageverplichting"
         → RegelRecht executes:
            POST /api/laws/execute
            {
              "service": "RVO",
              "law": "omgevingswet/werkgebonden_personenmobiliteit",
              "actor_bsn": "200000001",
              "subject_identifier": "001234567",
              "subject_type": "RECHTSPERSOON",
              "reference_date": "2024-07-01"
            }
         ↓
Authorization → Check: Mag BSN 200000001 handelen voor RSIN 001234567?
Checker      → Query bsn_rsin_relations
             → Match gevonden: function=BESTUURDER, authority=ZELFSTANDIG_BEVOEGD
             → Result: AUTHORIZED
             ↓
Law Engine   → Execute wet voor RSIN 001234567
             → Result: { rapportageverplichting: true, aantal_werknemers: 150 }
             ↓
Audit Log    → Write:
             {
               "timestamp": "2025-01-15T14:30:00Z",
               "actor_bsn": "200000001",
               "actor_name": "Jan de Vries",
               "subject_identifier": "001234567",
               "subject_type": "RECHTSPERSOON",
               "subject_name": "Tech B.V.",
               "law": "omgevingswet/werkgebonden_personenmobiliteit",
               "result": "SUCCESS"
             }
```

### Verificatiemechanismen

Voor het koppelen van BSN aan RSIN zijn er meerdere opties:

#### Optie 1: Overheids-KVK API (IDEAAL)

**Als RegelRecht overheidsapplicatie is:**

```yaml
Status: Overheidsorganisatie / Erkende uitvoeringsorganisatie
Toegang: KVK Dataservice Inschrijving (beveiligde API)
BSN beschikbaar: JA

Flow:
  1. Burger logt in met DigiD → BSN bekend
  2. RegelRecht query KVK API met BSN
  3. KVK retourneert alle bedrijven + functies + bevoegdheden
  4. Automatisch gekoppeld
  5. GEEN extra verificatie nodig

Voordelen:
  ✅ Real-time actueel (KVK is bron van waarheid)
  ✅ Geen eHerkenning nodig
  ✅ Geen manuele verificatie
  ✅ Wettelijk correct (KVK is authentieke bron)
```

#### Optie 2: eHerkenning Eenmalig (FALLBACK)

**Als geen KVK BSN-toegang:**

```yaml
Flow:
  1. Persoon logt EENMAAL in met eHerkenning namens bedrijf
  2. RegelRecht ziet BSN (via DigiD achter eHerkenning) + RSIN
  3. Koppeling opgeslagen in bsn_rsin_relations
  4. Vanaf nu: alleen DigiD nodig

Voordelen:
  ✅ Werkt zonder speciale KVK toegang
  ✅ Na setup geen eHerkenning meer nodig
  ⚠️ Wel initiële eHerkenning-kosten
  ⚠️ Update nodig bij functiewijziging
```

#### Optie 3: Verificatiecode (ALTERNATIEF)

**Voor kleine organisaties:**

```yaml
Flow:
  1. Persoon logt in met DigiD
  2. Claimt bestuurder te zijn van Tech B.V.
  3. RegelRecht stuurt brief met code naar KVK-adres
  4. Persoon voert code in
  5. Koppeling opgeslagen

Voordelen:
  ✅ Geen eHerkenning nodig
  ✅ Gratis
  ⚠️ Langzamer (postbezorging)
  ⚠️ Minder gebruiksvriendelijk
```

#### Optie 4: Bestaande Bestuurder Authoriseert (DELEGATIE)

**Voor meerdere vertegenwoordigers:**

```yaml
Flow:
  1. Eerste bestuurder: verificatie via optie 1, 2 of 3
  2. Eerste bestuurder logt in
  3. Authoriseert nieuwe persoon: "BSN 600000001 mag namens ons handelen"
  4. Nieuwe persoon logt in met DigiD
  5. Kan nu namens bedrijf handelen

Voordelen:
  ✅ Schaalbaar voor grote organisaties
  ✅ Geen herhaalde verificatie nodig
  ⚠️ Eerste bestuurder moet wel geverifieerd zijn
```

---

## Implementatieplan

### Fase 1: Identity & Authorization Core (2 weken)

**Database schema:**
```sql
-- Tabel voor BSN ↔ RSIN relaties
CREATE TABLE bsn_rsin_relations (
    id UUID PRIMARY KEY,
    bsn VARCHAR(9) NOT NULL,
    rsin VARCHAR(9) NOT NULL,
    kvk_nummer VARCHAR(8) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    function VARCHAR(100) NOT NULL,  -- BESTUURDER, BESTUURSLID, VENNOOT
    authority_type VARCHAR(100),     -- ZELFSTANDIG_BEVOEGD, GEZAMENLIJK_BEVOEGD
    verified_via VARCHAR(50) NOT NULL,
    verified_at TIMESTAMP NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE,
    source_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bsn_rsin_bsn ON bsn_rsin_relations(bsn);
CREATE INDEX idx_bsn_rsin_rsin ON bsn_rsin_relations(rsin);

-- Tabel voor algemene machtigingen (niet-KVK)
CREATE TABLE authorizations (
    id UUID PRIMARY KEY,
    actor_bsn VARCHAR(9) NOT NULL,
    subject_identifier VARCHAR(20) NOT NULL,  -- BSN of RSIN
    subject_type VARCHAR(50) NOT NULL,        -- NATUURLIJK_PERSOON, RECHTSPERSOON
    authority_type VARCHAR(100) NOT NULL,     -- BEWINDVOERING, CURATELE, INTERMEDIAIR
    scope VARCHAR(100),                       -- FINANCIEEL, VOLLEDIG, SPECIFIEK
    verified_via VARCHAR(50) NOT NULL,
    verified_at TIMESTAMP NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE,
    source_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_auth_actor ON authorizations(actor_bsn);
CREATE INDEX idx_auth_subject ON authorizations(subject_identifier);
```

**Services:**
```python
# services/identity_resolver.py
class IdentityResolver:
    def get_all_roles(self, authenticated_bsn: str) -> dict:
        """Haal alle rollen op voor een ingelogde gebruiker"""
        return {
            "self": self._get_person_info(authenticated_bsn),
            "as_representative_of_persons": self._get_natuurlijke_personen(authenticated_bsn),
            "as_officer_of_companies": self._get_rechtspersonen(authenticated_bsn),
        }

    def _get_rechtspersonen(self, bsn: str) -> list:
        """Haal bedrijven op waar BSN bestuurder van is"""
        # Optie 1: Via KVK API (als toegang beschikbaar)
        if settings.KVK_API_WITH_BSN:
            return self._fetch_from_kvk_api(bsn)
        # Optie 2: Via eigen database (na eenmalige verificatie)
        else:
            return self._fetch_from_local_db(bsn)

# services/authorization_checker.py
class AuthorizationChecker:
    def can_act_for(
        self,
        actor_bsn: str,
        subject_identifier: str,
        subject_type: str,
        required_scope: str = None
    ) -> tuple[bool, dict]:
        """
        Check of actor_bsn mag handelen voor subject_identifier

        Returns:
            (authorized: bool, details: dict)
        """
        # Check 1: Is actor == subject? (handelt voor zichzelf)
        if subject_type == "NATUURLIJK_PERSOON" and actor_bsn == subject_identifier:
            return (True, {"reason": "SELF", "scope": "VOLLEDIG"})

        # Check 2: BSN → RSIN relatie (bedrijfsvertegenwoordiging)
        if subject_type == "RECHTSPERSOON":
            relation = db.query(BsnRsinRelation).filter(
                BsnRsinRelation.bsn == actor_bsn,
                BsnRsinRelation.rsin == subject_identifier,
                BsnRsinRelation.valid_from <= today,
                (BsnRsinRelation.valid_until.is_(None) | (BsnRsinRelation.valid_until >= today))
            ).first()

            if relation:
                return (True, {
                    "reason": "STATUTORY_OFFICER",
                    "function": relation.function,
                    "authority_type": relation.authority_type,
                    "scope": "VOLLEDIG"
                })

        # Check 3: Algemene machtigingen
        authorization = db.query(Authorization).filter(
            Authorization.actor_bsn == actor_bsn,
            Authorization.subject_identifier == subject_identifier,
            Authorization.valid_from <= today,
            (Authorization.valid_until.is_(None) | (Authorization.valid_until >= today))
        ).first()

        if authorization:
            # Check scope indien vereist
            if required_scope and not self._scope_matches(authorization.scope, required_scope):
                return (False, {"reason": "INSUFFICIENT_SCOPE"})

            return (True, {
                "reason": "AUTHORIZATION",
                "authority_type": authorization.authority_type,
                "scope": authorization.scope
            })

        # Niet geautoriseerd
        return (False, {"reason": "NOT_AUTHORIZED"})
```

**API Endpoints:**
```python
# api/identity.py
@router.get("/api/identity/roles")
def get_roles(authenticated_bsn: str = Depends(get_authenticated_bsn)):
    """Haal alle rollen op voor ingelogde gebruiker"""
    resolver = IdentityResolver()
    return resolver.get_all_roles(authenticated_bsn)

@router.post("/api/identity/verify-company")
def verify_company_relation(
    kvk_nummer: str,
    authenticated_bsn: str = Depends(get_authenticated_bsn)
):
    """Verifieer dat BSN bestuurder is van KVK-bedrijf"""
    # Stuur verificatiecode of gebruik eHerkenning
    pass

# api/laws.py
@router.post("/api/laws/execute")
def execute_law(
    request: LawExecutionRequest,
    authenticated_bsn: str = Depends(get_authenticated_bsn)
):
    """Voer wet uit (met authorization check)"""

    # Check authorization
    checker = AuthorizationChecker()
    authorized, details = checker.can_act_for(
        actor_bsn=authenticated_bsn,
        subject_identifier=request.subject_identifier,
        subject_type=request.subject_type,
        required_scope=get_required_scope(request.law)
    )

    if not authorized:
        raise HTTPException(403, detail=f"Not authorized: {details['reason']}")

    # Execute law
    result = engine.execute(
        service=request.service,
        law=request.law,
        parameters={
            "SUBJECT_IDENTIFIER": request.subject_identifier,
            "SUBJECT_TYPE": request.subject_type,
            **request.parameters
        }
    )

    # Log execution
    audit_log.write({
        "timestamp": datetime.now(),
        "actor_bsn": authenticated_bsn,
        "subject_identifier": request.subject_identifier,
        "subject_type": request.subject_type,
        "law": request.law,
        "result": "SUCCESS",
        "authorization_details": details
    })

    return result
```

### Fase 2: KVK Integratie (2-3 weken)

**KVK API Configuratie:**
```python
# config/kvk.py
class KVKConfig:
    # Voor overheidsorganisaties met BSN-toegang
    KVK_API_ENDPOINT = "https://api.kvk.nl/api/v2/..."
    KVK_API_KEY = os.getenv("KVK_API_KEY")
    KVK_HAS_BSN_ACCESS = os.getenv("KVK_BSN_ACCESS", "false") == "true"

    # Cache configuratie (compliance met KVK gebruiksvoorwaarden)
    KVK_CACHE_TTL = 86400  # 24 uur
    KVK_REFRESH_ON_CRITICAL_ACTION = True

# services/kvk_service.py
class KVKService:
    def get_companies_for_bsn(self, bsn: str) -> list:
        """
        Haal bedrijven op waar BSN bestuurder van is

        Vereist: KVK API toegang met BSN-velden
        """
        if not settings.KVK_HAS_BSN_ACCESS:
            raise ValueError("No KVK BSN access - use manual verification instead")

        # Check cache
        cached = cache.get(f"kvk:bsn:{bsn}")
        if cached:
            return cached

        # Query KVK API
        response = requests.get(
            f"{settings.KVK_API_ENDPOINT}/functionarissen",
            params={"bsn": bsn},
            headers={"apikey": settings.KVK_API_KEY}
        )

        companies = []
        for record in response.json()["results"]:
            companies.append({
                "kvk_nummer": record["kvkNummer"],
                "rsin": record["rsin"],
                "company_name": record["handelsnaam"],
                "function": record["functie"],
                "authority_type": record["bevoegdheid"],
                "valid_from": record["ingangsdatum"],
                "valid_until": record.get("einddatum")
            })

        # Cache result
        cache.set(f"kvk:bsn:{bsn}", companies, ttl=settings.KVK_CACHE_TTL)

        return companies
```

### Fase 3: UI Rollen Dashboard (1-2 weken)

**Component:**
```typescript
// components/RoleSelector.tsx
interface Role {
  type: 'self' | 'representative' | 'officer';
  identifier: string;
  identifierType: 'BSN' | 'RSIN';
  name: string;
  details?: {
    function?: string;
    authority?: string;
    scope?: string;
  };
}

export function RoleSelector() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  useEffect(() => {
    // Fetch roles after DigiD login
    fetch('/api/identity/roles')
      .then(res => res.json())
      .then(data => {
        const allRoles: Role[] = [
          // Self
          {
            type: 'self',
            identifier: data.self.bsn,
            identifierType: 'BSN',
            name: data.self.name
          },
          // Representatives of natural persons
          ...data.as_representative_of_persons.map(p => ({
            type: 'representative' as const,
            identifier: p.bsn,
            identifierType: 'BSN' as const,
            name: p.name,
            details: {
              authority: p.authority_type,
              scope: p.scope
            }
          })),
          // Officers of companies
          ...data.as_officer_of_companies.map(c => ({
            type: 'officer' as const,
            identifier: c.rsin,
            identifierType: 'RSIN' as const,
            name: c.company_name,
            details: {
              function: c.function,
              authority: c.authority_type,
              kvk: c.kvk_nummer
            }
          }))
        ];
        setRoles(allRoles);
      });
  }, []);

  return (
    <div className="role-selector">
      <h2>Welkom {roles[0]?.name}</h2>
      <p>Handelen als:</p>

      {roles.map(role => (
        <RoleCard
          key={`${role.type}-${role.identifier}`}
          role={role}
          selected={selectedRole?.identifier === role.identifier}
          onSelect={() => setSelectedRole(role)}
        />
      ))}

      <button onClick={() => proceedWithRole(selectedRole)}>
        Doorgaan
      </button>
    </div>
  );
}
```

### Fase 4: Extend Wetten (1 week)

**Law Definition Updates:**
```yaml
# law/omgevingswet/werkgebonden_personenmobiliteit/RVO-2024-07-01.yaml
properties:
  parameters:
    # NIEUW: Subject parameters (wie/wat wordt beoordeeld)
    - name: "SUBJECT_IDENTIFIER"
      description: "BSN (voor eenmanszaak) of RSIN (voor rechtspersoon)"
      type: "string"
      required: true

    - name: "SUBJECT_TYPE"
      description: "Type subject"
      type: "enum"
      values: ["NATUURLIJK_PERSOON", "RECHTSPERSOON"]
      required: true

    # NIEUW: Actor parameter (wie voert uit - voor audit)
    - name: "ACTOR_BSN"
      description: "BSN van persoon die deze wet uitvoert"
      type: "string"
      required: true
      audit_only: true  # Niet gebruikt in berekening, alleen voor logging

    # BESTAAND: KVK_NUMMER blijft bestaan voor backwards compatibility
    - name: "KVK_NUMMER"
      description: "KvK nummer van de organisatie"
      type: "string"
      required: false  # Nu optioneel - kan via SUBJECT_IDENTIFIER
      maps_to: "SUBJECT_IDENTIFIER"  # Via resolver
      when_subject_type: "RECHTSPERSOON"

  # NIEUW: Authorization requirements
  authorization:
    required: true
    required_scope: "VOLLEDIG"  # Of "FINANCIEEL", "SPECIFIEK"

requirements:
  # NIEUW: Authorization check VOOR other requirements
  - operation: IS_AUTHORIZED
    actor: "$ACTOR_BSN"
    subject: "$SUBJECT_IDENTIFIER"
    subject_type: "$SUBJECT_TYPE"
    required_scope: "$VOLLEDIG"
    error_message: "U bent niet bevoegd om deze wet uit te voeren namens dit subject"

  # BESTAAND: Business logic requirements
  - all:
    - subject: "$VERSTREKT_MOBILITEITSVERGOEDING"
      operation: EQUALS
      value: true
    - operation: GREATER_OR_EQUAL
      subject: "$AANTAL_WERKNEMERS"
      value: 100
```

**Engine Updates:**
```python
# machine/engine.py
class Engine:
    def execute(
        self,
        service: str,
        law: str,
        parameters: dict,
        reference_date: datetime = None
    ) -> dict:
        """Execute law with authorization check"""

        law_def = self.load_law(service, law)

        # Extract subject and actor
        actor_bsn = parameters.get("ACTOR_BSN")
        subject_identifier = parameters.get("SUBJECT_IDENTIFIER")
        subject_type = parameters.get("SUBJECT_TYPE")

        # Check authorization (if required by law)
        if law_def.get("authorization", {}).get("required"):
            required_scope = law_def["authorization"].get("required_scope")

            checker = AuthorizationChecker()
            authorized, details = checker.can_act_for(
                actor_bsn=actor_bsn,
                subject_identifier=subject_identifier,
                subject_type=subject_type,
                required_scope=required_scope
            )

            if not authorized:
                raise UnauthorizedError(
                    f"Not authorized to execute {law} for {subject_identifier}: {details['reason']}"
                )

        # Execute law (existing logic)
        result = self._execute_actions(law_def, parameters, reference_date)

        # Audit log
        self._write_audit_log({
            "timestamp": datetime.now(),
            "actor_bsn": actor_bsn,
            "subject_identifier": subject_identifier,
            "subject_type": subject_type,
            "law": f"{service}/{law}",
            "result": "SUCCESS",
            "output": result
        })

        return result
```

### Fase 5: Testing (2 weken)

**Behave scenarios:**
```gherkin
# features/machtigingen.feature
Feature: Machtigingen en Vertegenwoordiging

  Scenario: Bestuurder vraagt RVO subsidie aan via DigiD
    Given persoon "Jan de Vries" met BSN "200000001"
    And "Jan" is bestuurder van "Tech B.V." KVK "12345678" RSIN "001234567"
    And koppeling is geverifieerd via KVK API
    When "Jan" logt in met DigiD
    Then "Jan" ziet rol "Bestuurder van Tech B.V."
    When "Jan" selecteert rol "Bestuurder van Tech B.V."
    And "Jan" vraagt "WPM rapportageverplichting" aan
    Then WPM wordt correct berekend voor RSIN "001234567"
    And audit log toont:
      | actor_bsn  | subject_identifier | subject_type  | law                                     |
      | 200000001  | 001234567          | RECHTSPERSOON | omgevingswet/werkgebonden_personenmobiliteit |

  Scenario: Bewindvoerder vraagt zorgtoeslag aan via DigiD
    Given persoon "Marie Peters" met BSN "300000001"
    And "Marie" is bewindvoerder van "Piet Jansen" BSN "100000001"
    And machtiging type "BEWINDVOERING" scope "FINANCIEEL"
    And machtiging is geverifieerd via Rechtspraak
    When "Marie" logt in met DigiD
    Then "Marie" ziet rol "Bewindvoerder van Piet Jansen"
    When "Marie" selecteert rol "Bewindvoerder van Piet Jansen"
    And "Marie" vraagt "zorgtoeslag" aan
    Then zorgtoeslag wordt berekend voor BSN "100000001"
    And audit log toont:
      | actor_bsn  | subject_identifier | authority_type | law            |
      | 300000001  | 100000001          | BEWINDVOERING  | zorgtoeslagwet |

  Scenario: Onbevoegd persoon kan niet namens bedrijf handelen
    Given persoon "Henk Bakker" met BSN "400000001"
    And "Henk" is GEEN bestuurder van "Tech B.V."
    When "Henk" logt in met DigiD
    Then "Henk" ziet GEEN rol "Bestuurder van Tech B.V."
    When "Henk" probeert WPM aan te vragen voor RSIN "001234567"
    Then krijgt "Henk" foutmelding "Not authorized"
    And audit log toont GEEN uitvoering van wet

  Scenario: Accountant vraagt belastingaangifte aan met intermediair machtiging
    Given persoon "Lisa de Boer" met BSN "500000001"
    And "Lisa" is accountant
    And "Lisa" heeft intermediair machtiging voor "Bob Smit" BSN "600000001"
    And machtiging type "BELASTINGDIENST_INTERMEDIAIR" scope "INKOMSTENBELASTING"
    And machtiging is geverifieerd via Logius Machtigingenregister
    When "Lisa" logt in met DigiD
    Then "Lisa" ziet rol "Intermediair voor Bob Smit"
    When "Lisa" selecteert rol "Intermediair voor Bob Smit"
    And "Lisa" vraagt "inkomstenbelasting" aan
    Then IB wordt berekend voor BSN "600000001"
    And audit log toont:
      | actor_bsn  | subject_identifier | authority_type                | scope              |
      | 500000001  | 600000001          | BELASTINGDIENST_INTERMEDIAIR  | INKOMSTENBELASTING |
```

---

## Open Vragen

### 1. EU-burgers & Niet-BSN Scenario's

**Vraag:** Hoe werkt dit voor iemand zonder BSN?

**Voorbeelden:**
- EU-burger die bestuurder is van Nederlands bedrijf
- Buitenlandse ingezetene met verblijfsvergunning
- Grensarbeider

**Onderzoek nodig:**
- Welke identifier heeft niet-BSN persoon in KVK?
- Is er alternatief (buitenlands fiscaal nummer)?
- Kunnen zij inloggen met eIDAS-middel?
- Hoe mappen we eIDAS-identifier naar KVK-record?

**Mogelijk antwoord:**
```yaml
Alternative identifiers:
  - BSN (Nederlandse burgers)
  - eIDAS_ID (EU-burgers via eIDAS)
  - FOREIGN_TAX_ID (niet-EU met verblijfsvergunning)

KVK stores:
  - Voor Nederlanders: BSN
  - Voor niet-Nederlanders: Foreign identifier

Authentication:
  - Nederlanders: DigiD
  - EU-burgers: eIDAS login
  - Mapping: eIDAS_ID → KVK record → RSIN
```

**TODO:** Verder onderzoek nodig!

### 2. KVK BSN-toegang

**Vraag:** Krijgt RegelRecht daadwerkelijk toegang tot KVK API met BSN-velden?

**Vereisten:**
- RegelRecht moet erkend zijn als overheidsorganisatie OF
- Erkende uitvoeringsorganisatie (zoals SVB, DUO)

**Alternatieven als GEEN toegang:**
- Optie A: Eenmalige eHerkenning verificatie
- Optie B: Verificatiecode naar KVK-adres
- Optie C: Hybride model (publieke KVK API + eigen matching)

**TODO:** Juridisch afklaren wat RegelRecht's status is.

### 3. Privacy Impact Assessment

**Vraag:** Mogen we BSN-RSIN koppelingen opslaan in eigen database?

**AVG/GDPR overwegingen:**
- BSN is bijzonder persoonsgegeven
- Doelbinding: alleen voor wetsuitvoering
- Minimale dataverzameling
- Bewaartermijn (7 jaar Archiefwet?)
- Recht op inzage/correctie/verwijdering

**TODO:** DPIA (Data Protection Impact Assessment) uitvoeren.

### 4. Rechterlijke Registers Toegang

**Vraag:** Hoe krijgen we toegang tot curator/bewindvoerder data?

**Huidige situatie:**
- Centraal Curatele Register bestaat
- Centraal Bewindregister bestaat
- GEEN publieke API (nog niet)

**Opties:**
- Samenwerking met Rechtspraak.nl
- Integratie met bestaande systemen (bijv. via SVB, gemeentes)
- Manuele upload door curator/bewindvoerder (tijdelijk)

**TODO:** Overleg met Rechtspraak en/of pilotgemeenten.

### 5. eHerkenning Afbouw

**Vraag:** Kunnen we eHerkenning volledig uitfaseren?

**Praktische overwegingen:**
- Niet alle bedrijven hebben DigiD-gebruikers met KVK-toegang
- Legacy systemen zijn afhankelijk van eHerkenning
- Overgangsperiode nodig?

**Voorstel:**
- **Korte termijn**: Hybride (DigiD-first, eHerkenning fallback)
- **Lange termijn**: Volledig DigiD-centrisch (na KVK integratie)

---

## Conclusie

Het DigiD-centrische model biedt een **veiligere, eenvoudigere en gebruiksvriendelijkere** oplossing dan het huidige eHerkenning-systeem. Door BSN en RSIN als universele identifiers te gebruiken, en DigiD als authenticatiemiddel, kunnen we:

✅ **Fraude tegengaan** (persoonlijke DigiD niet deelbaar)
✅ **Audit trail verbeteren** (altijd BSN van handelende persoon bekend)
✅ **UX vereenvoudigen** (één login-systeem voor alles)
✅ **Kosten reduceren** (geen eHerkenning-abonnementen)
✅ **Privacy waarborgen** (geen commerciële tussenpersonen)

De implementatie is haalbaar in **11-14 weken**, mits we KVK API-toegang met BSN-velden kunnen verkrijgen. Zo niet, dan is er een fallback via eenmalige eHerkenning-verificatie.

**Aanbeveling:** Start met Fase 1 (Identity & Authorization Core) en parallel onderzoek naar KVK toegang en EU-burgers scenario's.

---

## Advanced Architectuur: Self-Sovereign Identity (SSI) - De Ideale Toekomst

### Visie: One Identity, Infinite Roles

Het huidige systeem met BSN, RSIN, eHerkenning is een pragmatische maar gefragmenteerde oplossing. De **ideale** architectuur zou gebaseerd zijn op **Self-Sovereign Identity (SSI)** principes met **Decentralized Identifiers (DIDs)** en **Verifiable Credentials (VCs)**.

### Kernprincipes

1. **Universal Digital Identity**: Elke persoon heeft ÉÉN cryptografische identiteit die werkt voor ALLES, OVERAL in de EU
2. **Self-Custody**: Burgers beheren hun eigen identiteit in een digitale wallet, niet de overheid
3. **Privacy by Design**: Minimale data-uitwisseling via selective disclosure en zero-knowledge proofs
4. **Decentralization**: Geen centrale identity database, gedistribueerde verificatie
5. **Cryptographic Trust**: Verificatie via cryptografie, niet via centrale registers

---

### 1. Universal Identity Layer

#### Probleem met huidige systemen

```
Te veel identifiers:
├─ BSN (alleen NL)
├─ eIDAS persistent ID (per land verschillend)
├─ Paspoort nummer (niet digitaal)
├─ RSIN, EUID, KVK, LEI voor bedrijven
└─ Verschillende systemen per overheidsinstantie
```

#### Ideale oplossing: W3C Decentralized Identifiers (DIDs)

**Voorbeeld DIDs:**
```
Personen:
  did:eu:nl:person:abc123xyz456     # Nederlandse burger
  did:eu:de:person:def789ghi012     # Duitse burger

Bedrijven:
  did:eu:nl:company:kvk:12345678    # Nederlands bedrijf
  did:eu:de:company:hrb:98765       # Duits bedrijf

Autoriteiten:
  did:eu:nl:authority:kvk           # KVK als issuer
  did:eu:nl:authority:rechtspraak   # Rechtspraak als issuer
```

**Eigenschappen:**
- ✅ Werkt EU-breed (en wereldwijd via W3C standaard)
- ✅ Persoon BEZIT zijn eigen identiteit (self-sovereignty)
- ✅ Geen centrale database nodig (privacy!)
- ✅ Cryptografisch verifieerbaar (niet te vervalsen)
- ✅ Kan niet gestolen/gekopieerd worden (private key vereist)

**Technische werking:**
```yaml
Bij geboorte/immigratie:
  1. Overheid genereert DID voor persoon
  2. Persoon krijgt private key (only owner has this)
  3. Public key wordt gepubliceerd in DID registry (distributed)

Voor authenticatie:
  1. Persoon bewijst bezit van private key (cryptographic challenge)
  2. Geen username/password nodig
  3. Biometrie (face/fingerprint) unlocks wallet met private key

Cross-border:
  1. EU-burger met DE-DID logt in bij NL dienst
  2. Automatische trust via EU DID registry
  3. Wederzijdse erkenning (zoals eIDAS, maar cryptografisch)
```

---

### 2. EU Digital Identity Wallet 2.0

**Inhoud van de wallet:**

```
┌─────────────────────────────────────────┐
│  EU DIGITAL IDENTITY WALLET             │
│                                         │
│  🆔 My Identity                         │
│  ├─ DID: did:eu:nl:person:abc123       │
│  ├─ Name: Jan de Vries                 │
│  ├─ Date of Birth: 1990-01-01          │
│  └─ Nationality: NL                    │
│                                         │
│  🏢 My Roles (Verifiable Credentials)  │
│  ├─ 👤 Myself (always)                 │
│  ├─ 🏢 Director of Tech B.V.           │
│  │   Issuer: KVK (cryptographically signed) │
│  │   Valid: 2023-06-15 → present       │
│  │   Scope: Full authority             │
│  ├─ 🛡️ Guardian of Piet Jansen         │
│  │   Issuer: Court Amsterdam           │
│  │   Valid: 2024-01-01 → 2029-01-01   │
│  │   Scope: Financial matters          │
│  └─ 💼 Tax Intermediary for 5 clients  │
│      Issuer: Belastingdienst           │
│      Valid: 2024-01-01 → 2025-12-31   │
│                                         │
│  📜 My Credentials                      │
│  ├─ Master's Degree (University X)     │
│  ├─ Driver's License (RDW)             │
│  └─ Professional Certificates          │
│                                         │
│  🔐 Active Sessions                     │
│  └─ Logged in as: Director of Tech B.V.│
└─────────────────────────────────────────┘
```

**Key Features:**

1. **Self-Custody**: Burger beheert wallet, niet overheid
2. **Selective Disclosure**: Deel alleen wat nodig is voor specifieke actie
3. **Zero-Knowledge Proofs**:
   - Bewijs "ik ben 18+" zonder geboortedatum te delen
   - Bewijs "ik ben bevoegd bestuurder" zonder volledig KVK extract
4. **Revocable**: Machtigingen kunnen elk moment ingetrokken worden
5. **Auditable**: Burger ziet altijd wie wat heeft gevraagd

---

### 3. Verifiable Credentials voor Machtigingen

**In plaats van database met BSN↔RSIN relaties:**

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  "type": ["VerifiableCredential", "CorporateOfficerCredential"],
  "issuer": "did:eu:nl:authority:kvk",
  "issuanceDate": "2023-06-15T00:00:00Z",
  "expirationDate": null,

  "credentialSubject": {
    "id": "did:eu:nl:person:abc123",
    "role": "director",
    "organization": {
      "id": "did:eu:nl:company:kvk:12345678",
      "name": "Tech B.V.",
      "rsin": "001234567"
    },
    "authority": "independent",
    "scope": "full"
  },

  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2023-06-15T10:00:00Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "did:eu:nl:authority:kvk#key-1",
    "jws": "eyJhbGc...cryptographic_signature...xyz"
  }
}
```

**Voordelen:**

1. **Cryptografisch Verifieerbaar**:
   - Handtekening kan niet vervalst worden
   - KVK heeft deze credential getekend met private key
   - Iedereen kan verifiëren met KVK's public key (geen API call!)

2. **Geen Centrale Database**:
   - Credential zit in gebruiker's wallet
   - RegelRecht slaat niets op (stateless verification)
   - Privacy by design (geen honeypot van persoonlijke data)

3. **Real-time Revocatie**:
   ```yaml
   KVK publiceert revocation list:
     - Credential ID xyz123: REVOKED at 2025-10-16T09:00:00Z
     - Reden: Persoon is geen bestuurder meer

   RegelRecht checkt bij elke actie:
     - Is credential signature geldig? ✓
     - Staat credential op revocation list? → Denied
   ```

4. **Cross-Border Compatible**:
   ```yaml
   Duitse bestuurder van NL bedrijf:
     - Credential issued by KVK (NL authority)
     - Stored in Duitse EU Wallet
     - Works in hele EU (mutual recognition)
   ```

---

### 4. Authorization Flow (Ideaal Scenario)

```
┌──────────────────────────────────────────────────────────┐
│  STAP 1: LOGIN (Zero-database)                          │
└──────────────────────────────────────────────────────────┘

User      → Opens RegelRecht
          → Clicks "Login with EU Wallet"
          → Scans QR code / NFC / Bluetooth pairing

Wallet    → "RegelRecht wil je identiteit verifiëren"
User      → Approves (biometric: face/fingerprint)

Wallet    → Sends: DID (did:eu:nl:person:abc123)
          → Cryptographic proof of ownership

RegelRecht → Verifies proof
          → Session established (NO database lookup!)

┌──────────────────────────────────────────────────────────┐
│  STAP 2: ROLE DISCOVERY (Instant verification)          │
└──────────────────────────────────────────────────────────┘

RegelRecht → "Show me your role credentials"

Wallet     → Presents available VCs:
             1. Director VC (KVK-signed)
             2. Guardian VC (Court-signed)
             3. Tax Intermediary VC (BD-signed)

RegelRecht → Verifies signatures cryptographically:
             For each VC:
               1. Extract issuer DID from VC
               2. Fetch issuer's public key from DID registry
               3. Verify signature matches
               4. Check revocation list
             → All verified in <100ms

          → Shows roles to user

GEEN KVK API call!
GEEN database queries!
Pure cryptographic verification!

┌──────────────────────────────────────────────────────────┐
│  STAP 3: ROLE SELECTION & SESSION                       │
└──────────────────────────────────────────────────────────┘

User       → Selects: "Director of Tech B.V."

RegelRecht → Asks wallet: "Sign this session"
Wallet     → "Act as Director of Tech B.V. for 2 hours?"
User       → Approves (biometric)
Wallet     → Returns signed session token

Session:
  actor_did: did:eu:nl:person:abc123
  acting_as_did: did:eu:nl:company:kvk:12345678
  credential_id: kvk-director-xyz123
  scope: full
  valid_until: now + 2h
  signature: <user's wallet signature>

┌──────────────────────────────────────────────────────────┐
│  STAP 4: LAW EXECUTION (with audit trail)               │
└──────────────────────────────────────────────────────────┘

User       → Requests WPM calculation

RegelRecht → Verifies:
             1. Session still valid? ✓
             2. VC still valid (check revocation)? ✓
             3. Scope sufficient? ✓

          → Executes law for: did:eu:nl:company:kvk:12345678

          → Audit trail (cryptographically signed):
             {
               timestamp: "2025-10-16T14:30:00Z",
               actor_did: "did:eu:nl:person:abc123",
               subject_did: "did:eu:nl:company:kvk:12345678",
               credential_id: "kvk-director-xyz123",
               law: "omgevingswet/wpm",
               result: {...},
               signature: <user wallet signature of entire action>
             }
```

---

### 5. Privacy-Preserving Features

#### Selective Disclosure

```yaml
Traditional (reveal everything):
  Request: "Prove you're director"
  Response:
    - BSN: 200000001
    - Name: Jan de Vries
    - Birthdate: 1990-01-01
    - Address: Hoofdstraat 1, Amsterdam
    - ALL companies where director
    - Full KVK extract
    - Salary information
    # Massive oversharing!

Ideal (selective disclosure):
  Request: "Prove you're director of company X"
  Response:
    - VC for company X directorship only
    - Cryptographic proof of validity
    - NOTHING ELSE

  Other companies: Hidden
  Personal details: Hidden
  Minimal exposure!
```

#### Zero-Knowledge Proofs

```python
# Scenario: Wet vereist "persoon is 18+"

# Traditional:
birthdate = "1990-01-01"  # Shared
age = calculate_age(birthdate)  # 35
assert age >= 18  # True

# Ideal (ZKP):
proof = wallet.generate_zkp(
    claim="older_than_18",
    actual_value=birthdate,  # NOT shared!
    threshold=18
)

# RegelRecht verifies:
assert verify_zkp(proof, issuer_public_key)
# Result: TRUE (person is 18+)
# Revealed: NOTHING about actual birthdate!

# Mathematical magic: Can prove statement is true
# WITHOUT revealing underlying data
```

**Use cases:**
- "Ik ben 18+" zonder geboortedatum
- "Ik woon in Amsterdam" zonder exact adres
- "Ik verdien >€30k" zonder exact inkomen
- "Ik ben bevoegd bestuurder" zonder KVK details

---

### 6. Real-Time Verification

#### Probleem met caching:
```
Database (1 dag oud): "Jan is bestuurder"
Reality (vanochtend):  "Jan heeft ontslag genomen"
Result:               "Jan kan NOG STEEDS namens bedrijf handelen" ❌
```

#### Ideale oplossing: Short-lived Credentials + Revocation Lists

**Optie 1: Short-lived VCs**
```json
{
  "issuanceDate": "2025-10-16T08:00:00Z",
  "expirationDate": "2025-10-16T20:00:00Z",  // 12 uur geldig

  // After 12 hours: auto-expired
  // Wallet auto-refresh elke nacht
  // Max staleness: 12 uur
}
```

**Optie 2: Real-time Revocation**
```yaml
KVK maintains revocation registry:
  https://kvk.nl/vc/revocations

  Content:
    credential_id: xyz123
    revoked_at: 2025-10-16T09:00:00Z
    reason: "No longer director"

RegelRecht checks (every action):
  GET https://kvk.nl/vc/revocations/xyz123

  If revoked: DENY immediately

  Latency: ~50ms (CDN-cached)
  Accuracy: Real-time (max 1 min delay)
```

**Optie 3: Blockchain Revocation Registry**
```yaml
Immutable revocation log on distributed ledger:

  Block N:
    - Credential xyz123: REVOKED
    - Timestamp: 2025-10-16T09:00:00Z
    - Signed by: KVK authority

  Verification:
    - Query distributed nodes
    - Consensus-based (no single point of failure)
    - Cryptographically provable
```

---

### 7. Cross-Border (EU-wide)

**Scenario: Duitse bestuurder van Nederlands bedrijf**

```yaml
Step 1: KVK issues VC to German citizen
  {
    credentialSubject: {
      id: "did:eu:de:person:def789",        # German DID
      role: "director",
      organization: {
        id: "did:eu:nl:company:kvk:12345678"  # NL company
      }
    },
    issuer: "did:eu:nl:authority:kvk"       # NL authority
  }

Step 2: German citizen opens RegelRecht
  - Logs in with German EU Wallet
  - Wallet connects via eIDAS trust framework
  - Presents KVK-issued VC

Step 3: RegelRecht verification
  - Extracts issuer: did:eu:nl:authority:kvk
  - Fetches KVK public key from EU DID registry
  - Verifies signature
  - Accepted! (EU mutual recognition)

Step 4: German can act on behalf of NL company
  - No BSN needed
  - No special registration
  - Just German DID + NL credential
```

**Trust Framework:**
```yaml
EU DID Registry (distributed):

  Each country publishes authority DIDs:
    NL: did:eu:nl:authority:kvk        → KVK public key
        did:eu:nl:authority:rechtspraak → Court public key

    DE: did:eu:de:authority:handelsregister
    FR: did:eu:fr:authority:inpi
    # etc.

  Mutual recognition:
    If credential signed by recognized EU authority
    → Accept in ALL member states

  No central database:
    → Distributed trust model
    → Each country maintains own registry
    → EU-level interoperability via cryptography
```

---

### 8. Unified Authorization Dashboard

```
┌─────────────────────────────────────────────────────┐
│  MY AUTHORIZATIONS DASHBOARD                        │
│                                                     │
│  👤 Who can act on my behalf:                      │
│  ├─ Marie Peters (Tax Accountant)                  │
│  │   VC ID: bd-intermediary-abc456                 │
│  │   Scope: Tax filings only                       │
│  │   Valid: 2024-01-01 → 2025-12-31               │
│  │   Last used: 2 days ago                         │
│  │   [Revoke] [Extend] [Details] [Audit log]      │
│  │                                                  │
│  └─ Gemeente Amsterdam (Benefits)                  │
│      VC ID: gemeente-benefits-def789               │
│      Scope: Housing benefits application           │
│      Valid: One-time use (expires after use)       │
│      [Revoke] [Details]                            │
│                                                     │
│  🏢 I can act on behalf of:                        │
│  ├─ Tech B.V. (Director)                           │
│  │   VC ID: kvk-director-xyz123                    │
│  │   Issuer: KVK (verified ✓)                      │
│  │   Scope: Full authority                         │
│  │   Issued: 2023-06-15                            │
│  │   Last used: Today 14:30                        │
│  │   [View VC] [Usage history] [Revocation status]│
│  │                                                  │
│  └─ Piet Jansen (Guardian - Financial)             │
│      VC ID: court-guardian-ghi789                  │
│      Issuer: Rechtbank Amsterdam (verified ✓)      │
│      Scope: Financial matters only                 │
│      Valid: 2024-01-01 → 2029-01-01               │
│      [View VC] [Usage history]                     │
│                                                     │
│  📜 Recent Activity (cryptographically signed):    │
│  ├─ 2025-10-16 14:30 - WPM calc (as Tech B.V.)     │
│  │   Signed: 0x8f4a... [Verify signature]          │
│  ├─ 2025-10-15 10:00 - Zorgtoeslag (self)          │
│  │   Signed: 0x9b2c... [Verify signature]          │
│  └─ 2025-10-14 16:45 - Tax filing (for Piet)       │
│      Signed: 0x1d7e... [Verify signature]          │
│                                                     │
│  [Request new credential] [Export audit log]       │
│  [Revoke all] [Privacy settings]                   │
└─────────────────────────────────────────────────────┘
```

**Features:**

1. **Complete Transparency**: Alles in één dashboard
2. **User Control**: Direct revoke, geen tussenpersoon
3. **Cryptographic Audit**: Elke actie is signed & verifiable
4. **Proactive Alerts**: "New credential requested by..."
5. **Cross-Service**: Works voor alle overheidsdiensten (unified)
6. **Privacy Dashboard**: See what data was shared when

---

### 9. Implementation Roadmap naar SSI

#### Fase 1: Foundation (0-6 maanden)

```yaml
Goals:
  - Implement DID/VC support in RegelRecht
  - Partner met EU Digital Identity Wallet pilot
  - KVK starts VC issuance (pilot met 10 bedrijven)

Technical:
  - Add VC verification library
  - Support DID authentication naast DigiD
  - Build credential wallet integration

Deliverables:
  - RegelRecht accepts VCs AND traditional auth (hybrid)
  - Proof of concept met 10 pilotbedrijven
  - Open source VC libraries voor NL overheid
  - Documentation + developer guides
```

#### Fase 2: Credentials Ecosystem (6-12 maanden)

```yaml
Goals:
  - Multiple issuers: KVK, Rechtspraak, Belastingdienst
  - Wallets kunnen credentials opslaan en presenteren
  - Revocation infrastructure operational

Technical:
  - KVK VC issuance API
  - Rechtbank VC issuance (curator/bewindvoerder)
  - Belastingdienst intermediair VCs
  - Real-time revocation registry

Deliverables:
  - VCs for: director, curator, bewindvoerder, intermediair
  - Revocation lists (HTTPS + optional blockchain)
  - Inter-authority trust framework (NL level)
  - 1000+ early adopters
```

#### Fase 3: Privacy Features (12-18 maanden)

```yaml
Goals:
  - Selective disclosure in alle wetten
  - Zero-knowledge proofs voor gevoelige data
  - Minimize data sharing across board

Technical:
  - Implement BBS+ signatures (selective disclosure)
  - ZKP library voor leeftijd, inkomen, locatie
  - Update alle law definitions met privacy specs

Deliverables:
  - Selective disclosure voor alle VCs
  - ZKP voor: leeftijd, inkomen, woonplaats, vermogen
  - Privacy impact analysis per wet
  - User privacy dashboard
```

#### Fase 4: EU Integration (18-24 maanden)

```yaml
Goals:
  - Full eIDAS 2.0 compliance
  - Cross-border VC acceptance
  - Mutual recognition framework operational

Technical:
  - EU DID registry integration
  - Support alle EU Digital Identity Wallets
  - Cross-border trust anchors

Deliverables:
  - EU-burgers can use RegelRecht seamlessly
  - NL credentials accepted in other EU countries
  - Pilot cross-border use cases (DE, BE, FR)
  - EU-wide interoperability proof
```

---

### 10. Vergelijking: Nu vs. Ideaal

| Aspect | Huidig Systeem | SSI/DID/VC Model |
|--------|---------------|------------------|
| **Identiteit** | Meerdere nummers (BSN, RSIN, etc.) | Eén universele DID |
| **Eigenaarschap** | Overheid owns identity | Burger owns identity (self-sovereign) |
| **Privacy** | Centrale databases | Self-custody wallet, geen centrale opslag |
| **Beveiliging** | Deelbare credentials (eHerkenning) | Cryptografisch, niet-deelbaar |
| **Verificatie** | API calls naar centrale registers | Cryptografische verificatie (offline mogelijk) |
| **Cross-border** | Complex (eIDAS per land) | Seamless (EU DID registry) |
| **Machtigingen** | Versnipperd per dienst/register | Unified in wallet |
| **Transparantie** | Onduidelijk wie wat mag | Crystal clear dashboard |
| **Actualiteit** | Cached (uren/dagen oud) | Real-time (revocation lists) |
| **Data sharing** | Oversharing (BSN, naam, alles) | Minimal (selective disclosure) |
| **User control** | Beperkt (via intermediairs) | Volledig (direct revoke) |
| **Audit trail** | Per dienst verschillend | Cryptographic, immutable, user-controlled |
| **Fraudebestendigheid** | Matig (deelbare accounts) | Hoog (cryptographic binding) |
| **Kosten** | eHerkenning €€/jaar | Infrastructuur cost, gratis voor gebruikers |

---

### 11. Filosofische Shift

#### Van "Government owns your identity" naar "You own your identity"

**Traditional (now):**
```
Overheid owns your BSN
  → Je vraagt permission om het te gebruiken
  → Overheid tracks alles
  → Jij hebt beperkte control
  → Centrale database is honeypot voor hackers
```

**Ideal (SSI):**
```
Jij owns your DID (private key in wallet)
  → Overheid issues credentials TO you
  → Jij decides when/where to use them
  → Jij hebt full control
  → Jij ziet everything that happens
  → No central database (privacy by design)
```

#### Privacy by Design

**Principe:** Default to minimal disclosure

```
Don't ask: "Who are you?" (all personal data)
Ask:       "Prove you can do X" (only authorization proof)

Don't store: Everything about everyone
Store:       Cryptographic proofs only

Don't share: BSN, name, birthdate by default
Share:       Only what's explicitly needed for THIS action
```

#### Decentralization

**Principe:** No single point of failure or control

```
No central identity database
  → Distributed across wallets (user-controlled)
  → Verified via cryptography (mathematical proof)
  → Trust via EU framework (mutual recognition)
  → Resilient to attacks (no honeypot)
  → No surveillance infrastructure
```

---

### 12. First Steps naar SSI in RegelRecht

Om dit te realiseren:

1. **Research & Education**
   - Deep dive into W3C DID/VC specifications
   - Study EU Digital Identity Wallet architecture
   - Learn from SSI pioneers (Sovrin, Hyperledger Indy, etc.)

2. **Pilot Partnership**
   - Partner met EU Digital Identity Wallet pilot
   - Work with early adopter bedrijven
   - Collaborate with KVK on VC issuance

3. **Technical POC**
   - Implement VC verification in RegelRecht (parallel to existing auth)
   - Build DID resolver for EU registry
   - Create reference implementation for NL government

4. **Advocacy & Standardization**
   - Lobby KVK to start issuing VCs
   - Work with Forum Standaardisatie on NL standards
   - Participate in EU eIDAS 2.0 implementation

5. **Open Source Ecosystem**
   - Build libraries voor NL overheid
   - Contribute to W3C DID/VC specs
   - Create developer documentation & SDKs

6. **Community Building**
   - Start working group met andere overheidsdiensten
   - Organize hackathons & pilots
   - Share learnings & best practices

**Philosophy: Start klein, denk groot!**

Begin met een pilot (10 bedrijven, 1 credential type), leer, itereer, en schaal op. De reis naar volledig SSI is multi-jaar, maar elke stap brengt waarde.

---

## 6. Juridische Haalbaarheid van SSI/DID/VC Architectuur

### 6.1 Juridisch Kader Analyse

Deze sectie onderzoekt of de voorgestelde Self-Sovereign Identity architectuur met Decentralized Identifiers (DIDs) en Verifiable Credentials (VCs) juridisch mogelijk is binnen de huidige Nederlandse en Europese wet- en regelgeving.

---

### 6.2 eIDAS 2.0 en EU Digital Identity Wallet

#### Status
**✅ JURIDISCH GEFUNDEERD EN VERPLICHT**

#### Bevindingen

De EU heeft op **29 februari 2024** de herziene eIDAS verordening (eIDAS 2.0) formeel aangenomen, die **in werking trad op 20 mei 2024**. Deze verordening vormt het juridische fundament voor SSI in Europa.

**Key Legal Provisions:**

**Verordening (EU) 2024/1183** - eIDAS 2.0:

- **Artikel 6a**: Introduceert de **European Digital Identity Wallet (EUDI Wallet)**
  - Lidstaten **VERPLICHT** om digitale identiteitswallets aan te bieden aan burgers en bedrijven
  - Deadline: **Binnen 24 maanden** na inwerkingtreding (dus **mei 2026**)
  - Wallets moeten **gratis** beschikbaar zijn voor natuurlijke personen

- **Artikel 5a**: Vereist dat EUDI Wallets:
  - Gebruiker volledige controle geven over identiteitsgegevens
  - Selective disclosure mogelijk maken (alleen noodzakelijke attributen delen)
  - Verifiable Credentials kunnen opslaan en presenteren
  - Cross-border interoperabiliteit garanderen

- **Artikel 45a-45d**: Regelt **Electronic Attestations of Attributes (EAAs)**
  - Dit zijn in essentie Verifiable Credentials
  - Juridische geldigheid over hele EU
  - Trusted issuer framework
  - W3C VC Data Model wordt genoemd als referentiestandaard

**Implementatie Deadlines:**
- **Mei 2026**: Lidstaten moeten EUDI Wallet aanbieden
- **November 2026**: High value use cases (rijbewijs, diploma's, etc.) moeten beschikbaar zijn
- **2027**: Volledige eIDAS 2.0 implementatie

#### Conclusie voor RegelRecht

✅ **VC's accepteren is juridisch volledig gefundeerd**
- EU-verordening heeft directe werking
- Nederland MOET EUDI Wallet implementeren tegen 2026
- Overheidsorganisaties MOGEN (en worden aangemoedigd) VC's te accepteren

⚠️ **Maar:** Nederlandse implementatiewetgeving moet nog volgen
- Technische standaarden in ontwikkeling
- NL moet bepalen welke overheidsorganisaties welke credentials uitgeven
- Forum Standaardisatie moet NL-specifieke profielen vaststellen

---

### 6.3 AVG/GDPR Compatibiliteit

#### Status
**⚠️ COMPATIBEL MAAR COMPLEX**

#### Bevindingen

De AVG/GDPR is technologie-neutraal en legt principes vast, niet specifieke technologieën. SSI/VCs zijn **in principe compatibel** met GDPR, maar er zijn **interpretatie-uitdagingen**.

**Positieve Aspecten:**

1. **Data Minimization (Art. 5(1)(c) GDPR)**
   - SSI/VCs met selective disclosure zijn **ideaal** voor data minimalisatie
   - Zero-knowledge proofs passen perfect bij dit principe
   - Betere compliance dan huidige systemen die vaak "alles" vragen

2. **Purpose Limitation (Art. 5(1)(b) GDPR)**
   - Verifiable Presentations zijn context-specifiek
   - Gebruiker controleert welke data voor welk doel wordt gedeeld
   - Betere logging van purpose per disclosure

3. **Storage Limitation (Art. 5(1)(e) GDPR)**
   - Verifiers hoeven VC's niet op te slaan (alleen verificatie-resultaat)
   - Credentials hebben ingebouwde expiry
   - User wallet is user-controlled (niet "opslag door verwerkingsverantwoordelijke")

**Uitdagingen:**

1. **Roles onder GDPR**
   - **VC Issuer** (bijv. KVK) = Verwerkingsverantwoordelijke bij uitgifte
   - **Wallet provider** = Verwerker? Of user zelf verwerkingsverantwoordelijke?
   - **Verifier** (bijv. RVO) = Verwerkingsverantwoordelijke bij verificatie
   - **Onduidelijkheid:** Juridische status van gebruiker als "holder" van eigen credentials

2. **Right to Erasure (Art. 17 GDPR) vs. Immutability**
   - Probleem: Als VC hash op blockchain staat, kan deze niet gewist worden
   - Oplossing: Revocation via off-chain lists (niet de credential zelf on-chain)
   - Oplossing: Privacy-preserving blockchains (alleen proof, geen data)
   - **Best practice:** Credential data alleen in wallet, niet on-chain

3. **Right to Rectification (Art. 16 GDPR)**
   - Probleem: Hoe wijzig je een uitgegeven credential?
   - Oplossing: Oude credential revoken + nieuwe uitgeven
   - Issuer blijft verantwoordelijk voor correctheid

4. **Data Protection Impact Assessment (Art. 35 GDPR)**
   - SSI-systeem vereist DPIA bij introductie
   - Wel: Lagere privacy risico's dan centraal systeem
   - Focus: Wallet security, revocation privacy, issuer trustworthiness

**GDPR Guidance:**

European Data Protection Board (EDPB) heeft nog **geen expliciete guidance** over SSI/VCs gepubliceerd. Wel algemene principes uit bestaande opinions:
- Guidelines 4/2019 over Article 25 (data protection by design): SSI past hier goed bij
- Opinion 5/2019 over identity verification: Decentralized solutions worden erkend
- Strategy 2021-2025: Ondersteunt privacy-enhancing technologies

#### Conclusie voor RegelRecht

✅ **SSI is GDPR-compliant mits correct geïmplementeerd**
- Geen fundamentele juridische barrières
- Vereist zorgvuldige rol-definitie (verwerkingsverantwoordelijke/verwerker)
- DPIA noodzakelijk bij introductie
- Best practices: Geen persoonlijke data on-chain, alleen revocation pointers

⚠️ **Aandachtspunten:**
- Duidelijke verwerkersovereenkomsten met wallet providers
- Transparantie naar gebruikers over datastromen
- Revocation mechanisme moet GDPR-proof zijn

---

### 6.4 BSN Wetgeving en Decentralized Identifiers

#### Status
**❌ BSN KAN NIET VERVANGEN WORDEN DOOR DID (nu)**

#### Bevindingen

De **Wet algemene bepalingen burgerservicenummer (Wabb)** regelt het gebruik van het BSN in Nederland.

**Relevante Wetsartikelen:**

**Artikel 1 Wabb**: Definieert BSN als uniek identificerend nummer voor natuurlijke personen
- BSN is wettelijk verplicht nummer voor contact met overheid
- Wordt toegekend door Minister van BZK
- Formaat: 9 cijfers met modulo-11 check

**Artikel 3 Wabb**: Gebruik BSN bij wettelijke plicht
- Organisaties **mogen** BSN alleen gebruiken als wet dit expliciet toestaat
- Lijst in Bijlage bij Wabb: welke organisaties voor welk doel

**Artikel 11 Wabb**: Centrale voorziening (BRP)
- BSN gekoppeld aan Basisregistratie Personen
- Unieke link tussen BSN en persoon
- Wettelijke taak Minister BZK

**Probleem:**
- Wabb **verplicht** BSN voor overheidscommunicatie
- Geen wettelijke basis om DID als **vervanging** te gebruiken
- DID wordt niet erkend als equivalent van BSN

**Mogelijkheden binnen huidige wet:**

✅ **DID NAAST BSN is wel mogelijk:**
- DID kan gebruikt worden als **authenticatiemethode** (zoals DigiD nu doet)
- BSN blijft het identificerende nummer
- Architecture: DID → authenticate → resolve to BSN → use BSN for laws

```
User proves control of DID
  ↓
RegelRecht verifies cryptographic proof
  ↓
DID linked to BSN in secure register
  ↓
Execute law with BSN as parameter
```

⚠️ **Hybrid Model:**
- DID voor authenticatie en authorization proof
- BSN voor identificatie in law execution
- VC bevat claim: "This DID is linked to BSN [encrypted/hashed]"
- Verifier resolves DID→BSN only when needed

#### Wetswijziging Noodzakelijk voor Volledige SSI

Om BSN volledig te vervangen door DID:

**Vereiste wijzigingen:**
1. **Wabb wijzigen**: DID toevoegen als alternatief identificerend nummer
2. **BRP wijzigen**: DID registreren als persoonsgegeven (naast BSN)
3. **DigiD-wetgeving**: DID-based authenticatie toestaan
4. **Sectorale wetten**: Overal waar "BSN" staat, ook "of DID" toevoegen

**Realiteit:**
- Dit is een **grote wetsoperatie** (tientallen wetten)
- Politieke wil nodig
- Waarschijnlijk niet voor 2030

#### Conclusie voor RegelRecht

❌ **BSN vervangen door DID: Niet juridisch mogelijk nu**
- Vereist fundamentele wetgeving wijzigingen
- Multi-jaar traject

✅ **Hybrid Model (DID + BSN): Wel mogelijk**
- DID voor authentication/authorization
- BSN blijft identifier for law execution
- Geen wetswijziging nodig
- Geleidelijke transitie mogelijk

**Aanbevolen Architectuur:**
```yaml
# Verifiable Credential from KVK
credentialSubject:
  id: "did:eu:nl:person:abc123"  # Public identifier
  linkedIdentifiers:
    - type: "BSN"
      value: "encrypted_or_hashed"  # Not visible to all verifiers
    - type: "RSIN"
      value: "001234567"
  role: "director"
  organization:
    id: "did:eu:nl:company:kvk:12345678"
    kvk_nummer: "12345678"
```

---

### 6.5 KVK Bevoegdheden voor Uitgifte Verifiable Credentials

#### Status
**⚠️ JURIDISCH ONDUIDELIJK - IMPLEMENTATIEVERORDENING NODIG**

#### Bevindingen

**Huidige Wettelijke Basis KVK:**

**Handelsregisterwet 2007**:
- **Artikel 2**: KVK houdt handelsregister bij
- **Artikel 3**: Informatie in handelsregister is openbaar
- **Artikel 22**: KVK verstrekt uittreksels en inlichtingen
- **Artikel 23**: Vorm van verstrekking wordt bij ministeriële regeling vastgesteld

**Huidige Praktijk:**
- KVK geeft **digitaal ondertekende PDF-uittreksels** af
- Gebruikt PKI (Public Key Infrastructure) certificaten
- Voldoet aan eIDAS 1.0 qualified signatures
- **GEEN** W3C Verifiable Credentials (nog niet)

**eIDAS 2.0 Perspective:**

Met eIDAS 2.0 worden KVK-uittreksels **qualified electronic attestations of attributes**:
- **Artikel 45a eIDAS 2.0**: Definieert qualified EAA
- **Artikel 45b**: Eisen aan qualified trust service providers voor EAA's
- KVK zou **qualified trust service provider** kunnen worden voor company credentials

**Juridische Analyse:**

✅ **Argumenten PRO (KVK mag VCs uitgeven):**

1. **Impliciete bevoegdheid** (Handelsregisterwet art. 22)
   - Wet zegt: KVK "verstrekt uittreksels en inlichtingen"
   - Zegt niet HOE → ministeriële regeling bepaalt vorm
   - VC is gewoon een nieuwe vorm van uittreksel

2. **eIDAS 2.0 directe werking**
   - Als EU-verordening kan KVK credentials uitgeven als "qualified EAA"
   - Nederland moet dit faciliteren (art. 45c eIDAS 2.0)

3. **Bestaande digitale handtekening autoriteit**
   - KVK gebruikt al PKI certificates
   - VC signing is technisch vergelijkbaar
   - Alleen format wijzigt (PDF → JSON-LD)

⚠️ **Argumenten CONTRA (onduidelijkheden):**

1. **Geen expliciete VC-bevoegdheid in Handelsregisterwet**
   - Wet noemt alleen "uittreksels" (letterlijke uittreksels?)
   - VCs bevatten claims, niet complete uittreksels
   - Ministeriële regeling moet dit expliciet maken

2. **Trust service provider status onduidelijk**
   - Moet KVK eerst qualified trust service provider worden onder eIDAS 2.0?
   - Vereist dit aparte certificering/toezicht?
   - Rol Agentschap Telecom (toezicht eIDAS) niet duidelijk

3. **Liability bij verkeerde credentials**
   - Als VC onjuiste claim bevat → wie aansprakelijk?
   - Huidige wet regelt fouten in uittreksels (art. 36 Handelsregisterwet)
   - Geldt dit ook voor VCs?

**Wat Andere EU-landen Doen:**

- **Estland**: E-residency geeft blockchain-backed credentials (niet W3C VCs)
- **Duitsland**: Bundesnetzagentur onderzoekt VC-uitgifte voor business registers
- **België**: Crossroads Bank for Enterprises (CBE) in pilot fase met VCs
- **Geen enkel land** heeft nog production W3C VCs van business registers

#### Implementatie Route voor KVK

**Kortste Route naar Productie:**

1. **Ministeriële Regeling wijzigen** (Regeling handelsregister 2009)
   - Voeg toe: "Uittreksels kunnen worden verstrekt als Verifiable Credentials conform W3C standaard"
   - Verwijs naar eIDAS 2.0 artikel 45a (qualified EAA)
   - Specificeer formaat, signing methode, revocation

2. **KVK wordt Qualified Trust Service Provider**
   - Aanvragen bij Agentschap Telecom
   - Voldoen aan eIDAS 2.0 Artikel 45b eisen
   - Audit door conformity assessment body

3. **Pilot programma starten**
   - Begin met 1 credential type (bijv. "Director Credential")
   - Limited scope (10-50 bedrijven)
   - Juridische monitoring (past binnen wet?)

4. **Scaling besluit**
   - Na pilot: evaluatie juridische houdbaarheid
   - Evt. Handelsregisterwet aanpassen voor expliciete VC-bevoegdheid
   - Roll-out naar alle bedrijven

#### Conclusie voor RegelRecht

⚠️ **KVK VC-uitgifte: Juridisch onduidelijk maar waarschijnlijk haalbaar**

**Kortetermijn (2025-2026):**
- ❌ KVK geeft nog geen VCs uit
- ✅ RegelRecht kan voorbereiden door VC-verificatie te implementeren
- ✅ Lobby/samenwerking met KVK om pilot te starten

**Middellange termijn (2026-2028):**
- ✅ Ministeriële regeling aanpassen (relatief makkelijk)
- ✅ KVK pilot met VCs (eIDAS 2.0 compliance)
- ✅ RegelRecht als early adopter/reference implementation

**Lange termijn (2028+):**
- ✅ Wettelijke basis in Handelsregisterwet verstevigen
- ✅ KVK als trusted issuer voor alle company credentials
- ✅ Volledige SSI ecosystem voor bedrijven

---

### 6.6 Samenvatting: Wat Kan Nu, Wat Vereist Wetgeving?

| Aspect | Huidig Juridisch Kader | Vereiste Wijziging | Tijdlijn |
|--------|------------------------|-------------------|----------|
| **VC's accepteren** | ✅ Mogelijk (eIDAS 2.0 directe werking) | Geen - technische implementatie alleen | **Nu mogelijk** |
| **EUDI Wallet gebruiken** | ✅ Verplicht tegen 2026 (eIDAS 2.0) | Geen - EU-verordening | **2026 beschikbaar** |
| **VC verificatie in RegelRecht** | ✅ Mogelijk (geen wettelijke barrier) | Geen | **Nu mogelijk** |
| **KVK VCs uitgeven** | ⚠️ Onduidelijk - impliciete bevoegdheid | Ministeriële regeling + QTSP status | **2026-2027** |
| **Andere issuers (Belastingdienst, RVO)** | ⚠️ Per issuer te bepalen | Per issuer: bevoegdheid + QTSP status | **2026-2028** |
| **DID naast BSN** | ✅ Mogelijk (DID = auth, BSN = ID) | Geen | **Nu mogelijk** |
| **DID vervangt BSN** | ❌ Niet mogelijk | Wabb wijzigen + sectorale wetten | **2030+** |
| **Blockchain voor revocation** | ✅ Mogelijk (geen barrier) | Geen | **Nu mogelijk** |
| **Zero-knowledge proofs** | ✅ Mogelijk | Geen - wel DPIA (AVG) | **Nu mogelijk** |
| **Cross-border VCs accepteren** | ✅ Mogelijk (eIDAS 2.0) | Geen | **2026+** |

---

### 6.7 Aanbevelingen en Roadmap

#### Fase 1: Foundation (2025 Q2-Q4) - **GEEN WETGEVING NODIG**

**Doel:** RegelRecht VC-ready maken

**Acties:**
1. Implement W3C VC verification in RegelRecht
   - did-resolver library integratie
   - VC-JWT of VC-LD-Proof verification
   - Schema validation (credential types)

2. Hybrid authenticatie architecture
   - DigiD blijft primary (BSN-based)
   - VC-based authorization als optionele addon
   - Test met self-issued VCs (voor development)

3. Documentatie en standaarden
   - NL Credential Profiles definiëren (welke attributen?)
   - Schema's voor company credentials (KVK)
   - Schema's voor citizen credentials (government)

**Juridisch:**
- ✅ Geen wetgeving nodig
- DPIA opstellen voor VC processing
- Privacy by design in architecture

**Output:**
- RegelRecht kan VCs verifiëren
- Reference implementation voor anderen
- Proof of concept met test credentials

---

#### Fase 2: Pilot Partnerships (2026 Q1-Q3) - **MINISTERIËLE REGELING**

**Doel:** Eerste echte VCs van KVK

**Acties:**
1. Partner met KVK voor pilot
   - 10-20 vrijwillige bedrijven
   - 1 credential type: "Company Officer Authorization"
   - Limited scope: alleen RVO WPM rapportage

2. KVK wordt QTSP (Qualified Trust Service Provider)
   - Aanvraag bij Agentschap Telecom
   - eIDAS 2.0 compliance audit
   - Signing infrastructure voor VCs

3. Integratie met EUDI Wallet
   - NL wallet implementatie (DigiD/Mijn Overheid?)
   - VC storage in wallet
   - QR-code based presentation

**Juridisch:**
- ⚠️ **Ministeriële regeling nodig:** Regeling handelsregister 2009 aanpassen
- Lobby/samenwerking met Ministerie EZK (verantwoordelijk voor KVK)
- Legal opinion: past pilot binnen huidige Handelsregisterwet?

**Output:**
- 10-20 bedrijven met KVK-issued VCs
- RegelRecht accepteert deze VCs voor WPM rapportage
- Lessons learned voor scaling

---

#### Fase 3: Expansion (2026 Q4 - 2027) - **MEER ISSUERS**

**Doel:** Meerdere credential types en issuers

**Acties:**
1. Uitbreiding KVK credentials
   - UBO (Ultimate Beneficial Owner) credentials
   - Company registration credentials
   - Historical data credentials (oprichtingsdatum, etc.)

2. Andere issuers onboarden
   - RVO: Subsidie entitlement credentials
   - Belastingdienst: Tax representative credentials
   - Gemeenten: Bijstand authorization credentials

3. Cross-law gebruik
   - VC van KVK gebruiken voor zorgtoeslag (ondernemerschap check)
   - VC van gemeente gebruiken voor andere toeslagen
   - VC van Belastingdienst voor inkomensafhankelijke regelingen

**Juridisch:**
- ⚠️ Per issuer: bevoegdheid checken en evt. ministeriële regeling
- Coördinatie via Forum Standaardisatie (pas-toe-of-leg-uit)
- Juridische handboeken voor government issuers

**Output:**
- 5+ credential types beschikbaar
- 3+ government issuers
- Meerdere laws in RegelRecht gebruiken VCs

---

#### Fase 4: Scaling (2028-2029) - **WETSWIJZIGING OPTIONEEL**

**Doel:** Mainstream adoption

**Acties:**
1. KVK VCs voor ALLE bedrijven
   - Automatische VC issuance bij inschrijving
   - Self-service VC refresh via MijnKVK
   - Revocation bij uitschrijving/wijziging

2. Citizen credentials
   - BRP credentials (adres, leeftijd, etc.)
   - Diploma credentials (DUO)
   - Healthcare credentials (zorgverzekeraar)

3. Private sector adoption
   - Banken accepteren government VCs voor KYC
   - Werkgevers accepteren diploma VCs
   - Verzekeraars accepteren healthcare VCs

**Juridisch:**
- ⚠️ **Optioneel:** Handelsregisterwet expliciet wijzigen voor VCs
- Niet strikt nodig (ministeriële regeling voldoet)
- Maar: verstevigt juridische basis

**Output:**
- Miljoen+ VCs in circulatie
- Mainstream adoption door burgers en bedrijven
- RegelRecht als reference implementation

---

#### Fase 5: Full SSI (2030+) - **GROTE WETSOPERATIE**

**Doel:** BSN vervangen door DID

**Acties:**
1. DID als primary identifier
   - Wabb wijzigen: DID gelijkwaardig aan BSN
   - BRP registreert DIDs
   - Alle sectorale wetten: BSN → DID

2. Volledige decentralisatie
   - Geen centrale identity database meer
   - Blockchain-based DID registry
   - User-controlled wallet als single source of truth

**Juridisch:**
- ❌ **Grote wetsoperatie nodig:**
  - Wabb volledig herzien
  - Tientallen sectorale wetten aanpassen
  - Politieke wil en maatschappelijk debat

**Realiteit:**
- Dit is een **10+ jaar visie**
- Enorm complex
- Waarschijnlijk geleidelijke transitie (DID naast BSN voor decennia)

**Output:**
- Volledige SSI ecosystem
- Europese interoperabiliteit
- Privacy by design in overheid

---

### 6.8 Kritische Succesfactoren

Voor succesvol realiseren van SSI in RegelRecht:

1. **Partnership met KVK** ⭐⭐⭐
   - Zonder KVK als eerste issuer: geen business credentials
   - Vroeg betrekken in pilot fase
   - Co-development van standards

2. **EU Wallet Alignment** ⭐⭐⭐
   - Wacht niet op NL wallet - werk samen met implementatie
   - Zorg dat RegelRecht compatibel is met EUDI wallet specs
   - Participate in EU Large Scale Pilots

3. **Juridische Clarity** ⭐⭐
   - Krijg legal opinions early
   - Work met ministerie EZK (KVK) en BZK (DigiD/BSN)
   - Zorg voor expliciete bevoegdheid (ministeriële regeling minimum)

4. **Technical Standards** ⭐⭐
   - Don't invent proprietary formats
   - Use W3C specs (DID Core, VC Data Model, VC-JWT)
   - Contribute to Dutch profiles (Forum Standaardisatie)

5. **Privacy by Design** ⭐⭐
   - DPIA vanaf dag 1
   - Selective disclosure als default
   - Clear user consent flows

6. **Developer Experience** ⭐
   - Open source libraries
   - Good documentation
   - Low barrier to entry voor developers

7. **Political Support** ⭐
   - Lobby voor SSI bij TK/EK
   - Show benefits (privacy, cost reduction, user control)
   - European examples (Estonia, Belgium)

---

### 6.9 Risico's en Mitigaties

| Risico | Impact | Probability | Mitigatie |
|--------|--------|------------|-----------|
| **KVK weigert VCs uit te geven** | Hoog | Middel | Start met ander issuer (gemeente, RVO), toon success |
| **EUDI Wallet vertraagt** | Middel | Laag | Support ook andere wallets (IRMA, Yivi, private) |
| **Juridische challenge tegen VCs** | Hoog | Laag | Get legal opinions, start met pilot (lager risico) |
| **Privacy concerns (AVG violation)** | Hoog | Middel | DPIA, privacy by design, transparantie |
| **Technical complexity** | Middel | Middel | Use proven libraries, don't reinvent wheel |
| **Low adoption (niemand gebruikt)** | Hoog | Middel | Strong UX, show clear benefits, make optional |
| **Vendor lock-in (proprietary wallets)** | Middel | Middel | Open standards only, multiple wallet support |
| **Cross-border friction** | Laag | Hoog | eIDAS 2.0 zorgt voor interoperabiliteit |

---

### 6.10 Conclusie: Juridische Haalbaarheid

**Is SSI juridisch mogelijk in Nederland? JA, maar gefaseerd:**

✅ **Nu mogelijk (2025):**
- VC verificatie in RegelRecht implementeren
- Test credentials gebruiken voor development
- Architectuur voorbereiden

✅ **2026-2027 mogelijk:**
- KVK VCs uitgeven (met ministeriële regeling)
- EUDI Wallet gebruiken
- Pilot met 10-20 bedrijven

⚠️ **2028-2030 mogelijk:**
- Mainstream adoption
- Meerdere issuers
- Cross-law gebruik

❌ **Voor 2030 NIET mogelijk:**
- BSN volledig vervangen door DID
- Volledige decentralisatie
- Geen centrale identity registers meer

**Grootste juridische blocker:**
- Niet eIDAS 2.0 (die is er al!)
- Niet GDPR (die is compatibel)
- Wel: **Nederlandse wetgeving (Wabb, Handelsregisterwet)**
  - Dit vereist nationale politieke wil
  - Geleidelijke transitie is realistischer dan "big bang"

**Beste strategie voor RegelRecht:**
1. Start met VC verification (nu)
2. Pilot met KVK credentials (2026)
3. Expand naar meer issuers (2027-2028)
4. DID naast BSN (hybrid, 2028+)
5. Lobby voor DID → BSN vervanging (2030+)

**Bottom line:**
SSI is juridisch haalbaar en door EU verplicht tegen 2026. De grootste challenge is niet juridisch, maar **organisatorisch en politiek**: Nederlandse overheid moet willen, investeren, en samenwerken. RegelRecht kan als katalysator fungeren door te tonen dat het werkt.
