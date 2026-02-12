# Demo Test: Huurtoeslag Afwijzing en Bezwaar

Dit document beschrijft de Playwright MCP test voor de huurtoeslag afwijzing en bezwaar flow.

## Vereisten

- Server draait op `http://localhost:8000`
- Playwright MCP is geconfigureerd

## Test Flow

### Stap 1: Navigeer naar burger pagina

```
browser_navigate: http://localhost:8000/?bsn=100000001
```

### Stap 2: Open Huurtoeslag aanvraag

Klik op "Huurtoeslag aanvragen" knop in de Huurtoeslag tile.

### Stap 3: Vul huurtoeslag gegevens in

Gebruik `browser_fill_form` met de volgende velden:

| Veld | Type | Waarde |
|------|------|--------|
| rekening_huur | textbox | 720 |
| rekening_servicekosten | textbox | 48 |

### Stap 4: Dien aanvraag in

Klik op "Aanvraag indienen" knop en bevestig in de dialog.

### Stap 5: Ga naar zaaksysteem

```
browser_navigate: http://localhost:8000/demo/#zaaksysteem
```

### Stap 6: Wijs de huurtoeslag aanvraag af

1. Zoek de huurtoeslag case in de lijst (status: BEREKEND)
2. Klik op "Wijs af" knop
3. Vul reden in: "Inkomen te hoog voor huurtoeslag"
4. Bevestig de afwijzing

### Stap 7: Verifieer in admin dashboard

```
browser_navigate: http://localhost:8000/demo/#admin
```

Controleer dat de case status "AFGEWEZEN" is.

### Stap 8: Ga naar burger view

```
browser_navigate: http://localhost:8000/?bsn=100000001
```

### Stap 9: Verifieer bezwaar knop

De Huurtoeslag tile moet tonen:
- Status label: "Afgewezen"
- Tekst: "Aanvraag afgewezen - U heeft geen recht op deze toeslag."
- Sectie: "Mogelijkheid tot bezwaar"
- Knop: "Ga in bezwaar"

### Stap 10: Dien bezwaar in

1. Klik op "Ga in bezwaar" knop
2. Vul reden in: "Ik ben het niet eens met de afwijzing. Mijn inkomen is lager dan de grens voor huurtoeslag."
3. Klik op "Bevestigen"

### Stap 11: Verifieer resultaat

De Huurtoeslag tile moet nu tonen:
- Status label: "In bezwaar gegaan"

## Verwachte uitkomst

- Case doorloopt statussen: BEREKEND -> AFGEWEZEN -> OBJECTED
- Burger ziet bezwaar mogelijkheid bij afgewezen aanvraag
- Na bezwaar wordt status bijgewerkt naar "In bezwaar gegaan"
- Er wordt een bericht aangemaakt (zichtbaar in "Berichten" tab)

## Gerelateerde bestanden

- `web/templates/partials/tiles/base_tile.html` - Bezwaar knop template
- `machine/events/case/aggregate.py` - Case status transitions
- `laws/awir/berichten/TOESLAGEN-2025-01-01.yaml` - Bericht triggers
