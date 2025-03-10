Huurtoeslag \
Gegenereerd op basis van wet_op_de_huurtoeslag \
**Geldig vanaf**: 2025-01-01 \
**Omschrijving**: Regels voor het bepalen van het recht op en de hoogte van de huurtoeslag volgens de Wet op de huurtoeslag en de Algemene wet inkomensafhankelijke regelingen (AWIR), geldend voor het jaar 2025.


Objecttype: Natuurlijk persoon
- Gegevens medebewoners <span style="color:green">Household members</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Gegevens kinderen <span style="color:green">Children</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- BSN van de partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Woonadres van de partner <span style="color:green">Partner address</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Leeftijd van de aanvrager <span style="color:green">Age</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft de persoon een partner <span style="color:green">Has partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Aantal personen in huishouden <span style="color:green">Household size</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Woonadres <span style="color:green">Residence address</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Toetsingsinkomen <span style="color:green">Income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Toetsingsinkomen partner <span style="color:green">Partner income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Vermogen <span style="color:green">Net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Gezamenlijk vermogen met partner <span style="color:green">Combined net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- <span style="color:green">Is eligible</span> boolean
- <span style="color:green">Base rent</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Subsidy amount</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">AFTOPPINGSGRENS_1_2</span> : 68296
- Parameter <span style="color:blue">AFTOPPINGSGRENS_3_PLUS</span> : 73193
- Parameter <span style="color:blue">INKOMENSGRENS_ALLEENSTAANDE</span> : 4400000
- Parameter <span style="color:blue">INKOMENSGRENS_PARTNERS</span> : 5400000
- Parameter <span style="color:blue">KIND_VRIJSTELLING</span> : 543200
- Parameter <span style="color:blue">KWALITEITSKORTINGSGRENS</span> : 47720
- Parameter <span style="color:blue">LEEFTIJDSGRENS_KIND_INKOMEN</span> : 23
- Parameter <span style="color:blue">MAXIMALE_HUURGRENS</span> : 88571
- Parameter <span style="color:blue">MAX_SERVICE_COSTS</span> : 4800
- Parameter <span style="color:blue">MINIMUM_AGE</span> : 18
- Parameter <span style="color:blue">MINIMUM_BASISHUUR_PERCENTAGE</span> : 0.0486
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_BOVEN_AFTOP</span> : 0.4
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS</span> : 1
- Parameter <span style="color:blue">SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP</span> : 0.65
- Parameter <span style="color:blue">VERMOGENSGRENS_ALLEENSTAANDE</span> : 3695200
- Parameter <span style="color:blue">VERMOGENSGRENS_PARTNERS</span> : 7390400


Regel bepaal/bereken is eligible \
Geldig vanaf: 2025-01-01

De <span style="color: green">is_eligible</span> is
<span style="color:green">true</span>


Regel bepaal/bereken base rent \
Geldig vanaf: 2025-01-01

De <span style="color: green">base_rent</span> is
<span style="color:green">$RENT_AMOUNT</span> plus <span style="color:green">$SERVICE_COSTS</span>

 min
  - Indien <span style="color:green">$HAS_PARTNER</span> gelijk aan <span style="color:green">true</span>


    dan <span style="color:green">$INCOME</span> plus <span style="color:green">$PARTNER_INCOME</span>



  - Anders <span style="color:green">$INCOME</span>


 keer <span style="color:blue">$MINIMUM_BASISHUUR_PERCENTAGE</span>




Regel bepaal/bereken subsidy amount \
Geldig vanaf: 2025-01-01

De <span style="color: green">subsidy_amount</span> is
<span style="color:green">$base_rent</span> minimaal <span style="color:blue">$KWALITEITSKORTINGSGRENS</span>

 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_ONDER_KWALITEITSKORTINGSGRENS</span>

 plus  maximaal <span style="color:green">$base_rent</span> minimaal
  - Indien <span style="color:green">$HOUSEHOLD_SIZE</span> minder dan of gelijk aan <span style="color:green">2</span>


    dan <span style="color:blue">$AFTOPPINGSGRENS_1_2</span>


  - Anders <span style="color:blue">$AFTOPPINGSGRENS_3_PLUS</span>




 min <span style="color:blue">$KWALITEITSKORTINGSGRENS</span>



 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_TUSSEN_KWALITEIT_AFTOP</span>

 plus  maximaal <span style="color:green">$base_rent</span> min
  - Indien <span style="color:green">$HOUSEHOLD_SIZE</span> minder dan of gelijk aan <span style="color:green">2</span>


    dan <span style="color:blue">$AFTOPPINGSGRENS_1_2</span>


  - Anders <span style="color:blue">$AFTOPPINGSGRENS_3_PLUS</span>






 keer <span style="color:blue">$SUBSIDIEPERCENTAGE_BOVEN_AFTOP</span>
