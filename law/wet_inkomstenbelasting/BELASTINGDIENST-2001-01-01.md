Inkomstenbelasting \
Gegenereerd op basis van wet_inkomstenbelasting \
**Geldig vanaf**: 2001-01-01 \
**Omschrijving**: Regels voor het berekenen van de inkomstenbelasting volgens de Wet inkomstenbelasting. De inkomstenbelasting wordt opgelegd op inkomen dat natuurlijke personen ontvangen, onderverdeeld in drie 'boxen': box 1 (werk en woning), box 2 (aanmerkelijk belang), en box 3 (sparen en beleggen). De wet regelt ook de berekening van heffingskortingen die de te betalen belasting verminderen.


Objecttype: Natuurlijk persoon
- Leeftijd van de persoon <span style="color:green">Leeftijd</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Geboortedatum van de persoon <span style="color:green">Geboortedatum</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- AOW-leeftijd voor deze persoon <span style="color:green">Pensioenleeftijd</span> uit het <span style="color:yellow"> SVB </span> op basis van <span style="color:pink"> algemene_ouderdomswet/leeftijdsbepaling </span>
- Heeft de persoon een fiscale partner <span style="color:green">Heeft partner</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- BSN van de fiscale partner <span style="color:green">Partner bsn</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- Heeft de persoon kinderen jonger dan 12 jaar <span style="color:green">Heeft kinderen onder 12</span> uit het <span style="color:yellow"> RvIG </span> op basis van <span style="color:pink"> wet_brp </span>
- <span style="color:green">Totale belastingschuld</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box1 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box1 belasting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box2 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box2 belasting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box3 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Box3 belasting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Algemene heffingskorting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Arbeidskorting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Inkomensafhankelijke combinatiekorting</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Totale heffingskortingen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Belastbaar inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Buitenlands inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Vermogen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box1 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box2 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner box3 inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner buitenlands inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Partner inkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Gezamenlijk vermogen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Bezittingen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Bedrijfsinkomen</span> amount (eurocent precisie: 0 minimum: 0)
- <span style="color:green">Maandelijks inkomen</span> amount (eurocent precisie: 0 minimum: 0)

## Parameters ##
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_AFBOUW</span> : 0.06578
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_AFBOUW_AOW</span> : 0.03427
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span> : 2466800
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_MAX</span> : 310400
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_MAX_AOW</span> : 165800
- Parameter <span style="color:blue">ALGEMENE_HEFFINGSKORTING_NULPUNT</span> : 7243000
- Parameter <span style="color:blue">ARBEIDSKORTING_AFBOUW</span> : 0.0651
- Parameter <span style="color:blue">ARBEIDSKORTING_AFBOUW_AOW</span> : 0.034
- Parameter <span style="color:blue">ARBEIDSKORTING_AFBOUW_START</span> : 4081200
- Parameter <span style="color:blue">ARBEIDSKORTING_MAX</span> : 446400
- Parameter <span style="color:blue">ARBEIDSKORTING_MAX_AOW</span> : 238500
- Parameter <span style="color:blue">ARBEIDSKORTING_NULPUNT</span> : 11932700
- Parameter <span style="color:blue">BOX1_SCHIJF1_GRENS</span> : 7457300
- Parameter <span style="color:blue">BOX1_SCHIJF2_GRENS</span> : 11932700
- Parameter <span style="color:blue">BOX1_TARIEF1</span> : 0.3693
- Parameter <span style="color:blue">BOX1_TARIEF1_AOW</span> : 0.1975
- Parameter <span style="color:blue">BOX1_TARIEF2</span> : 0.4953
- Parameter <span style="color:blue">BOX1_TARIEF2_AOW</span> : 0.4953
- Parameter <span style="color:blue">BOX2_SCHIJF1_GRENS</span> : 6700000
- Parameter <span style="color:blue">BOX2_TARIEF1</span> : 0.245
- Parameter <span style="color:blue">BOX2_TARIEF2</span> : 0.33
- Parameter <span style="color:blue">BOX3_BELASTINGTARIEF</span> : 0.34
- Parameter <span style="color:blue">BOX3_FORFAITAIR_RENDEMENT</span> : 0.06
- Parameter <span style="color:blue">BOX3_HEFFINGSVRIJE_VOET_ALLEENSTAAND</span> : 5772900
- Parameter <span style="color:blue">BOX3_HEFFINGSVRIJE_VOET_PARTNERS</span> : 11545800
- Parameter <span style="color:blue">BOX3_RENDEMENT</span> : 0.0674
- Parameter <span style="color:blue">HEFFINGSVRIJ_VERMOGEN</span> : 5720000
- Parameter <span style="color:blue">INKOMENSAFHANKELIJKE_COMBINATIEKORTING_BASIS</span> : 88800
- Parameter <span style="color:blue">INKOMENSAFHANKELIJKE_COMBINATIEKORTING_MAX</span> : 265000
- Parameter <span style="color:blue">INKOMENSAFHANKELIJKE_COMBINATIEKORTING_MIN_INKOMEN</span> : 550300
- Parameter <span style="color:blue">INKOMENSAFHANKELIJKE_COMBINATIEKORTING_PERCENTAGE</span> : 0.11213
- Parameter <span style="color:blue">MIN_PERSONAL_INCOME</span> : 0


Regel bepaal/bereken box1 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_inkomen</span> is
<span style="color:green">$BOX1_DIENSTBETREKKING</span> plus <span style="color:green">$BOX1_ONDERNEMING</span> plus <span style="color:green">$BOX1_UITKERINGEN</span> plus <span style="color:green">$BOX1_OVERIGE_WERKZAAMHEDEN</span> plus <span style="color:green">$BOX1_EIGEN_WONING</span>


Regel bepaal/bereken box2 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_inkomen</span> is
<span style="color:green">$BOX2_DIVIDEND</span> plus <span style="color:green">$BOX2_AANDELEN</span>


Regel bepaal/bereken box3 bezittingen \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_bezittingen</span> is
<span style="color:green">$BOX3_SPAREN</span> plus <span style="color:green">$BOX3_BELEGGEN</span> plus <span style="color:green">$BOX3_ONROEREND_GOED</span>

 min <span style="color:green">$BOX3_SCHULDEN</span> min 
  - Indien <span style="color:green">$HEEFT_PARTNER</span> gelijk aan <span style="color:green">true</span>
  
  
    dan <span style="color:blue">$BOX3_HEFFINGSVRIJE_VOET_PARTNERS</span>
  
	
  - Anders <span style="color:blue">$BOX3_HEFFINGSVRIJE_VOET_ALLEENSTAAND</span>
  
	





Regel bepaal/bereken box3 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_inkomen</span> is
<span style="color:green">$box3_bezittingen</span> keer <span style="color:blue">$BOX3_FORFAITAIR_RENDEMENT</span>


Regel bepaal/bereken belastbaar inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">belastbaar_inkomen</span> is
<span style="color:green">$box1_inkomen</span> plus <span style="color:green">$box2_inkomen</span> plus <span style="color:green">$box3_inkomen</span> plus  min <span style="color:green">$PERSOONSGEBONDEN_AFTREK</span>




Regel bepaal/bereken box1 inkomen na aftrek \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_inkomen_na_aftrek</span> is
<span style="color:green">$box1_inkomen</span> min <span style="color:green">$PERSOONSGEBONDEN_AFTREK</span>




Regel bepaal/bereken resterende aftrek na box1 \
Geldig vanaf: 2001-01-01

De <span style="color: green">resterende_aftrek_na_box1</span> is
<span style="color:green">$PERSOONSGEBONDEN_AFTREK</span> min <span style="color:green">$box1_inkomen</span>




Regel bepaal/bereken box3 inkomen na aftrek \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_inkomen_na_aftrek</span> is
<span style="color:green">$box3_inkomen</span> min <span style="color:green">$resterende_aftrek_na_box1</span>




Regel bepaal/bereken resterende aftrek na box3 \
Geldig vanaf: 2001-01-01

De <span style="color: green">resterende_aftrek_na_box3</span> is
<span style="color:green">$resterende_aftrek_na_box1</span> min <span style="color:green">$box3_inkomen</span>




Regel bepaal/bereken box2 inkomen na aftrek \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_inkomen_na_aftrek</span> is
<span style="color:green">$box2_inkomen</span> min <span style="color:green">$resterende_aftrek_na_box3</span>




Regel bepaal/bereken is aow leeftijd \
Geldig vanaf: 2001-01-01

De <span style="color: green">is_aow_leeftijd</span> is
<span style="color:green">$LEEFTIJD</span> groter dan of gelijk aan <span style="color:green">$PENSIOENLEEFTIJD</span>


Regel bepaal/bereken box1 belasting \
Geldig vanaf: 2001-01-01

De <span style="color: green">box1_belasting</span> is

  - Indien <span style="color:green">$is_aow_leeftijd</span> gelijk aan <span style="color:green">true</span>
  
  
    dan 
    - Indien <span style="color:green">$box1_inkomen_na_aftrek</span> minder dan of gelijk aan <span style="color:blue">$BOX1_SCHIJF1_GRENS</span>
    
    
      dan <span style="color:green">$box1_inkomen_na_aftrek</span> keer <span style="color:blue">$BOX1_TARIEF1_AOW</span>
    
    
  	
    - Anders <span style="color:blue">$BOX1_SCHIJF1_GRENS</span> keer <span style="color:blue">$BOX1_TARIEF1_AOW</span>
    
     plus <span style="color:green">$box1_inkomen_na_aftrek</span> min <span style="color:blue">$BOX1_SCHIJF1_GRENS</span>
    
     keer <span style="color:blue">$BOX1_TARIEF2_AOW</span>
    
    
    
    
  	
  
	
  - Anders 
    - Indien <span style="color:green">$box1_inkomen_na_aftrek</span> minder dan of gelijk aan <span style="color:blue">$BOX1_SCHIJF1_GRENS</span>
    
    
      dan <span style="color:green">$box1_inkomen_na_aftrek</span> keer <span style="color:blue">$BOX1_TARIEF1</span>
    
    
  	
    - Anders <span style="color:blue">$BOX1_SCHIJF1_GRENS</span> keer <span style="color:blue">$BOX1_TARIEF1</span>
    
     plus <span style="color:green">$box1_inkomen_na_aftrek</span> min <span style="color:blue">$BOX1_SCHIJF1_GRENS</span>
    
     keer <span style="color:blue">$BOX1_TARIEF2</span>
    
    
    
    
  	
  
	

Regel bepaal/bereken box2 belasting \
Geldig vanaf: 2001-01-01

De <span style="color: green">box2_belasting</span> is

  - Indien <span style="color:green">$box2_inkomen_na_aftrek</span> minder dan of gelijk aan <span style="color:blue">$BOX2_SCHIJF1_GRENS</span>
  
  
    dan <span style="color:green">$box2_inkomen_na_aftrek</span> keer <span style="color:blue">$BOX2_TARIEF1</span>
  
  
	
  - Anders <span style="color:blue">$BOX2_SCHIJF1_GRENS</span> keer <span style="color:blue">$BOX2_TARIEF1</span>
  
   plus <span style="color:green">$box2_inkomen_na_aftrek</span> min <span style="color:blue">$BOX2_SCHIJF1_GRENS</span>
  
   keer <span style="color:blue">$BOX2_TARIEF2</span>
  
  
  
  
	

Regel bepaal/bereken box3 belasting \
Geldig vanaf: 2001-01-01

De <span style="color: green">box3_belasting</span> is
<span style="color:green">$box3_inkomen_na_aftrek</span> keer <span style="color:blue">$BOX3_BELASTINGTARIEF</span>


Regel bepaal/bereken algemene heffingskorting \
Geldig vanaf: 2001-01-01

De <span style="color: green">algemene_heffingskorting</span> is

  - Indien <span style="color:green">$is_aow_leeftijd</span> gelijk aan <span style="color:green">true</span>
  
  
    dan <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_MAX_AOW</span> min 
    - Indien <span style="color:green">$box1_inkomen</span> groter dan <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
    
      dan <span style="color:green">$box1_inkomen</span> min <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
     minimaal <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_NULPUNT</span> min <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
    
    
     keer <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_AOW</span>
    
    
  	
    - Anders <span style="color:green">0</span>
    
  	
  
  
  
  
  
	
  - Anders <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_MAX</span> min 
    - Indien <span style="color:green">$box1_inkomen</span> groter dan <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
    
      dan <span style="color:green">$box1_inkomen</span> min <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
     minimaal <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_NULPUNT</span> min <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW_START</span>
    
    
    
     keer <span style="color:blue">$ALGEMENE_HEFFINGSKORTING_AFBOUW</span>
    
    
  	
    - Anders <span style="color:green">0</span>
    
  	
  
  
  
  
  
	

Regel bepaal/bereken arbeidskorting \
Geldig vanaf: 2001-01-01

De <span style="color: green">arbeidskorting</span> is

  - Indien <span style="color:green">$is_aow_leeftijd</span> gelijk aan <span style="color:green">true</span>
  
  
    dan <span style="color:blue">$ARBEIDSKORTING_MAX_AOW</span> min 
    - Indien <span style="color:green">$BOX1_DIENSTBETREKKING</span> groter dan <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
    
      dan <span style="color:green">$BOX1_DIENSTBETREKKING</span> min <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
     minimaal <span style="color:blue">$ARBEIDSKORTING_NULPUNT</span> min <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
    
    
     keer <span style="color:blue">$ARBEIDSKORTING_AFBOUW_AOW</span>
    
    
  	
    - Anders <span style="color:green">0</span>
    
  	
  
  
  
  
  
	
  - Anders <span style="color:blue">$ARBEIDSKORTING_MAX</span> min 
    - Indien <span style="color:green">$BOX1_DIENSTBETREKKING</span> groter dan <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
    
      dan <span style="color:green">$BOX1_DIENSTBETREKKING</span> min <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
     minimaal <span style="color:blue">$ARBEIDSKORTING_NULPUNT</span> min <span style="color:blue">$ARBEIDSKORTING_AFBOUW_START</span>
    
    
    
     keer <span style="color:blue">$ARBEIDSKORTING_AFBOUW</span>
    
    
  	
    - Anders <span style="color:green">0</span>
    
  	
  
  
  
  
  
	

Regel bepaal/bereken inkomensafhankelijke combinatiekorting \
Geldig vanaf: 2001-01-01

De <span style="color: green">inkomensafhankelijke_combinatiekorting</span> is

  - Indien <span style="color:green">$HEEFT_KINDEREN_ONDER_12</span> gelijk aan <span style="color:green">true</span>
  
   en <span style="color:green">$BOX1_DIENSTBETREKKING</span> groter dan <span style="color:blue">$INKOMENSAFHANKELIJKE_COMBINATIEKORTING_MIN_INKOMEN</span>
  
  
  
  
    dan <span style="color:blue">$INKOMENSAFHANKELIJKE_COMBINATIEKORTING_BASIS</span> plus <span style="color:green">$BOX1_DIENSTBETREKKING</span> min <span style="color:blue">$INKOMENSAFHANKELIJKE_COMBINATIEKORTING_MIN_INKOMEN</span>
  
   keer <span style="color:blue">$INKOMENSAFHANKELIJKE_COMBINATIEKORTING_PERCENTAGE</span>
  
  
  
   minimaal <span style="color:blue">$INKOMENSAFHANKELIJKE_COMBINATIEKORTING_MAX</span>
  
  
	
  - Anders <span style="color:green">0</span>
  
	

Regel bepaal/bereken totale heffingskortingen \
Geldig vanaf: 2001-01-01

De <span style="color: green">totale_heffingskortingen</span> is
<span style="color:green">$algemene_heffingskorting</span> plus <span style="color:green">$arbeidskorting</span> plus <span style="color:green">$inkomensafhankelijke_combinatiekorting</span>


Regel bepaal/bereken totale belastingschuld \
Geldig vanaf: 2001-01-01

De <span style="color: green">totale_belastingschuld</span> is
<span style="color:green">$box1_belasting</span> plus <span style="color:green">$box2_belasting</span> plus <span style="color:green">$box3_belasting</span>

 min <span style="color:green">$totale_heffingskortingen</span>




Regel bepaal/bereken buitenlands inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">buitenlands_inkomen</span> is
<span style="color:green">$BUITENLANDS_INKOMEN</span>


Regel bepaal/bereken inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">inkomen</span> is
<span style="color:green">$box1_inkomen</span> plus <span style="color:green">$box2_inkomen</span> plus <span style="color:green">$box3_inkomen</span> plus <span style="color:green">$buitenlands_inkomen</span>


Regel bepaal/bereken vermogen \
Geldig vanaf: 2001-01-01

De <span style="color: green">vermogen</span> is
<span style="color:green">$BOX3_SPAREN</span> plus <span style="color:green">$BOX3_BELEGGEN</span> plus <span style="color:green">$BOX3_ONROEREND_GOED</span>

 min <span style="color:green">$BOX3_SCHULDEN</span>


Regel bepaal/bereken partner box1 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box1_inkomen</span> is

  - Indien 
  
    dan <span style="color:green">$PARTNER_BOX1_DIENSTBETREKKING</span> plus <span style="color:green">$PARTNER_BOX1_UITKERINGEN</span> plus <span style="color:green">$PARTNER_BOX1_ONDERNEMING</span> plus <span style="color:green">$PARTNER_BOX1_OVERIGE_WERKZAAMHEDEN</span> plus <span style="color:green">$PARTNER_BOX1_EIGEN_WONING</span>
  
  
	
  - Anders <span style="color:green">0</span>
  
	



Regel bepaal/bereken partner box2 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box2_inkomen</span> is

  - Indien 
  
    dan <span style="color:green">$PARTNER_BOX2_DIVIDEND</span> plus <span style="color:green">$PARTNER_BOX2_AANDELEN</span>
  
  
	
  - Anders <span style="color:green">0</span>
  
	



Regel bepaal/bereken partner box3 inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_box3_inkomen</span> is

  - Indien 
  
    dan <span style="color:green">$PARTNER_BOX3_SPAREN</span> plus <span style="color:green">$PARTNER_BOX3_BELEGGEN</span> plus <span style="color:green">$PARTNER_BOX3_ONROEREND_GOED</span>
  
   min <span style="color:green">$PARTNER_BOX3_SCHULDEN</span> min <span style="color:blue">$HEFFINGSVRIJ_VERMOGEN</span>
  
  
  
   keer <span style="color:blue">$BOX3_RENDEMENT</span>
  
  
	
  - Anders <span style="color:green">0</span>
  
	

Regel bepaal/bereken partner buitenlands inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_buitenlands_inkomen</span> is
<span style="color:green">$PARTNER_BUITENLANDS_INKOMEN</span>


Regel bepaal/bereken partner inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">partner_inkomen</span> is
<span style="color:green">$partner_box1_inkomen</span> plus <span style="color:green">$partner_box2_inkomen</span> plus <span style="color:green">$partner_box3_inkomen</span> plus <span style="color:green">$partner_buitenlands_inkomen</span>


Regel bepaal/bereken gezamenlijk vermogen \
Geldig vanaf: 2001-01-01

De <span style="color: green">gezamenlijk_vermogen</span> is

  - Indien 
  
    dan <span style="color:green">$vermogen</span> plus <span style="color:green">$PARTNER_BOX3_SPAREN</span> plus <span style="color:green">$PARTNER_BOX3_BELEGGEN</span> plus <span style="color:green">$PARTNER_BOX3_ONROEREND_GOED</span>
  
   min <span style="color:green">$PARTNER_BOX3_SCHULDEN</span>
  
  
  
  
	
  - Anders <span style="color:green">$vermogen</span>
  
	

Regel bepaal/bereken bezittingen \
Geldig vanaf: 2001-01-01

De <span style="color: green">bezittingen</span> is
<span style="color:green">$BOX3_SPAREN</span> plus <span style="color:green">$BOX3_BELEGGEN</span> plus <span style="color:green">$BOX3_ONROEREND_GOED</span>


Regel bepaal/bereken bedrijfsinkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">bedrijfsinkomen</span> is
<span style="color:green">$BOX1_ONDERNEMING</span> delen door <span style="color:green">12</span>


Regel bepaal/bereken maandelijks inkomen \
Geldig vanaf: 2001-01-01

De <span style="color: green">maandelijks_inkomen</span> is
<span style="color:green">$box1_inkomen</span> plus <span style="color:green">$box2_inkomen</span> plus <span style="color:green">$box3_inkomen</span>

 delen door <span style="color:green">12</span>


