# Legal Basis Identificatie Systeem

## Doel
Dit document beschrijft het formaat voor het `legal_basis` veld dat wordt toegevoegd aan alle YAML-definities om fijnmazige verwijzingen naar wetteksten mogelijk te maken, conform bestaande Nederlandse standaarden zoals Juriconnect BWB.

## Formaat van het `legal_basis` veld

Het `legal_basis` veld is een object met de volgende structuur:

```yaml
legal_basis:
  law: "naam_van_de_wet"
  bwb_id: "BWBR0000000"     # BWB identificatie nummer
  article: "artikelnummer"  # optioneel
  paragraph: "lidnummer"    # optioneel
  sentence: "zinsnummer"    # optioneel
  url: "https://wetten.overheid.nl/..."
  juriconnect: "jci1.3:c:BWBR0000000&artikel=1&lid=1"  # optioneel
  explanation: "Nederlandse uitleg hoe dit YAML-element zich verhoudt tot de wettekst"
```

### Velden:
- **law**: Naam van de wet (verplicht)
- **bwb_id**: BWB identificatienummer van de wet (verplicht indien beschikbaar)
- **article**: Artikelnummer als het van toepassing is
- **paragraph**: Lid- of paragraafnummer binnen het artikel (gebruik "lid" voor lidnummers)
- **sentence**: Zinsnummer binnen het lid/paragraaf voor zeer fijnmazige verwijzing
- **url**: Directe link naar wetten.overheid.nl (verplicht)
- **juriconnect**: Optionele Juriconnect BWB 1.3 verwijzing conform standaard
- **explanation**: Nederlandse uitleg die beschrijft hoe het YAML-element de wettekst operationaliseert (verplicht)

## Aansluiting bij bestaande standaarden

### Juriconnect BWB 1.3
We ondersteunen de Juriconnect BWB 1.3 standaard zoals gebruikt op wetten.overheid.nl:
- Formaat: `jci1.3:c:BWBR{nummer}&{parameters}`
- Parameters: `hoofdstuk`, `paragraaf`, `artikel`, `lid`, `zin`
- Voorbeeld: `jci1.3:c:BWBR0018451&artikel=2&lid=1`

### BWB Identificatie
We gebruiken BWB identificatienummers zoals:
- BWBR0018451 (Zorgtoeslagwet)
- BWBR0008659 (Wet op de huurtoeslag)
- BWBR0001840 (Grondwet)

## Identificatie van tekstelementen

Voor fijnmazige verwijzingen gebruiken we de volgende conventie conform wetten.overheid.nl:
- Artikel: `"2"`, `"2a"`, `"B1"`
- Lid: `"1"`, `"2"`, etc.
- Zin: `"1"`, `"2"`, etc. (genummerd binnen het lid)
- Hoofdstuk: `"I"`, `"II"`, etc.
- Paragraaf: `"1"`, `"2"`, etc.

## URL Structuur

URLs naar wetten.overheid.nl volgen het patroon:
`https://wetten.overheid.nl/BWBR{nummer}/{datum}#{locatie}`

Waar locatie kan zijn:
- `#Paragraaf2_Artikel2` voor artikel 2
- `#Paragraaf2_Artikel2_lid1` voor artikel 2, lid 1
- `#Hoofdstuk1_Artikel1` voor artikel 1 in hoofdstuk 1
- Verfijnde links kunnen gemaakt worden via linkeddata.overheid.nl

## Toepassingsgebieden

Het `legal_basis` veld kan worden toegevoegd aan:
- **Top-level service definition**: Voor de algemene grondslag van de service
- **Parameters**: Voor de wettelijke basis van vereiste parameters
- **Input fields**: Voor de grondslag van benodigde input
- **Output fields**: Voor wat de wet zegt over deze output
- **Sources**: Voor de wettelijke basis van databronnen
- **Definitions**: Voor wettelijke definities en constanten
- **Requirements**: Voor wettelijke voorwaarden
- **Actions**: Voor berekeningsregels en operaties
- **Operations binnen actions**: Voor specifieke berekeningsstappen
- **Conditions binnen actions**: Voor beslisregels en drempelwaarden

### Fijnmazige Action Annotatie

Bij het annoteren van actions moet elke berekeningsstap en beslissing worden voorzien van een legal_basis:

```yaml
actions:
  - output: "hoogte_toeslag"
    operation: IF
    conditions:
      - test:
          operation: GREATER_THAN
          values:
            - "$INKOMEN"
            - "$DREMPELINKOMEN"
          legal_basis:
            law: "Zorgtoeslagwet"
            article: "2"
            paragraph: "2"
            explanation: "Artikel 2 lid 2 bepaalt dat inkomen boven drempelinkomen afbouw veroorzaakt"
        then:
          operation: MULTIPLY
          values:
            - "$AFBOUWPERCENTAGE"
            - operation: SUBTRACT
              values:
                - "$INKOMEN"
                - "$DREMPELINKOMEN"
              legal_basis:
                law: "Zorgtoeslagwet"
                article: "2"
                paragraph: "3"
                explanation: "Artikel 2 lid 3 bepaalt 13,7% afbouw over inkomen boven drempel"
```

## Voorbeeld

```yaml
properties:
  input:
    - name: "LEEFTIJD"
      description: "Leeftijd van de aanvrager"
      type: "number"
      legal_basis:
        law: "Wet op de zorgtoeslag"
        bwb_id: "BWBR0018451"
        article: "2"
        paragraph: "1"
        sentence: "1"
        url: "https://wetten.overheid.nl/BWBR0018451/2025-01-01#Paragraaf2_Artikel2"
        juriconnect: "jci1.3:c:BWBR0018451&artikel=2&lid=1"
        explanation: "Artikel 2 lid 1 vereist dat de aanvrager 18 jaar of ouder is, daarom wordt leeftijd opgevraagd"
```
