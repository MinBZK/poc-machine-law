Bepalen inkomens- en vermogensgegevens \
Gegenereerd op basis van wet_inkomstenbelasting \
**Geldig vanaf**: 2001-01-01 \
**Omschrijving**: Regels voor het bepalen van inkomen en vermogen volgens de Wet inkomstenbelasting 2001. Omvat de drie boxen: werk en woning (box 1), aanmerkelijk belang (box 2), en sparen en beleggen (box 3).


Objecttype: Natuurlijk persoon
- Heeft de persoon een fiscaal partner <span style="color:green">Has partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft de persoon een fiscaal partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- <span style="color:green">Box1 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box2 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box3 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Foreign income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Net worth</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box1 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box2 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box3 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner foreign income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Combined net worth</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Assets</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Business income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Monthly income</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">BOX3_RENDEMENT</span> : 0.0674
- Parameter <span style="color:blue">HEFFINGSVRIJ_VERMOGEN</span> : 5720000


Regel bepaal/bereken box1 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_income</span> is
<span style="color:green">$BOX1_EMPLOYMENT</span> plus <span style="color:green">$BOX1_BENEFITS</span> plus <span style="color:green">$BOX1_BUSINESS</span> plus <span style="color:green">$BOX1_OTHER_WORK</span> plus <span style="color:green">$BOX1_HOME</span>

Regel bepaal/bereken box2 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_income</span> is
<span style="color:green">$BOX2_DIVIDEND</span> plus <span style="color:green">$BOX2_SHARES</span>

Regel bepaal/bereken box3 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_income</span> is
<span style="color:green">$BOX3_SAVINGS</span> plus <span style="color:green">$BOX3_INVESTMENTS</span> plus <span style="color:green">$BOX3_PROPERTIES</span>
 min <span style="color:green">$BOX3_DEBTS</span> min <span style="color:blue">$HEFFINGSVRIJ_VERMOGEN</span>

 keer <span style="color:blue">$BOX3_RENDEMENT</span>

Regel bepaal/bereken income \
Geldig vanaf: 2001-01-01

De <span style="color: green">income</span> is
<span style="color:green">$box1_income</span> plus <span style="color:green">$box2_income</span> plus <span style="color:green">$box3_income</span> plus <span style="color:green">$foreign_income</span>

Regel bepaal/bereken net worth \
Geldig vanaf: 2001-01-01

De <span style="color: green">net_worth</span> is
<span style="color:green">$BOX3_SAVINGS</span> plus <span style="color:green">$BOX3_INVESTMENTS</span> plus <span style="color:green">$BOX3_PROPERTIES</span>
 min <span style="color:green">$BOX3_DEBTS</span>

Regel bepaal/bereken partner box1 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box1_income</span> is

  - Indien

    dan <span style="color:green">$PARTNER_BOX1_EMPLOYMENT</span> plus <span style="color:green">$PARTNER_BOX1_BENEFITS</span> plus <span style="color:green">$PARTNER_BOX1_BUSINESS</span> plus <span style="color:green">$PARTNER_BOX1_OTHER_WORK</span> plus <span style="color:green">$PARTNER_BOX1_HOME</span>


  - Anders <span style="color:green">0</span>




Regel bepaal/bereken partner box2 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box2_income</span> is

  - Indien

    dan <span style="color:green">$PARTNER_BOX2_DIVIDEND</span> plus <span style="color:green">$PARTNER_BOX2_SHARES</span>


  - Anders <span style="color:green">0</span>




Regel bepaal/bereken partner box3 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box3_income</span> is

  - Indien

    dan <span style="color:green">$PARTNER_BOX3_SAVINGS</span> plus <span style="color:green">$PARTNER_BOX3_INVESTMENTS</span> plus <span style="color:green">$PARTNER_BOX3_PROPERTIES</span>
   min <span style="color:green">$PARTNER_BOX3_DEBTS</span> min <span style="color:blue">$HEFFINGSVRIJ_VERMOGEN</span>

   keer <span style="color:blue">$BOX3_RENDEMENT</span>


  - Anders <span style="color:green">0</span>



Regel bepaal/bereken partner income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_income</span> is
<span style="color:green">$partner_box1_income</span> plus <span style="color:green">$partner_box2_income</span> plus <span style="color:green">$partner_box3_income</span> plus <span style="color:green">$partner_foreign_income</span>

Regel bepaal/bereken partner foreign income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_foreign_income</span> is
<span style="color:green">$PARTNER_FOREIGN_INCOME</span>

Regel bepaal/bereken combined net worth \
Geldig vanaf: 2001-01-01

De <span style="color: green">combined_net_worth</span> is

  - Indien

    dan <span style="color:green">$net_worth</span> plus <span style="color:green">$PARTNER_BOX3_SAVINGS</span> plus <span style="color:green">$PARTNER_BOX3_INVESTMENTS</span> plus <span style="color:green">$PARTNER_BOX3_PROPERTIES</span>
   min <span style="color:green">$PARTNER_BOX3_DEBTS</span>



  - Anders <span style="color:green">$net_worth</span>



Regel bepaal/bereken assets \
Geldig vanaf: 2001-01-01

De <span style="color: green">assets</span> is
<span style="color:green">$BOX3_SAVINGS</span> plus <span style="color:green">$BOX3_INVESTMENTS</span> plus <span style="color:green">$BOX3_PROPERTIES</span>

Regel bepaal/bereken business income \
Geldig vanaf: 2001-01-01

De <span style="color: green">business_income</span> is
<span style="color:green">$BOX1_BUSINESS</span> delen door <span style="color:green">12</span>

Regel bepaal/bereken monthly income \
Geldig vanaf: 2001-01-01

De <span style="color: green">monthly_income</span> is
<span style="color:green">$box1_income</span> plus <span style="color:green">$box2_income</span> plus <span style="color:green">$box3_income</span>
 delen door <span style="color:green">12</span>
