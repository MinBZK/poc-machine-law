Bepalen kinderopvangtoeslag \
Gegenereerd op basis van wet_kinderopvang \
**Geldig vanaf**: 2024-01-01 \
**Omschrijving**: Regels voor het bepalen van recht op en hoogte van kinderopvangtoeslag volgens de Wet kinderopvang voor het jaar 2025.


Objecttype: Natuurlijk persoon
- Toetsingsinkomen <span style="color:green">Inkomen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- BSN van de partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Toetsingsinkomen partner <span style="color:green">Partner inkomen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- BSNs van de kinderen van de aanvrager <span style="color:green">Kinderen bsns</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Totaal gewerkte uren per jaar <span style="color:green">Gewerkte uren</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_structuur_uitvoeringsorganisatie_werk_en_inkomen </span>
- Totaal gewerkte uren partner per jaar <span style="color:green">Partner gewerkte uren</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_structuur_uitvoeringsorganisatie_werk_en_inkomen </span>
- <span style="color:green">Is gerechtigd</span> boolean
- <span style="color:green">Jaarbedrag</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">INKOMENSDREMPEL_1</span> : 3500000
- Parameter <span style="color:blue">INKOMENSDREMPEL_2</span> : 7000000
- Parameter <span style="color:blue">MAX_HOURS_PER_YEAR</span> : 2760
- Parameter <span style="color:blue">MAX_UURTARIEF_BSO</span> : 766
- Parameter <span style="color:blue">MAX_UURTARIEF_DAGOPVANG</span> : 902
- Parameter <span style="color:blue">MIN_HOURS_PARTNER</span> : 1040
- Parameter <span style="color:blue">MIN_HOURS_PER_WEEK</span> : 20
- Parameter <span style="color:blue">PERCENTAGE_1</span> : 0.96
- Parameter <span style="color:blue">PERCENTAGE_2</span> : 0.8
- Parameter <span style="color:blue">PERCENTAGE_3</span> : 0.33


Regel bepaal/bereken is gerechtigd \
Geldig vanaf: 2024-01-01

De <span style="color: green">is_gerechtigd</span> is
<span style="color:green">true</span>


Regel bepaal/bereken jaarbedrag \
Geldig vanaf: 2024-01-01

De <span style="color: green">jaarbedrag</span> is
voor elke <span style="color:green">[map[legal_basis:map[article:1.6 bwb_id:BWBR0017017 explanation:Artikel 1.6 Wet kinderopvang bepaalt berekening toeslaghoogte per kind juriconnect:jci1.3:c:BWBR0017017&artikel=1.6&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.6] operation:MULTIPLY values:[map[legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 2 Wet kinderopvang bepaalt dat toeslag gebaseerd is op laagste van werkelijk en maximum uurtarief juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=2&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:2 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:MIN values:[map[conditions:[map[test:map[legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 2 Wet kinderopvang bepaalt maximum uurtarief dagopvang juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=2&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:2 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:EQUALS subject:$soort_opvang value:DAGOPVANG] then:$MAX_UURTARIEF_DAGOPVANG] map[else:$MAX_UURTARIEF_BSO]] legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 2 Wet kinderopvang bepaalt maximum uurtarieven per soort opvang juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=2&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:2 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:IF] $uurtarief]] map[legal_basis:map[article:1.9 bwb_id:BWBR0017017 explanation:Artikel 1.9 Wet kinderopvang bepaalt maximum aantal vergoede uren per jaar juriconnect:jci1.3:c:BWBR0017017&artikel=1.9&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.9] operation:MIN values:[$uren_per_jaar $MAX_HOURS_PER_YEAR]] map[conditions:[map[test:map[legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 3 Wet kinderopvang bepaalt vergoedingspercentage bij inkomen tot eerste drempel juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=3&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:3 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:LESS_THAN values:[map[legal_basis:map[article:1.6 bwb_id:BWBR0017017 explanation:Artikel 1.6 lid 2 Wet kinderopvang bepaalt gezamenlijk toetsingsinkomen juriconnect:jci1.3:c:BWBR0017017&artikel=1.6&lid=2&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:2 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.6] operation:ADD values:[$INKOMEN map[conditions:[map[test:map[legal_basis:map[article:3 bwb_id:BWBR0018472 explanation:Artikel 3 AWIR bepaalt wanneer partnerinkomen meetelt voor toeslagen juriconnect:jci1.3:c:BWBR0018472&artikel=3&z=2024-01-01&g=2024-01-01 law:Algemene wet inkomensafhankelijke regelingen url:https://wetten.overheid.nl/BWBR0018472/2024-01-01#Hoofdstuk1_Paragraaf1.2_Artikel3] operation:NOT_NULL subject:$PARTNER_BSN] then:$PARTNER_INKOMEN] map[else:0]] operation:IF]]] $INKOMENSDREMPEL_1]] then:$PERCENTAGE_1] map[test:map[legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 3 Wet kinderopvang bepaalt vergoedingspercentage bij inkomen tot tweede drempel juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=3&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:3 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:LESS_THAN values:[map[legal_basis:map[article:1.6 bwb_id:BWBR0017017 explanation:Artikel 1.6 lid 2 Wet kinderopvang bepaalt gezamenlijk toetsingsinkomen juriconnect:jci1.3:c:BWBR0017017&artikel=1.6&lid=2&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:2 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.6] operation:ADD values:[$INKOMEN map[conditions:[map[test:map[legal_basis:map[article:3 bwb_id:BWBR0018472 explanation:Artikel 3 AWIR bepaalt wanneer partnerinkomen meetelt voor toeslagen juriconnect:jci1.3:c:BWBR0018472&artikel=3&z=2024-01-01&g=2024-01-01 law:Algemene wet inkomensafhankelijke regelingen url:https://wetten.overheid.nl/BWBR0018472/2024-01-01#Hoofdstuk1_Paragraaf1.2_Artikel3] operation:NOT_NULL subject:$PARTNER_BSN] then:$PARTNER_INKOMEN] map[else:0]] operation:IF]]] $INKOMENSDREMPEL_2]] then:$PERCENTAGE_2] map[else:$PERCENTAGE_3]] legal_basis:map[article:1.7 bwb_id:BWBR0017017 explanation:Artikel 1.7 lid 3 Wet kinderopvang bepaalt vergoedingspercentages per inkomenscategorie juriconnect:jci1.3:c:BWBR0017017&artikel=1.7&lid=3&z=2024-12-11&g=2024-12-11 law:Wet kinderopvang paragraph:3 url:https://wetten.overheid.nl/BWBR0017017/2024-12-11#Hoofdstuk1_Afdeling1_Paragraaf4_Artikel1.7] operation:IF]]]]</span>
