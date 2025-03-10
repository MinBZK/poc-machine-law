Zorgtoeslag \
Gegenereerd op basis van zorgtoeslagwet \
**Geldig vanaf**: 2024-01-01 \
**Omschrijving**: Berekeningsregels voor het bepalen van het recht op en de hoogte van de zorgtoeslag volgens artikel 2 van de Wet op de zorgtoeslag, geldend voor het jaar 2024.


Objecttype: Natuurlijk persoon
- Leeftijd van de aanvrager <span style="color:green">Age</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Partnerschap status <span style="color:green">Has partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Verzekeringsstatus <span style="color:green">Has insurance</span> uit het <span style="color:yellow"> RVZ </span> op basis van <span style="color:pink"> zvw </span>
- Verdragsverzekering status <span style="color:green">Has act insurance</span> uit het <span style="color:yellow"> RVZ </span> op basis van <span style="color:pink"> zvw </span>
- Detentiestatus <span style="color:green">Is incarcerated</span> uit het <span style="color:yellow"> DJI </span> op basis van <span style="color:pink"> penitentiaire_beginselenwet </span>
- Forensische status <span style="color:green">Is forensic</span> uit het <span style="color:yellow"> DJI </span> op basis van <span style="color:pink"> wet_forensische_zorg </span>
- Toetsingsinkomen <span style="color:green">Income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Vermogen <span style="color:green">Net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Gezamenlijk vermogen <span style="color:green">Combined net worth</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Partnerinkomen <span style="color:green">Partner income</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- <span style="color:green">Is verzekerde zorgtoeslag</span> boolean
- <span style="color:green">Hoogte toeslag</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">AFBOUWPERCENTAGE_BOVEN_DREMPEL</span> : 0.0387
- Parameter <span style="color:blue">AFBOUWPERCENTAGE_MINIMUM</span> : 0.1367
- Parameter <span style="color:blue">DREMPELINKOMEN_ALLEENSTAANDE</span> : 3749600
- Parameter <span style="color:blue">DREMPELINKOMEN_TOESLAGPARTNER</span> : 4821800
- Parameter <span style="color:blue">MINIMUM_AGE</span> : 18
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND</span> : 0.0486
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_MET_PARTNER</span> : 0.0486
- Parameter <span style="color:blue">STANDAARDPREMIE_2024</span> : 182100
- Parameter <span style="color:blue">VERMOGENSGRENS_ALLEENSTAANDE</span> : 14193900
- Parameter <span style="color:blue">VERMOGENSGRENS_TOESLAGPARTNER</span> : 17942900


Regel bepaal/bereken is verzekerde zorgtoeslag \
Geldig vanaf: 2024-01-01

De <span style="color: green">is_verzekerde_zorgtoeslag</span> is
<span style="color:green">true</span>


Regel bepaal/bereken hoogte toeslag \
Geldig vanaf: 2024-01-01

De <span style="color: green">hoogte_toeslag</span> is

  - Indien <span style="color:green">$HAS_PARTNER</span> gelijk aan <span style="color:green">false</span>


    dan
    - Indien <span style="color:green">$INCOME</span> groter dan <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>


      dan <span style="color:green">0</span>


    - Indien <span style="color:green">$NET_WORTH</span> groter dan <span style="color:blue">$VERMOGENSGRENS_ALLEENSTAANDE</span>


      dan <span style="color:green">0</span>


    - Anders <span style="color:blue">$STANDAARDPREMIE_2024</span> min <span style="color:blue">$PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND</span> keer <span style="color:green">$INCOME</span> minimaal <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>



     plus
      - Indien <span style="color:green">$INCOME</span> groter dan <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>


        dan <span style="color:green">$INCOME</span> min <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>

       keer <span style="color:blue">$AFBOUWPERCENTAGE_MINIMUM</span>



      - Anders <span style="color:green">0</span>










  - Indien <span style="color:green">$HAS_PARTNER</span> gelijk aan <span style="color:green">true</span>


    dan
    - Indien <span style="color:green">$INCOME</span> plus <span style="color:green">$PARTNER_INCOME</span>

     groter dan <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>


      dan <span style="color:green">0</span>


    - Indien <span style="color:green">$COMBINED_NET_WORTH</span> groter dan <span style="color:blue">$VERMOGENSGRENS_TOESLAGPARTNER</span>


      dan <span style="color:green">0</span>


    - Anders <span style="color:blue">$STANDAARDPREMIE_2024</span> keer <span style="color:green">2</span>

     min <span style="color:blue">$PERCENTAGE_DREMPELINKOMEN_MET_PARTNER</span> keer <span style="color:green">$INCOME</span> plus <span style="color:green">$PARTNER_INCOME</span>

     minimaal <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>



     plus
      - Indien <span style="color:green">$INCOME</span> plus <span style="color:green">$PARTNER_INCOME</span>

       groter dan <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>


        dan <span style="color:green">$INCOME</span> plus <span style="color:green">$PARTNER_INCOME</span>

       min <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>

       keer <span style="color:blue">$AFBOUWPERCENTAGE_BOVEN_DREMPEL</span>



      - Anders <span style="color:green">0</span>
