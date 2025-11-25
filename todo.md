# TODO

## User interface voor aanvraag en verwerken zaak + inzicht gebruiker

## Admin Scherm voor ambtenaar om status van zaken te zien

## Betalingen uitvoeren

## Notification op de website als er een betaling of berekening is geweest

- PDF's / emails??


## Ingangsdatum vs Aanvraagdatum

De aanvraag datum is niet hetzelfde als de startdatum van de zorgtoeslag. Je mag tot 1 september voor het jaar ervoor toeslag aanvragen (AWIR Art. 15 lid 1).

### Wijzigingen nodig:

1. **Toeslag aggregate** - voeg `ingangsdatum` toe naast `aanvraag_datum`
   - `aanvraag_datum` = wanneer de aanvraag is ingediend (automatisch)
   - `ingangsdatum` = gewenste startdatum toeslag (door aanvrager opgegeven)

2. **Validatie bij aanvraag**:
   - Voldeed aanvrager op `ingangsdatum` aan de voorwaarden?
   - Is `ingangsdatum` binnen de terugwerkende kracht termijn?

3. **Time simulation** - verwerk maanden vanaf `ingangsdatum`, niet `aanvraag_datum`

4. **AWIR YAML** - voeg terugwerkende kracht regels toe

---

## Maandelijkse Granulariteit - Wettelijke Basis

De maandelijkse verwerkingscyclus heeft een wettelijke basis in twee wetten:

### AWIR Artikel 5: Doorwerking wijzigingen
> Wijzigingen in de situatie van een belanghebbende die van belang zijn voor inkomensafhankelijke regelingen en optreden na de eerste dag van de maand, werken door vanaf de eerstvolgende maand.

**Implicatie:** Een wijziging halverwege de maand werkt pas door in de volgende iteratie.

### Wet op de zorgtoeslag Artikel 2: Maandelijkse aanspraak
> De aanspraak op een zorgtoeslag wordt voor iedere kalendermaand afzonderlijk bepaald.

**Implicatie:** De berekening moet per maand worden opgedeeld.

### Samenvatting voor het model

| Wet | Artikel | Focus |
|-----|---------|-------|
| AWIR | Art. 5 | Wanneer wijzigingen effect hebben |
| Wzt | Art. 2 | Hoe de berekening wordt opgedeeld |

Dit bevestigt:
- De maandelijkse loop in de time simulation is correct
- De "wijzigingen" check klopt: een wijziging halverwege de maand werkt pas door in de volgende iteratie

### TODO: Implementatie
- [ ] Maandelijkse trigger logica verplaatsen naar YAML (nu hardcoded in simulator)
- [ ] AWIR Art. 5 toevoegen aan de regelset
- [ ] Wzt Art. 2 toevoegen aan de zorgtoeslag regelset
