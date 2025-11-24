Feature: AWIR Toeslagproces - Zorgtoeslag
  Als burger
  Wil ik zorgtoeslag kunnen aanvragen en ontvangen
  Zodat ik mijn zorgverzekering kan betalen

  Background:
    Given de datum is "2025-02-01"
    And een persoon met BSN "999993653"

  Scenario: Burger vraagt zorgtoeslag aan en heeft recht
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 25000                     | 0                         | 0                     | 0                               | 0            |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000      | 0           | 0              | 0        |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    Then is de toeslag status "AANVRAAG"
    When de aanspraak wordt berekend
    Then heeft de burger aanspraak op zorgtoeslag
    And is de toeslag status "BEREKEND"

  Scenario: Burger krijgt voorschotbeschikking
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 25000                     | 0                         | 0                     | 0                               | 0            |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000      | 0           | 0              | 0        |
    And de burger heeft zorgtoeslag aangevraagd voor jaar 2025
    And de aanspraak is berekend met recht op toeslag
    When de voorschotbeschikking wordt vastgesteld
    Then is de toeslag status "VOORSCHOT"
    And is het voorschot maandbedrag groter dan 0
    And bevat de beschikkingen historie een "VOORSCHOT" beschikking

  Scenario: Maandelijkse herberekening en betaling
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 25000                     | 0                         | 0                     | 0                               | 0            |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000      | 0           | 0              | 0        |
    And de burger heeft een lopende zorgtoeslag voor jaar 2025
    When maand 3 wordt herberekend
    And maand 3 wordt betaald
    Then bevat de maandelijkse berekeningen een berekening voor maand 3
    And bevat de maandelijkse betalingen een betaling voor maand 3
    And is de betaling gebaseerd op het voorschotbedrag

  Scenario: Definitieve beschikking met nabetaling
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de burger heeft een afgeronde zorgtoeslag voor jaar 2024
    And het totaal betaalde voorschot is 200000 eurocent
    When de definitieve beschikking wordt vastgesteld met jaarbedrag 220000 eurocent
    And de vereffening wordt uitgevoerd
    Then is de toeslag status "VEREFFEND"
    And is het vereffening type "NABETALING"
    And is het vereffening bedrag 20000 eurocent

  Scenario: Definitieve beschikking met terugvordering
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de burger heeft een afgeronde zorgtoeslag voor jaar 2024
    And het totaal betaalde voorschot is 240000 eurocent
    When de definitieve beschikking wordt vastgesteld met jaarbedrag 200000 eurocent
    And de vereffening wordt uitgevoerd
    Then is de toeslag status "VEREFFEND"
    And is het vereffening type "TERUGVORDERING"
    And is het vereffening bedrag 40000 eurocent

  Scenario: Burger jonger dan 18 heeft geen recht op zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2010-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    Then heeft de burger geen aanspraak op zorgtoeslag
    And is de toeslag status "AFGEWEZEN"

  Scenario: Volledige jaarcyclus zorgtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1985-06-15    | Rotterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 30000                     | 0                         | 0                     | 0                               | 0            |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    And alle 12 maanden worden doorlopen met herberekening en betaling
    And de definitieve beschikking wordt vastgesteld
    And de vereffening wordt uitgevoerd
    Then is de toeslag status "VEREFFEND"
    And bevat de maandelijkse berekeningen 12 berekeningen
    And bevat de maandelijkse betalingen 12 betalingen
