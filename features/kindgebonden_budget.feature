Feature: Berekening Kindgebonden Budget met ALO-kop
  Als ouder
  Wil ik weten of ik recht heb op kindgebonden budget
  Zodat ik financiële ondersteuning krijg voor mijn kinderen

  Background:
    Given de datum is "2025-02-01"

  Scenario: Alleenstaande ouder met 1 kind krijgt basisbedrag + ALO-kop
    Given een persoon met BSN "200000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000001 | 1988-04-12    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000001 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000001 | 1               | [5]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000001 | 2500000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000001 | 5000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het ALO-kop bedrag "€3.480,00"
    And is het kindgebonden budget ongeveer "€5.991,00" per jaar

  Scenario: Paar met 2 kinderen krijgt aangepast bedrag zonder ALO-kop
    Given een persoon met BSN "200000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000002 | 1985-09-22    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000002 | HUWELIJK          | 200000003   |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000002 | 2               | [7, 10]             | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000002 | 3500000          |
      | 200000003 | 3000000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen         |
      | 200000002 | 8000000          |
      | 200000003 | 7000000          |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het ALO-kop bedrag "€0,00"
    And is het kindgebonden budget ongeveer "€5.022,00" per jaar

  Scenario: Alleenstaande met inkomen boven grens krijgt geen kindgebonden budget
    Given een persoon met BSN "200000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000004 | 1982-11-30    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000004 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000004 | 1               | [8]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000004 | 12000000         |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000004 | 5000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het kindgebonden budget ongeveer "€0,00" per jaar

  Scenario: Alleenstaande met kind krijgt basisbedrag
    Given een persoon met BSN "200000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000005 | 1990-01-15    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000005 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000005 | 1               | [10]                | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000005 | 2200000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000005 | 3000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het kindgebonden budget ongeveer "€5.991,00" per jaar

  Scenario: Alleenstaande met kind en hoger inkomen
    Given een persoon met BSN "200000006"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000006 | 1987-06-20    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000006 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000006 | 1               | [8]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000006 | 2400000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000006 | 4000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het kindgebonden budget ongeveer "€5.991,00" per jaar

  Scenario: Geen kinderbijslag betekent geen kindgebonden budget
    Given een persoon met BSN "200000007"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000007 | 1995-03-08    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000007 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000007 | 0               | []                  | false                  |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000007 | 2000000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000007 | 2000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon geen recht op kindgebonden budget

  Scenario: Vermogen boven grens betekent geen kindgebonden budget
    Given een persoon met BSN "200000008"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000008 | 1983-12-05    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000008 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000008 | 1               | [6]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000008 | 2500000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen  |
      | 200000008 | 15000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon geen recht op kindgebonden budget

  Scenario: Alleenstaande met laag inkomen krijgt maximaal kindgebonden budget
    Given een persoon met BSN "200000009"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 200000009 | 1991-08-18    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 200000009 | GEEN              | null        |
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 200000009 | 1               | [4]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 200000009 | 1500000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 200000009 | 1000000  |
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then heeft de persoon recht op kindgebonden budget
    And is het ALO-kop bedrag "€3.480,00"
    And is het kindgebonden budget ongeveer "€5.991,00" per jaar
