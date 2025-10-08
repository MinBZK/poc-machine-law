![GitHub License](https://img.shields.io/github/license/minbzk/poc-machine-law)
![RegelRecht](https://img.shields.io/badge/RegelRecht-PoC-blue)

# RegelRecht PoC
*Van wet naar digitale werking*

> **Note**: Dit project is nu de Proof of Concept voor **RegelRecht**.
> Voorheen bekend als PoC Machine Law, Machine Law, Van wet naar werking, Van wet naar digitale werking, Project Zonder Naam, en Law as Code.

> Een proof-of-concept voor het uitvoeren van machine-leesbare specificaties van Nederlandse wet- en regelgeving.

Deze PoC is onderdeel van het **[RegelRecht Ecosysteem](https://minbzk.github.io/regelrecht/)**.


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

Dit project bouwt voort op [regels.overheid.nl](https://regels.overheid.nl/). Waar regels.overheid.nl zich vooral
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

Clone deze repository inclusief submodules:
```bash
git clone --recurse-submodules git@github.com:MinBZK/poc-machine-law.git
cd poc-machine-law
```

Installeer `uv` volgens de [documentatie](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) of maak gebruik van [asdf](https://asdf-vm.com/) (zodat de juiste versie van `uv` wordt gebruikt):
```bash
asdf install
```

Installeer alle dependencies:
```bash
uv sync
```

Run behavior tests:
```bash
script/test-behaviour
```

Run UI tests
```bash
# Install Playwright
playwright install

# Run tests
script/test-ui
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

### MCP Server (Model Context Protocol)

De applicatie biedt ook een MCP (Model Context Protocol) server die AI agents toegang geeft tot Nederlandse wetgeving:

```bash
# Start de web server (inclusief MCP endpoint)
uv run web/main.py
```

De MCP server is beschikbaar op http://0.0.0.0:8001/mcp/ en ondersteunt:

**🔧 Tools:**
- `execute_law` - Voer een Nederlandse wet uit voor specifieke parameters
- `check_eligibility` - Controleer geschiktheid voor uitkeringen/toeslagen
- `calculate_benefit_amount` - Bereken uitkeringsbedragen

**📚 Resources:**
- `laws://list` - Lijst van alle beschikbare wetten
- `law://{service}/{law}/spec` - Specificatie van een specifieke wet
- `profile://{bsn}` - Burgerprofiel gegevens

**💬 Prompts:**
- `check_all_benefits` - Controleer alle mogelijke uitkeringen
- `explain_calculation` - Leg berekeningen uit
- `compare_scenarios` - Vergelijk verschillende scenario's

**Test de MCP client:**
```bash
uv run python law_mcp/test_client.py
```

De MCP implementatie volgt de 2025-03-26 specificatie en ondersteunt Streamable HTTP transport voor AI agents.

### Go server starten (backend)

De web interface is geconfigureerd om standaard de Go engine te gebruiken (zie `web/config/config.yaml`). Om de Go server te starten:

```bash
cd machinev2/backend
APP_BACKEND_LISTEN_ADDRESS=:8081 APP_INPUT_FILE=../../data/profiles.yaml APP_DEBUG=false go run . serve
```

De Go server is vervolgens beschikbaar op port 8081. Als je de Python engine wilt gebruiken in plaats van de Go engine, pas dan `web/config/config.yaml` aan door de `default: true` regel te verplaatsen naar de Python engine.

### Control Panel

Er is ook een control panel beschikbaar op http://0.0.0.0:8000/admin/control waarmee je de engine kunt configureren en monitoren.

### LLM Providers

De applicatie ondersteunt meerdere LLM providers voor het genereren van uitleg en het beantwoorden van vragen:

1. **Claude (Anthropic)** - Standaard provider
   ```bash
   # Stel Claude in als provider
   export ANTHROPIC_API_KEY=jouw_anthropic_api_key
   export LLM_PROVIDER=claude
   ```

2. **VLAM.ai** - Nederlandse overheids-LLM
   ```bash
   # Stel VLAM.ai in als provider
   export VLAM_API_KEY=jouw_vlam_api_key
   export VLAM_BASE_URL=https://api.demo.vlam.ai/v2.1/projects/poc/openai-compatible/v1
   export VLAM_MODEL_ID=ubiops-deployment/bzk-dig-chat//chat-model
   export LLM_PROVIDER=vlam
   ```

Je kunt ook de provider selecteren in de web-interface, op voorwaarde dat de benodigde API-sleutels zijn ingesteld.

### Feature Flags

De applicatie ondersteunt feature flags om bepaalde functionaliteiten aan of uit te zetten. Feature flags kunnen worden beheerd via het admin control panel op `/admin/control`.

Momenteel ondersteunde feature flags:

- `WALLET` - Bestuurt de NL Wallet integratie
- `CHAT` - Bestuurt de chat interface

Feature flags worden opgeslagen als environment variables met het prefix `FEATURE_`. Bijvoorbeeld, de wallet feature flag wordt opgeslagen als `FEATURE_WALLET`.

Je kunt features in- en uitschakelen via de admin control panel UI of door de environment variables handmatig in te stellen:

```bash
# Wallet feature uitschakelen
export FEATURE_WALLET=0

# Chat feature inschakelen
export FEATURE_CHAT=1
```



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
