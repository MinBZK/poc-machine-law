Bepalen verzekerde zorgtoeslag 2025 \
Gegenereerd op basis van zorgtoeslagwet \
**Geldig vanaf**: 2025-01-01 \
**Omschrijving**: Berekeningsregels voor het bepalen van het recht op en de hoogte van de zorgtoeslag volgens artikel 2 van de Wet op de zorgtoeslag, geldend voor het jaar 2025. Dit jaar wordt de studiefinanciering meegenomen als inkomen (studiefinanciering is een gift geworden).


Objecttype: Natuurlijk persoon
- Leeftijd van de aanvrager <span style="color:green">Age</span> uit het <span style="color:yellow"> BRP </span> op basis van <span style="color:pink"> wet_brp </span>
- Partnerschap status <span style="color:green">Has partner</span> uit het <span style="color:yellow"> BRP </span> op basis van <span style="color:pink"> wet_brp </span>
- Verzekeringsstatus <span style="color:green">Has insurance</span> uit het <span style="color:yellow"> RVZ </span> op basis van <span style="color:pink"> zvw </span>
- Verdragsverzekering status <span style="color:green">Has act insurance</span> uit het <span style="color:yellow"> RVZ </span> op basis van <span style="color:pink"> zvw </span>
- Detentiestatus <span style="color:green">Is incarcerated</span> uit het <span style="color:yellow"> DJI </span> op basis van <span style="color:pink"> penitentiaire_beginselenwet </span>
- Forensische status <span style="color:green">Is forensic</span> uit het <span style="color:yellow"> DJI </span> op basis van <span style="color:pink"> wet_forensische_zorg </span>
- Toetsingsinkomen <span style="color:green">Income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Studiefinanciering <span style="color:green">Study grant</span> uit het <span style="color:yellow"> DUO </span> op basis van <span style="color:pink"> wet_studiefinanciering </span>
- Vermogen <span style="color:green">Net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Gezamenlijk vermogen <span style="color:green">Combined net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Partnerinkomen <span style="color:green">Partner income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Partner studiefinanciering <span style="color:green">Partner study grant</span> uit het <span style="color:yellow"> DUO </span> op basis van <span style="color:pink"> wet_studiefinanciering </span>
- <span style="color:green">Is verzekerde zorgtoeslag</span> boolean
- <span style="color:green">Hoogte toeslag</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">AFBOUWPERCENTAGE_BOVEN_DREMPEL</span> : 0.1367
- Parameter <span style="color:blue">DREMPELINKOMEN_ALLEENSTAANDE</span> : 3749600
- Parameter <span style="color:blue">DREMPELINKOMEN_TOESLAGPARTNER</span> : 4821800
- Parameter <span style="color:blue">MINIMUM_AGE</span> : 18
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND</span> : 0.01879
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_MET_PARTNER</span> : 0.04256
- Parameter <span style="color:blue">STANDAARDPREMIE_2025</span> : 182100
- Parameter <span style="color:blue">VERMOGENSGRENS_ALLEENSTAANDE</span> : 14193900
- Parameter <span style="color:blue">VERMOGENSGRENS_TOESLAGPARTNER</span> : 17942900


Regel bepaal/bereken is verzekerde zorgtoeslag \
Geldig vanaf: 2025-01-01

Een <span style="color:purple">Natuurlijk persoon</span> <span style="color:green">is_verzekerde_zorgtoeslag</span>
Indien hij aan de volgende voorwaarden voldoet:
- Hij voldoet aan ten minste een van de volgende voorwaarden:
  - Indien <span style="color:green">$HAS_INSURANCE</span> waar is
  - Indien <span style="color:green">$HAS_ACT_INSURANCE</span> waar is
- Zijn <span style="color:green">$AGE</span> is groter of gelijk aan <span style="color:blue">$MINIMUM_AGE</span>
- Indien <span style="color:green">$IS_INCARCERATED</span> onwaar is
- Indien <span style="color:green">$IS_FORENSIC</span> onwaar is

Regel bepaal/bereken hoogte toeslag \
Geldig vanaf: 2025-01-01

De <span style="color: green">hoogte_toeslag</span> is
