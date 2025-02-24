Feature: Berekening Huurtoeslag
  Als burger
  Wil ik weten of ik recht heb op huurtoeslag
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given de datum is "2025-02-01"
    And een persoon met BSN "999993653"

  Scenario: Persoon onder 18 heeft geen recht op huurtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 2008-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN             | null        |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then is niet voldaan aan de voorwaarden

  Scenario: Kind onder 23 met inkomen onder vrijstellingsbedrag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993654 | 2005-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN             | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 999993653 | 25000                     |
      | 999993654 | 5000                      |
    And met een kale huur 600 en servicekosten 45
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op huurtoeslag
    #And is het toetsingsinkomen "25000" euro
    # Toelichting: Inkomen kind (5000) < vrijstelling (5432), telt dus niet mee

  Scenario: Kind onder 23 met hoog vermogen (telt niet mee)
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993654 | 2003-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN             | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 999993653 | 25000                     |
      | 999993654 | 6000                      |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen |
      | 999993653 | 10000     | 0           |
      | 999993654 | 200000    | 0           |
    And de volgende huurgegevens:
      | kale_huur | servicekosten |
      | 600       | 45            |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op huurtoeslag
    And is het toetsingsinkomen "25568" euro
    # Toelichting: Vermogen kind (200.000) telt niet mee want boven 18
    # Inkomen: 25000 + (6000 - 5432) = 25568
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993654 | 2005-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993655 | 2006-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN             | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 999993653 | 25000                     |
      | 999993654 | 8000                      |
      | 999993655 | 7000                      |
    And de volgende huurgegevens:
      | kale_huur | servicekosten |
      | 600       | 50           |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op huurtoeslag
    And is het toetsingsinkomen "29136" euro
    # Berekening: 25000 + (8000 - 5432) + (7000 - 5432) = 29136

  Scenario: Gezin met twee kinderen waarvan één met vermogen onder 18
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993654 | 1992-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993655 | 2008-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
      | 999993656 | 2010-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type          | partner_bsn |
      | 999993653 | GEREGISTREERD_PARTNERSCHAP | 999993654   |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 999993653 | 25000                     |
      | 999993654 | 25000                     |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen |
      | 999993653 | 10000     | 0           |
      | 999993654 | 10000     | 0           |
      | 999993655 | 40000     | 0           |
      | 999993656 | 5000      | 0           |
    And de volgende huurgegevens:
      | kale_huur | servicekosten |
      | 700       | 45           |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then is niet voldaan aan de voorwaarden
    # Toelichting: Vermogen kind onder 18 (40.000) telt mee bij ouders
    # Totaal vermogen: 10.000 + 10.000 + 40.000 + 5.000 = 65.000 > vermogensgrens

  Scenario: Huur boven maximale servicekosten
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 999993653 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN             | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 999993653 | 25000                     |
    And de volgende huurgegevens:
      | kale_huur | servicekosten |
      | 600       | 100          |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op huurtoeslag
    And is de rekenhuur "648" euro
    # Toelichting: 600 + 48 (max servicekosten) = 648
