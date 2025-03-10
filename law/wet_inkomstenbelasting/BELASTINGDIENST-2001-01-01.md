Berekening Inkomstenbelasting \
Gegenereerd op basis van wet_inkomstenbelasting \
**Geldig vanaf**: 2001-01-01 \
**Omschrijving**: Regels voor het berekenen van de inkomstenbelasting volgens de Wet inkomstenbelasting. De inkomstenbelasting wordt opgelegd op inkomen dat natuurlijke personen ontvangen, onderverdeeld in drie 'boxen': box 1 (werk en woning), box 2 (aanmerkelijk belang), en box 3 (sparen en beleggen). De wet regelt ook de berekening van heffingskortingen die de te betalen belasting verminderen.


Objecttype: Natuurlijk persoon
- Leeftijd van de persoon <span style="color:green">Age</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Geboortedatum van de persoon <span style="color:green">Birth date</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- AOW-leeftijd voor deze persoon <span style="color:green">Retirement age</span> uit het <span style="color:yellow"> SVB </span> op basis van <span style="color:pink"> algemene_ouderdomswet/leeftijdsbepaling </span>
- Heeft de persoon een fiscale partner <span style="color:green">Has partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- BSN van de fiscale partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft de persoon kinderen jonger dan 12 jaar <span style="color:green">Has children under 12</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- <span style="color:green">Total tax due</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box1 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box1 tax</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box2 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box2 tax</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box3 income</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box3 tax</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">General tax credit</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Labor tax credit</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Income dependent combination credit</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Total tax credits</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Taxable income</span> amount (eurocent precisie: 0 minimum: 0)
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
- Parameter <span style="color:blue">BOX1_BRACKET1_LIMIT</span> : 7457300
- Parameter <span style="color:blue">BOX1_BRACKET2_LIMIT</span> : 11932700
- Parameter <span style="color:blue">BOX1_RATE1</span> : 0.3693
- Parameter <span style="color:blue">BOX1_RATE1_AOW</span> : 0.1975
- Parameter <span style="color:blue">BOX1_RATE2</span> : 0.4953
- Parameter <span style="color:blue">BOX1_RATE2_AOW</span> : 0.4953
- Parameter <span style="color:blue">BOX2_BRACKET1_LIMIT</span> : 6700000
- Parameter <span style="color:blue">BOX2_RATE1</span> : 0.245
- Parameter <span style="color:blue">BOX2_RATE2</span> : 0.33
- Parameter <span style="color:blue">BOX3_DEEMED_RETURN_RATE</span> : 0.06
- Parameter <span style="color:blue">BOX3_RENDEMENT</span> : 0.0674
- Parameter <span style="color:blue">BOX3_TAX_FREE_ALLOWANCE_PARTNERS</span> : 11545800
- Parameter <span style="color:blue">BOX3_TAX_FREE_ALLOWANCE_SINGLE</span> : 5772900
- Parameter <span style="color:blue">BOX3_TAX_RATE</span> : 0.34
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_MAX</span> : 310400
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_MAX_AOW</span> : 165800
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_REDUCTION_RATE</span> : 0.06578
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_REDUCTION_RATE_AOW</span> : 0.03427
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_REDUCTION_START</span> : 2466800
- Parameter <span style="color:blue">GENERAL_TAX_CREDIT_ZERO_POINT</span> : 7243000
- Parameter <span style="color:blue">HEFFINGSVRIJ_VERMOGEN</span> : 5720000
- Parameter <span style="color:blue">INCOME_DEPENDENT_COMBINATION_CREDIT_BASE</span> : 88800
- Parameter <span style="color:blue">INCOME_DEPENDENT_COMBINATION_CREDIT_MAX</span> : 265000
- Parameter <span style="color:blue">INCOME_DEPENDENT_COMBINATION_CREDIT_MIN_INCOME</span> : 550300
- Parameter <span style="color:blue">INCOME_DEPENDENT_COMBINATION_CREDIT_RATE</span> : 0.11213
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_MAX</span> : 446400
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_MAX_AOW</span> : 238500
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_REDUCTION_RATE</span> : 0.0651
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_REDUCTION_RATE_AOW</span> : 0.034
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_REDUCTION_START</span> : 4081200
- Parameter <span style="color:blue">LABOR_TAX_CREDIT_ZERO_POINT</span> : 11932700
- Parameter <span style="color:blue">MIN_PERSONAL_INCOME</span> : 0


Regel bepaal/bereken box1 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_income</span> is
<span style="color:green">$BOX1_EMPLOYMENT</span> plus <span style="color:green">$BOX1_BUSINESS</span> plus <span style="color:green">$BOX1_BENEFITS</span> plus <span style="color:green">$BOX1_OTHER_WORK</span> plus <span style="color:green">$BOX1_HOME</span>


Regel bepaal/bereken box2 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_income</span> is
<span style="color:green">$BOX2_DIVIDEND</span> plus <span style="color:green">$BOX2_SHARES</span>


Regel bepaal/bereken box3 assets \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_assets</span> is
<span style="color:green">$BOX3_SAVINGS</span> plus <span style="color:green">$BOX3_INVESTMENTS</span> plus <span style="color:green">$BOX3_PROPERTIES</span>

 min <span style="color:green">$BOX3_DEBTS</span> min
  - Indien <span style="color:green">$HAS_PARTNER</span> gelijk aan <span style="color:green">true</span>


    dan <span style="color:blue">$BOX3_TAX_FREE_ALLOWANCE_PARTNERS</span>


  - Anders <span style="color:blue">$BOX3_TAX_FREE_ALLOWANCE_SINGLE</span>







Regel bepaal/bereken box3 income \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_income</span> is
<span style="color:green">$box3_assets</span> keer <span style="color:blue">$BOX3_DEEMED_RETURN_RATE</span>


Regel bepaal/bereken taxable income \
Geldig vanaf: 2001-01-01

De <span style="color: green">taxable_income</span> is
<span style="color:green">$box1_income</span> plus <span style="color:green">$box2_income</span> plus <span style="color:green">$box3_income</span> plus  min <span style="color:green">$PERSONAL_DEDUCTIONS</span>




Regel bepaal/bereken box1 income after deduction \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_income_after_deduction</span> is
<span style="color:green">$box1_income</span> min <span style="color:green">$PERSONAL_DEDUCTIONS</span>




Regel bepaal/bereken remaining deduction after box1 \
Geldig vanaf: 2001-01-01

De <span style="color: green">remaining_deduction_after_box1</span> is
<span style="color:green">$PERSONAL_DEDUCTIONS</span> min <span style="color:green">$box1_income</span>




Regel bepaal/bereken box3 income after deduction \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_income_after_deduction</span> is
<span style="color:green">$box3_income</span> min <span style="color:green">$remaining_deduction_after_box1</span>




Regel bepaal/bereken remaining deduction after box3 \
Geldig vanaf: 2001-01-01

De <span style="color: green">remaining_deduction_after_box3</span> is
<span style="color:green">$remaining_deduction_after_box1</span> min <span style="color:green">$box3_income</span>




Regel bepaal/bereken box2 income after deduction \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_income_after_deduction</span> is
<span style="color:green">$box2_income</span> min <span style="color:green">$remaining_deduction_after_box3</span>




Regel bepaal/bereken is aow age \
Geldig vanaf: 2001-01-01

De <span style="color: green">is_aow_age</span> is
<span style="color:green">$AGE</span> groter dan of gelijk aan <span style="color:green">$RETIREMENT_AGE</span>


Regel bepaal/bereken box1 tax \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_tax</span> is

  - Indien <span style="color:green">$is_aow_age</span> gelijk aan <span style="color:green">true</span>


    dan
    - Indien <span style="color:green">$box1_income_after_deduction</span> minder dan of gelijk aan <span style="color:blue">$BOX1_BRACKET1_LIMIT</span>


      dan <span style="color:green">$box1_income_after_deduction</span> keer <span style="color:blue">$BOX1_RATE1_AOW</span>



    - Anders <span style="color:blue">$BOX1_BRACKET1_LIMIT</span> keer <span style="color:blue">$BOX1_RATE1_AOW</span>

     plus <span style="color:green">$box1_income_after_deduction</span> min <span style="color:blue">$BOX1_BRACKET1_LIMIT</span>

     keer <span style="color:blue">$BOX1_RATE2_AOW</span>







  - Anders
    - Indien <span style="color:green">$box1_income_after_deduction</span> minder dan of gelijk aan <span style="color:blue">$BOX1_BRACKET1_LIMIT</span>


      dan <span style="color:green">$box1_income_after_deduction</span> keer <span style="color:blue">$BOX1_RATE1</span>



    - Anders <span style="color:blue">$BOX1_BRACKET1_LIMIT</span> keer <span style="color:blue">$BOX1_RATE1</span>

     plus <span style="color:green">$box1_income_after_deduction</span> min <span style="color:blue">$BOX1_BRACKET1_LIMIT</span>

     keer <span style="color:blue">$BOX1_RATE2</span>








Regel bepaal/bereken box2 tax \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_tax</span> is

  - Indien <span style="color:green">$box2_income_after_deduction</span> minder dan of gelijk aan <span style="color:blue">$BOX2_BRACKET1_LIMIT</span>


    dan <span style="color:green">$box2_income_after_deduction</span> keer <span style="color:blue">$BOX2_RATE1</span>



  - Anders <span style="color:blue">$BOX2_BRACKET1_LIMIT</span> keer <span style="color:blue">$BOX2_RATE1</span>

   plus <span style="color:green">$box2_income_after_deduction</span> min <span style="color:blue">$BOX2_BRACKET1_LIMIT</span>

   keer <span style="color:blue">$BOX2_RATE2</span>






Regel bepaal/bereken box3 tax \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_tax</span> is
<span style="color:green">$box3_income_after_deduction</span> keer <span style="color:blue">$BOX3_TAX_RATE</span>


Regel bepaal/bereken general tax credit \
Geldig vanaf: 2001-01-01

De <span style="color: green">general_tax_credit</span> is

  - Indien <span style="color:green">$is_aow_age</span> gelijk aan <span style="color:green">true</span>


    dan <span style="color:blue">$GENERAL_TAX_CREDIT_MAX_AOW</span> min
    - Indien <span style="color:green">$box1_income</span> groter dan <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>


      dan <span style="color:green">$box1_income</span> min <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>

     minimaal <span style="color:blue">$GENERAL_TAX_CREDIT_ZERO_POINT</span> min <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>



     keer <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_RATE_AOW</span>



    - Anders <span style="color:green">0</span>








  - Anders <span style="color:blue">$GENERAL_TAX_CREDIT_MAX</span> min
    - Indien <span style="color:green">$box1_income</span> groter dan <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>


      dan <span style="color:green">$box1_income</span> min <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>

     minimaal <span style="color:blue">$GENERAL_TAX_CREDIT_ZERO_POINT</span> min <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_START</span>



     keer <span style="color:blue">$GENERAL_TAX_CREDIT_REDUCTION_RATE</span>



    - Anders <span style="color:green">0</span>









Regel bepaal/bereken labor tax credit \
Geldig vanaf: 2001-01-01

De <span style="color: green">labor_tax_credit</span> is

  - Indien <span style="color:green">$is_aow_age</span> gelijk aan <span style="color:green">true</span>


    dan <span style="color:blue">$LABOR_TAX_CREDIT_MAX_AOW</span> min
    - Indien <span style="color:green">$BOX1_EMPLOYMENT</span> groter dan <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>


      dan <span style="color:green">$BOX1_EMPLOYMENT</span> min <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>

     minimaal <span style="color:blue">$LABOR_TAX_CREDIT_ZERO_POINT</span> min <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>



     keer <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_RATE_AOW</span>



    - Anders <span style="color:green">0</span>








  - Anders <span style="color:blue">$LABOR_TAX_CREDIT_MAX</span> min
    - Indien <span style="color:green">$BOX1_EMPLOYMENT</span> groter dan <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>


      dan <span style="color:green">$BOX1_EMPLOYMENT</span> min <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>

     minimaal <span style="color:blue">$LABOR_TAX_CREDIT_ZERO_POINT</span> min <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_START</span>



     keer <span style="color:blue">$LABOR_TAX_CREDIT_REDUCTION_RATE</span>



    - Anders <span style="color:green">0</span>









Regel bepaal/bereken income dependent combination credit \
Geldig vanaf: 2001-01-01

De <span style="color: green">income_dependent_combination_credit</span> is

  - Indien <span style="color:green">$HAS_CHILDREN_UNDER_12</span> gelijk aan <span style="color:green">true</span>

   en <span style="color:green">$BOX1_EMPLOYMENT</span> groter dan <span style="color:blue">$INCOME_DEPENDENT_COMBINATION_CREDIT_MIN_INCOME</span>




    dan <span style="color:blue">$INCOME_DEPENDENT_COMBINATION_CREDIT_BASE</span> plus <span style="color:green">$BOX1_EMPLOYMENT</span> min <span style="color:blue">$INCOME_DEPENDENT_COMBINATION_CREDIT_MIN_INCOME</span>

   keer <span style="color:blue">$INCOME_DEPENDENT_COMBINATION_CREDIT_RATE</span>



   minimaal <span style="color:blue">$INCOME_DEPENDENT_COMBINATION_CREDIT_MAX</span>



  - Anders <span style="color:green">0</span>



Regel bepaal/bereken total tax credits \
Geldig vanaf: 2001-01-01

De <span style="color: green">total_tax_credits</span> is
<span style="color:green">$general_tax_credit</span> plus <span style="color:green">$labor_tax_credit</span> plus <span style="color:green">$income_dependent_combination_credit</span>


Regel bepaal/bereken total tax due \
Geldig vanaf: 2001-01-01

De <span style="color: green">total_tax_due</span> is
<span style="color:green">$box1_tax</span> plus <span style="color:green">$box2_tax</span> plus <span style="color:green">$box3_tax</span>

 min <span style="color:green">$total_tax_credits</span>




Regel bepaal/bereken foreign income \
Geldig vanaf: 2001-01-01

De <span style="color: green">foreign_income</span> is
<span style="color:green">$FOREIGN_INCOME</span>


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



Regel bepaal/bereken partner foreign income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_foreign_income</span> is
<span style="color:green">$PARTNER_FOREIGN_INCOME</span>


Regel bepaal/bereken partner income \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_income</span> is
<span style="color:green">$partner_box1_income</span> plus <span style="color:green">$partner_box2_income</span> plus <span style="color:green">$partner_box3_income</span> plus <span style="color:green">$partner_foreign_income</span>


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
