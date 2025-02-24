# 🤖 Machine-leesbare Wetgeving
![GitHub License](https://img.shields.io/github/license/minbzk/poc-machine-law)

> Een proof-of-concept voor het omzetten van Nederlandse wetgeving naar machine-leesbare specificaties

## 💡 Motivatie

Veel Nederlandse wetten zijn in essentie mechanische processen. Dit wordt duidelijk uit deze drie voorbeelden:

### 1. AOW-opbouw (Pensioenberekening)

[→ Algemene Ouderdomswet, Artikel 13, lid 1-3](https://wetten.overheid.nl/jci1.3:c:BWBR0002221&hoofdstuk=III&artikel=13)

```
1. De oppbouw van het ouderdomspensioen vindt plaats over een tijdvak van 50 jaren.
2. Voor elk jaar wordt 2 percent van het ouderdomspensioen opgebouwd.
3. Bij een korter tijdvak dan 50 jaren wordt het ouderdomspensioen evenredig verlaagd.
```

**Wat maakt dit mechanisch?**
Dit is een pure rekenkundige formule: `uitkering = basispensioen × (opbouwjaren ÷ 50) × 0.02`. Elke variabele is exact
gedefinieerd en de berekening is deterministisch.

### 2. Huurtoeslag (Inkomensafhankelijke normhuur)

[→ Wet op de Huurtoeslag, Artikel 19, lid 2-3](https://wetten.overheid.nl/jci1.3:c:BWBR0008659&hoofdstuk=3&paragraaf=1&artikel=19)

```
Voor elk rekeninkomen boven het minimum-inkomenspunt geldt de formule:
(a x Y²) + (b x Y)

waarbij:
Y = het rekeninkomen
a, b = factoren per type huishouden, vast te stellen bij ministeriële regeling

De uitkomst wordt naar boven afgerond op hele eurocenten.
```

**Wat maakt dit mechanisch?**
Dit is een pure wiskundige formule met kwadratische en lineaire termen. De wetgever heeft hier expliciet gekozen voor
een algebraïsche notatie - inclusief variabelen, machten en constanten. Dit is één-op-één om te zetten naar code.

### 3. Kostendelersnorm (Bijstandsberekening)

[→ Participatiewet, Artikel 22a, lid 2-3](https://wetten.overheid.nl/jci1.3:c:BWBR0015703&hoofdstuk=3&paragraaf=3.2&artikel=22a)

```
De kostendelersnorm wordt berekend volgens de formule:
(40% + A × 30%) × N
waarbij:
A = aantal kostendelende medebewoners
N = gehuwdennorm genoemd in artikel 21, onderdeel b
```

**Wat maakt dit mechanisch?**
Dit is letterlijk een wiskundige formule met variabelen, constanten en een exacte berekeningswijze. Het is een algoritme
dat direct om te zetten is naar code.

## 🔍 Het Probleem

Deze wetten zijn algoritmes vermomd als tekst. Dit leidt tot drie problemen:

1. 👩‍💻 **Interpretatie door programmeurs** zonder juridische achtergrond.
    - **MERK OP**: wetten in deze PoC zijn _nu_ grotendeels door een programmeur (met behulp van een LLM) omgezet naar
      `machine law`. Uiteindelijk zouden dit soort gegenereerde `machine law` interpretaties het startpunt kunnen zijn
      voor juristen.
2. 🤷 **Gebrek aan transparantie** voor burgers en ambtenaren ("computer says no")
3. ⚠️ **Moeilijke kwaliteitscontrole** van implementaties

## 🔄 Voortbouwen op regels.overheid.nl

Dit experiment bouwt voort op [regels.overheid.nl](https://regels.overheid.nl/). Waar regels.overheid.nl zich vooral
richt
op het documenteren en publiceren van wetten, gaan wij een stap verder:

1. **Executeerbare Code**: regel specificaties zijn niet alleen documentatie, maar daadwerkelijk uitvoerbare code die
   direct door computersystemen verwerkt kan worden
2. **Ingebouwde Engine**: De specificaties komen met een engine die ze kan uitvoeren, valideren en testen
3. **Formele Verificatie**: Door de exacte specificatie kunnen we bewijzen dat implementaties correct zijn en resolven.
4. **Directe Implementatie**: Overheidsorganisaties kunnen (uiteindelijk) de specificaties direct in hun systemen
   gebruiken.

Dit maakt het mogelijk om wetten niet alleen te *beschrijven*, maar ook te *testen* en *valideren* voordat ze in
productie gaan.

## 📚 Geïmplementeerde Wetten

Vooralsnog zijn deze wetten geïmplementeerd in `machine law` (met behulp van een LLM).

### Zorgtoeslag

- [Hoofdwet](law/zorgtoeslagwet/TOESLAGEN-2025-01-01.yaml) - Berekening zorgtoeslag
- [Verzekeringsstatus](law/zvw/RVZ-2024-01-01.yaml) - Bepaling verzekeringsstatus

### AOW

- [Hoofdwet](law/algemene_ouderdomswet/SVB-2024-01-01.yaml) - Berekening AOW-uitkering
- [Leeftijdsbepaling](law/algemene_ouderdomswet/leeftijdsbepaling/SVB-2024-01-01.yaml) - Bepaling AOW-leeftijd

### Huurtoeslag

- [Hoofdwet](law/wet_op_de_huurtoeslag/TOESLAGEN-2025-01-01.yaml) - Berekening huurtoeslag

### Participatiewet (Bijstand)

- [Landelijke regels](law/participatiewet/bijstand/SZW-2023-01-01.yaml) - Beoordeling bijstandsrecht (SZW)
- [Gemeente Amsterdam](law/participatiewet/bijstand/gemeenten/GEMEENTE_AMSTERDAM-2023-01-01.yaml) - Lokale bijstandsregels

### Bestuursrecht (AWB)

- [Bezwaarprocedure](law/awb/bezwaar/JenV-2024-01-01.yaml) - Regels voor bezwaar
- [Beroepsprocedure](law/awb/beroep/JenV-2024-01-01.yaml) - Regels voor beroep

### Kieswet

- [Hoofdwet](law/kieswet/KIESRAAD-2024-01-01.yaml) - Bepaling kiesrecht

### Overige Wetten

- [Handelsregisterwet](law/handelsregisterwet/KVK-2024-01-01.yaml) - KVK-registratie
- [Vreemdelingenwet](law/vreemdelingenwet/IND-2024-01-01.yaml) - Verblijfsvergunningen
- [Penitentiaire Beginselenwet](law/penitentiaire_beginselenwet/DJI-2022-01-01.yaml) - Detentieregels
- [Wet Forensische Zorg](law/wet_forensische_zorg/DJI-2022-01-01.yaml) - Forensische zorg
- [Wet Studiefinanciering](law/wet_studiefinanciering/DUO-2024-01-01.yaml) - Studiefinanciering
- [Wetboek van Strafrecht](law/wetboek_van_strafrecht/JUSTID-2023-01-01.yaml) - Strafbepalingen

### Ondersteunende Wetten

- [Wet BRP](law/wet_brp/RvIG-2020-01-01.yaml) - Persoonsgegevens
- [Wet Inkomstenbelasting](law/wet_inkomstenbelasting/UWV-2020-01-01.yaml) - Toetsingsinkomen
- [SUWI](law/wet_structuur_uitvoeringsorganisatie_werk_en_inkomen/UWV-2024-01-01.yaml) - Verzekerde jaren
- [CBS](law/wet_op_het_centraal_bureau_voor_de_statistiek/CBS-2024-01-01.yaml) - Levensverwachting

## 🚀 Aan de slag

Installeer eerst [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation), installeer dan dependencies:
```bash
git clone git@github.com:MinBZK/poc-machine-law.git
cd poc-machine-law
uv sync
```

Run features:
```bash
uv run behave features --no-capture -v --define log_level=DEBUG
```

Run simulaties:
```bash
uv run simulate.py
```

Run de burger interface:
```bash
uv run web/main.py
```

Dit zou een interface hier http://0.0.0.0:8000 en hier http://0.0.0.0:8000/admin op moeten leveren.



## 📂 Repository structuur

- [law](law) - Machine-leesbare wetspecificaties
- [engine.py](machine/engine.py) - De wetgevingsengine die specificaties uitvoert

## 🛣️ Roadmap

In willekeurige volgorde:

- ~~📅 Implementatie van referentiedatums~~
- ~~📚 Toevoegen van meer wetten naast de zorgtoeslagwet~~
- ~~⚖️ Onderzoeken hoe algemene wetten (zoals bezwaarrecht) hierin passen~~
- ~~👥 Verbeteren van uitlegbaarheid naar burgers~~
- 🙋 Hardheid-by-design
- 🔧 Ontwikkelen van tools om wetten om te zetten
- 🔍 Detectie van deadlocks/loops in wetgeving

## 🤝 Bijdragen

Bijdragen zijn welkom! Zie de [issues](https://github.com/MinBZK/poc-machine-law/issues) voor openstaande punten.
