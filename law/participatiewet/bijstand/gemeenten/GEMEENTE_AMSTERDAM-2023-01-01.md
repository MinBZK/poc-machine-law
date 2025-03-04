Bijstand Gemeente Amsterdam \
Gegenereerd op basis van participatiewet/bijstand \
Geldig vanaf: 2024-01-01

Objecttype: Natuurlijk persoon
- Voldoet aan landelijke voorwaarden <span style="color:green">Meets national requirements</span> uit het <span style="color:yellow"> SZW </span> op basis van <span style="color:pink"> participatiewet/bijstand </span>
- Landelijke bijstandsnorm <span style="color:green">National base amount</span> uit het <span style="color:yellow"> SZW </span> op basis van <span style="color:pink"> participatiewet/bijstand </span>
- Landelijke kostendelersnorm <span style="color:green">Kostendelersnorm</span> uit het <span style="color:yellow"> SZW </span> op basis van <span style="color:pink"> participatiewet/bijstand </span>
- Leeftijd van de aanvrager <span style="color:green">Age</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft vast woonadres <span style="color:green">Has fixed address</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Postdres <span style="color:green">Postal address</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Is ondernemer/ZZP-er <span style="color:green">Is entrepreneur</span> uit het <span style="color:yellow"> KVK </span> op basis van <span style="color:pink"> handelsregisterwet </span>
- Inkomsten uit onderneming <span style="color:green">Business income</span> uit het <span style="color:yellow"> BELASTINGDIENST </span> op basis van <span style="color:pink"> wet_inkomstenbelasting </span>
- <span style="color:green">Is eligible</span> boolean
- <span style="color:green">Benefit amount</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Housing assistance</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Startup assistance</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:green">FULL_EXEMPTION_REASONS</span> : [MEDISCH_VOLLEDIG MANTELZORG_VOLLEDIG SOCIALE_OMSTANDIGHEDEN_VOLLEDIG]
- Parameter <span style="color:green">HOUSING_ASSISTANCE_AMOUNT</span> : 60000
- Parameter <span style="color:green">RE_INTEGRATION_SUPPLEMENT</span> : 15000
- Parameter <span style="color:green">STARTUP_ASSISTANCE_MAX</span> : 200000
- Parameter <span style="color:green">VALID_POSTAL_ADDRESSES</span> : [De Regenboog Groep 1, 1012NX Amsterdam HVO-Querido Leger des Heils Amsterdam]
- Parameter <span style="color:green">YOUTH_MAX_AGE</span> : 27
- Parameter <span style="color:green">YOUTH_SUPPLEMENT</span> : 25000
- Parameter <span style="color:green">ZZP_INCOME_DISREGARD_PERCENTAGE</span> : 0.2


Regel bepaal/bereken is eligible

Geldig vanaf: 2024-01-01



Regel bepaal/bereken benefit amount

Geldig vanaf: 2024-01-01


	<span style="color:green">$NATIONAL_BASE_AMOUNT</span> keer <span style="color:green">$KOSTENDELERSNORM</span>
 plus
  - als <span style="color:green">$AGE</span> minder dan of gelijk aan <span style="color:green">$YOUTH_MAX_AGE</span>
   en <span style="color:green">$HAS_FIXED_ADDRESS</span> gelijk aan
  	<span style="color:green">true</span>




    dan <span style="color:green">$YOUTH_SUPPLEMENT</span>

  - anders <span style="color:green">0</span>
 plus
  - als <span style="color:green">$IS_ENTREPRENEUR</span> gelijk aan
  	<span style="color:green">true</span>
   en <span style="color:green">$BUSINESS_INCOME</span> groter dan <span style="color:green">0</span>




    dan <span style="color:green">$BUSINESS_INCOME</span> keer <span style="color:green">$ZZP_INCOME_DISREGARD_PERCENTAGE</span>


  - anders <span style="color:green">0</span>
 plus
  - als <span style="color:green"><no value></span>


    dan <span style="color:green">$RE_INTEGRATION_SUPPLEMENT</span>

  - anders <span style="color:green">0</span>




Regel bepaal/bereken housing assistance

Geldig vanaf: 2024-01-01
De <span style="color: green">housing_assistance</span> is
-  dan<span style="color:green">$HOUSING_ASSISTANCE_AMOUNT</span>
-


Regel bepaal/bereken startup assistance

Geldig vanaf: 2024-01-01
De <span style="color: green">startup_assistance</span> is
-  dan<span style="color:green">$STARTUP_ASSISTANCE_MAX</span>
-
