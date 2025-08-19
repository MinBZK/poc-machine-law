Zorgtoeslag \
Gegenereerd op basis van zorgtoeslagwet \
**Geldig vanaf**: 2025-01-01 \
**Omschrijving**: Berekeningsregels voor het bepalen van het recht op en de hoogte van de zorgtoeslag volgens artikel 2 van de Wet op de zorgtoeslag, geldend voor het jaar 2025.


Objecttype: Natuurlijk persoon
- Leeftijd van de aanvrager <span style="color:green">Leeftijd</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Aanvrager is verzekerde in de zin van de zvw <span style="color:green">Is verzekerde</span> uit het <span style="color:yellow"> RVZ </span> op basis van <span style="color:pink"> zvw </span>
- Toetsingsinkomen <span style="color:green">Inkomen</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Vermogen <span style="color:green">Vermogen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Gezamenlijk vermogen <span style="color:green">Gezamenlijk vermogen</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Partnerinkomen <span style="color:green">Partner inkomen</span> uit het <span style="color:yellow"> UWV </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- Partnerschap status <span style="color:green">Heeft partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Standaardpremie <span style="color:green">Standaardpremie</span> uit het <span style="color:yellow"> VWS </span> op basis van <span style="color:pink"> zorgtoeslagwet/regelingen/regeling_vaststelling_standaardpremie_en_bestuursrechtelijke_premies </span>
- <span style="color:green">Is verzekerde zorgtoeslag</span> boolean
- <span style="color:green">Hoogte toeslag</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">AFBOUWPERCENTAGE_BOVEN_DREMPEL</span> : 0.137
- Parameter <span style="color:blue">AFBOUWPERCENTAGE_MINIMUM</span> : 0.137
- Parameter <span style="color:blue">DREMPELINKOMEN_ALLEENSTAANDE</span> : 3971900
- Parameter <span style="color:blue">DREMPELINKOMEN_TOESLAGPARTNER</span> : 5020600
- Parameter <span style="color:blue">MINIMUM_LEEFTIJD</span> : 18
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND</span> : 0.01896
- Parameter <span style="color:blue">PERCENTAGE_DREMPELINKOMEN_MET_PARTNER</span> : 0.04273
- Parameter <span style="color:blue">VERMOGENSGRENS_ALLEENSTAANDE</span> : 14189600
- Parameter <span style="color:blue">VERMOGENSGRENS_TOESLAGPARTNER</span> : 17942900


Regel bepaal/bereken is verzekerde zorgtoeslag \
Geldig vanaf: 2025-01-01

De <span style="color: green">is_verzekerde_zorgtoeslag</span> is
<span style="color:green">true</span>


Regel bepaal/bereken hoogte toeslag \
Geldig vanaf: 2025-01-01

De <span style="color: green">hoogte_toeslag</span> is

  - Indien <span style="color:green">$HEEFT_PARTNER</span> gelijk aan <span style="color:green">false</span>


    dan
    - Indien <span style="color:green">$INKOMEN</span> groter dan <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>


      dan <span style="color:green">0</span>


    - Indien <span style="color:green">$VERMOGEN</span> groter dan <span style="color:blue">$VERMOGENSGRENS_ALLEENSTAANDE</span>


      dan <span style="color:green">0</span>


    - Anders <span style="color:green">$STANDAARDPREMIE</span> min <span style="color:blue">$PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND</span> keer <span style="color:green">$INKOMEN</span> minimaal <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>



     plus
      - Indien <span style="color:green">$INKOMEN</span> groter dan <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>


        dan <span style="color:green">$INKOMEN</span> min <span style="color:blue">$DREMPELINKOMEN_ALLEENSTAANDE</span>

       keer <span style="color:blue">$AFBOUWPERCENTAGE_MINIMUM</span>



      - Anders <span style="color:green">0</span>










  - Indien <span style="color:green">$HEEFT_PARTNER</span> gelijk aan <span style="color:green">true</span>


    dan
    - Indien <span style="color:green">$INKOMEN</span> plus <span style="color:green">$PARTNER_INKOMEN</span>

     groter dan <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>


      dan <span style="color:green">0</span>


    - Indien <span style="color:green">$GEZAMENLIJK_VERMOGEN</span> groter dan <span style="color:blue">$VERMOGENSGRENS_TOESLAGPARTNER</span>


      dan <span style="color:green">0</span>


    - Anders <span style="color:green">$STANDAARDPREMIE</span> keer <span style="color:green">2</span>

     min <span style="color:blue">$PERCENTAGE_DREMPELINKOMEN_MET_PARTNER</span> keer <span style="color:green">$INKOMEN</span> plus <span style="color:green">$PARTNER_INKOMEN</span>

     minimaal <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>



     plus
      - Indien <span style="color:green">$INKOMEN</span> plus <span style="color:green">$PARTNER_INKOMEN</span>

       groter dan <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>


        dan <span style="color:green">$INKOMEN</span> plus <span style="color:green">$PARTNER_INKOMEN</span>

       min <span style="color:blue">$DREMPELINKOMEN_TOESLAGPARTNER</span>

       keer <span style="color:blue">$AFBOUWPERCENTAGE_BOVEN_DREMPEL</span>



      - Anders <span style="color:green">0</span>
