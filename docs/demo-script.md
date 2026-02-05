# Demo Script: RegelRecht + Zorgtoeslagworkflow Hackathon

## Setup (vooraf)

### 1. Worktree aanmaken (eenmalig)
```bash
cd poc-machine-law
git worktree add .worktrees/zorgtoeslagworkflow zorgtoeslagworkflow
```

### 2. Twee servers starten
```bash
# Terminal 1 - Main branch (poort 8000) - voor presentatie & burger portal
cd poc-machine-law
uv run web/main.py

# Terminal 2 - Workflow branch (poort 8001) - voor hackathon features
cd poc-machine-law/.worktrees/zorgtoeslagworkflow
uv run web/main.py --port 8001
```

### 3. Browser tabs openen
- Tab 1: `http://localhost:8000/demo/workspace`
- Tab 2: `http://localhost:8001/demo/workspace`

---

## Demo Flow

### Deel 1: Introductie (main branch - poort 8000)

**URL:** `http://localhost:8000/demo/workspace`

| Slide | Inhoud | Talking points |
|-------|--------|----------------|
| 1 | Titel: "RegelRecht" | - Van wet naar digitale werking |
| 2 | "De huidige situatie" | - Huidige problemen met regelgeving |
| 3 | "Wat als..." | - Visie op geautomatiseerde regeltoepassing |
| 4 | "Demo RegelRecht" | - Overgang naar live demo |

**Navigatie:** Pijltjestoetsen of spatiebalk

---

### Deel 2: Wet als code (main branch - poort 8000)

**Tab:** Wetten

1. Klik op **"Wetten"** tab
2. Selecteer **zorgtoeslagwet** uit de lijst
3. Toon de YAML structuur:
   - Parameters (toetsingsinkomen, vermogen)
   - Beslisregels (draagkracht, recht op toeslag)
   - Berekeningen (standaardpremie, toeslag)

**Key points:**
- "Dit is de wet, leesbaar voor zowel mens als machine"
- "Elke regel verwijst naar de bron in de wet"

---

### Deel 3: Burger aanvraag (main branch - poort 8000)

**Tab:** Burger.nl

1. Klik op **"Burger.nl"** tab
2. Selecteer **Zorgtoeslag** aanvraag
3. Vul voorbeeldgegevens in:
   - Inkomen: € 25.000
   - Vermogen: € 10.000
   - Toeslagpartner: Nee
4. Verstuur aanvraag
5. Toon het resultaat met uitleg

**Key points:**
- "De burger voert gegevens in"
- "Direct inzicht in de berekening"
- "Transparante besluitvorming"

---

### Deel 4: Hackathon - Zaaksysteem (workflow branch - poort 8001)

**URL:** `http://localhost:8001/demo/workspace`
**Tab:** Zaaksysteem

1. Klik op **"Zaaksysteem"** tab
2. Toon het overzicht van zaken
3. Klik op een zaak om details te zien

**Key points:**
- "De hackathon: wat gebeurt er NA de aanvraag?"
- "Complete case lifecycle"
- "Event-driven architectuur"

---

### Deel 5: Tijdlijn & Simulatie (workflow branch - poort 8001)

**URL:** `http://localhost:8001/zaken/tijdlijn`

1. Toon de tijdlijn view
2. Gebruik "Volgende dag" knop om tijd te simuleren
3. Toon status transities:
   - AANVRAAG INGEDIEND → BEREKEND → VOORSCHOT → LOPEND

**Wat je ziet:**
- Dag-voor-dag verwerking
- Automatische status updates
- Timeline events met badges

---

### Deel 6: Berichten systeem (workflow branch - poort 8001)

**URL:** `http://localhost:8001/berichten`

1. Toon de berichten inbox
2. Klik op een bericht (beschikking)
3. Toon de inhoud van de beschikking

**Key points:**
- "Automatisch gegenereerde berichten"
- "Burger krijgt notificatie bij belangrijke momenten"
- "Beschikkingen met volledige onderbouwing"

---

### Deel 7: AWIR Jaar-einde (optioneel)

Als je tijd hebt, toon de jaar-einde workflow:

1. Simuleer meerdere maanden vooruit
2. Toon IB-aanslag verwerking
3. Definitieve beschikking & vereffening

---

## Tips voor de demo

### Vooraf checken
- [ ] Beide servers draaien
- [ ] Geen foutmeldingen in terminal
- [ ] Testdata is reset (indien nodig)

### Reset tussen demos
```bash
# In workflow branch terminal, herstart server:
Ctrl+C
uv run web/main.py --port 8001
```

### Backup plan
Als iets niet werkt, schakel naar de **Scenarios** tab en run de BDD tests:
```bash
uv run behave features/zorgtoeslag.feature -v
```

---

## Belangrijke URLs samenvatting

| Functie | URL |
|---------|-----|
| Demo workspace (main) | http://localhost:8000/demo/workspace |
| Demo workspace (workflow) | http://localhost:8001/demo/workspace |
| Zaken overzicht | http://localhost:8001/zaken |
| Tijdlijn | http://localhost:8001/zaken/tijdlijn |
| Berichten | http://localhost:8001/berichten |
| Admin dashboard | http://localhost:8001/admin |
