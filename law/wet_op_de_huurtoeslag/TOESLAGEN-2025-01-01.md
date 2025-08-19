Huurtoeslag \
Gegenereerd op basis van wet_op_de_huurtoeslag \
**Geldig vanaf**: 2025-01-01 \
**Omschrijving**: Regels voor het bepalen van het recht op en de hoogte van de huurtoeslag volgens de Wet op de huurtoeslag en de Algemene wet inkomensafhankelijke regelingen (AWIR), geldend voor het jaar 2025.


Objecttype: Natuurlijk persoon
- Gegevens medebewoners <span style="color:green">Huishoudleden</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Gegevens kinderen <span style="color:green">Kinderen</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- BSN van de partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Woonadres van de partner <span style="color:green">Partner adres</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Leeftijd van de aanvrager <span style="color:green">Leeftijd</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft de persoon een partner <span style="color:green">Heeft partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Aantal personen in huishouden <span style="color:green">Huishoudgrootte</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Woonadres <span style="color:green">Verblijfsadres</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Toetsingsinkomen <span style="color:green">Inkomen</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Toetsingsinkomen partner <span style="color:green">Partner inkomen</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Vermogen <span style="color:green">Vermogen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Gezamenlijk vermogen met partner <span style="color:green">Gezamenlijk vermogen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- <span style="color:green">Is gerechtigd</span> boolean
- <span style="color:green">Basishuur</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Subsidiebedrag</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">AFTOPPINGSGRENS_1_2</span> : 68296
- Parameter <span style="color:blue">AFTOPPINGSGRENS_3_PLUS</span> : 73193
- Parameter <span style="color:blue">INKOMENSGRENS_ALLEENSTAANDE</span> : 4400000
- Parameter <span style="color:blue">INKOMENSGRENS_PARTNERS</span> : 5400000
- Parameter <span style="color:blue">KIND_VRIJSTELLING</span> : 543200
- Parameter <span style="color:blue">KWALITEITSKORTINGSGRENS</span> : 47720
- Parameter <span style="color:blue">LEEFTIJDSGRENS_KIND_INKOMEN</span> : 23
- Parameter <span style="color:blue">MAXIMALE_HUURGRENS</span> : 88571
- Parameter <span style="color:blue">MAXIMALE_SERVICEKOSTEN</span> : 4800
- Parameter <span style="color:blue">MINIMUM_BASISHUUR_PERCENTAGE</span> : 0.0486
- Parameter <span style="color:blue">MINIMUM_LEEFTIJD</span> : 18
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_BOVEN_AFTOP</span> : 0.4
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS</span> : 1
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP</span> : 0.65
- Parameter <span style="color:blue">VERMOGENSGRENS_ALLEENSTAANDE</span> : 3695200
- Parameter <span style="color:blue">VERMOGENSGRENS_PARTNERS</span> : 7390400


Regel bepaal/bereken is gerechtigd \
Geldig vanaf: 2025-01-01

De <span style="color: green">is_gerechtigd</span> is
<span style="color:green">true</span>


Regel bepaal/bereken basishuur \
Geldig vanaf: 2025-01-01

De <span style="color: green">basishuur</span> is
<span style="color:green">$HUURPRIJS</span> plus <span style="color:green">$SERVICEKOSTEN</span>

 min
  - Indien <span style="color:green">$HEEFT_PARTNER</span> gelijk aan <span style="color:green">true</span>


    dan <span style="color:green">$INKOMEN</span> plus <span style="color:green">$PARTNER_INKOMEN</span>



  - Anders <span style="color:green">$INKOMEN</span>


 keer <span style="color:blue">$MINIMUM_BASISHUUR_PERCENTAGE</span>




Regel bepaal/bereken subsidiebedrag \
Geldig vanaf: 2025-01-01

De <span style="color: green">subsidiebedrag</span> is
<span style="color:green">$basishuur</span> minimaal <span style="color:blue">$KWALITEITSKORTINGSGRENS</span>

 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS</span>

 plus  maximaal <span style="color:green">$basishuur</span> minimaal
  - Indien <span style="color:green">$HUISHOUDGROOTTE</span> minder dan of gelijk aan <span style="color:green">2</span>


    dan <span style="color:blue">$AFTOPPINGSGRENS_1_2</span>


  - Anders <span style="color:blue">$AFTOPPINGSGRENS_3_PLUS</span>




 min <span style="color:blue">$KWALITEITSKORTINGSGRENS</span>



 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP</span>

 plus  maximaal <span style="color:green">$basishuur</span> min
  - Indien <span style="color:green">$HUISHOUDGROOTTE</span> minder dan of gelijk aan <span style="color:green">2</span>


    dan <span style="color:blue">$AFTOPPINGSGRENS_1_2</span>


  - Anders <span style="color:blue">$AFTOPPINGSGRENS_3_PLUS</span>






 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_BOVEN_AFTOP</span>
