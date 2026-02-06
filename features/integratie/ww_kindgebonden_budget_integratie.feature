Feature: Integratie WW en Kindgebonden Budget
  Als alleenstaande ouder met WW-uitkering
  Wil ik weten hoe mijn WW-inkomen mijn kindgebonden budget beïnvloedt
  Zodat ik mijn financiële situatie begrijp

  Background:
    Given de datum is "2025-02-01"

  Scenario: Alleenstaande ouder met WW ontvangt kindgebonden budget + ALO-kop
    Given een persoon met BSN "300000001"
    # Persoons- en relatiegegevens
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 300000001 | 1988-06-15    | NEDERLANDS   | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 300000001 | GEEN              | null        |
    # WW gegevens
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 300000001 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 300000001 | 40.0                    | 0.0                   | 32                | 8                     | 3600000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 300000001 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 300000001 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 300000001 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 300000001 | false          |
    # Kindgebonden budget gegevens
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 300000001 | 1               | [6]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 300000001 | 3000000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 300000001 | 4000000  |
    # Tests
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW duur "8" maanden
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then is voldaan aan de voorwaarden
    And is het ALO-kop bedrag "€3.480,00"
    And is het totale kindgebonden budget ongeveer "€5.870,00" per jaar

  Scenario: WW-inkomen zorgt voor afbouw kindgebonden budget
    Given een persoon met BSN "300000002"
    # Persoons- en relatiegegevens
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 300000002 | 1985-03-22    | NEDERLANDS   | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 300000002 | GEEN              | null        |
    # WW gegevens - hoog jaarloon
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 300000002 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 300000002 | 40.0                    | 0.0                   | 35                | 12                    | 10000000  |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 300000002 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 300000002 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 300000002 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 300000002 | false          |
    # Kindgebonden budget gegevens
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 300000002 | 2               | [8, 11]             | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 300000002 | 5800000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 300000002 | 8000000  |
    # Tests
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW uitkering maximaal omdat het dagloon gemaximeerd is
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then is voldaan aan de voorwaarden
    And is het ALO-kop bedrag "€3.480,00"
    And is het kindgebonden budget lager door hoog inkomen

  Scenario: Van paar naar alleenstaand door werkloosheid - ALO-kop wordt actief
    Given een persoon met BSN "300000003"
    # Persoons- en relatiegegevens - eerst gehuwd, dan gescheiden
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 300000003 | 1990-09-10    | NEDERLANDS   | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 300000003 | GEEN              | null        |
    # WW gegevens
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 300000003 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 300000003 | 36.0                    | 0.0                   | 30                | 7                     | 3200000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 300000003 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 300000003 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 300000003 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 300000003 | false          |
    # Kindgebonden budget gegevens - nu alleenstaand
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 300000003 | 1               | [9]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 300000003 | 2650000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 300000003 | 3500000  |
    # Tests
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW duur "7" maanden
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then is voldaan aan de voorwaarden
    And is het ALO-kop bedrag "€3.480,00"
    And ontvangt de persoon de ALO-kop omdat deze alleenstaand is

  Scenario: Laag WW-inkomen met meerdere kinderen en ALO-kop
    Given een persoon met BSN "300000004"
    # Persoons- en relatiegegevens
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 300000004 | 1987-12-28    | NEDERLANDS   | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 300000004 | GEEN              | null        |
    # WW gegevens - laag inkomen
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 300000004 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 300000004 | 24.0                    | 0.0                   | 28                | 5                     | 2400000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 300000004 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 300000004 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 300000004 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 300000004 | false          |
    # Kindgebonden budget gegevens - 3 kinderen
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 300000004 | 3               | [5, 13, 16]         | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 300000004 | 1980000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 300000004 | 2500000  |
    # Tests
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW duur "5" maanden
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then is voldaan aan de voorwaarden
    And is het ALO-kop bedrag "€3.480,00"
    And is het kindgebonden budget hoog door laag inkomen en meerdere kinderen
    And ontvangt de persoon extra bedragen voor kinderen 12+ en 16+

  Scenario: Geen WW maar wel kindgebonden budget
    Given een persoon met BSN "300000005"
    # Persoons- en relatiegegevens
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 300000005 | 1993-05-03    | NEDERLANDS   | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 300000005 | GEEN              | null        |
    # WW gegevens - te weinig gewerkt
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 300000005 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 300000005 | 16.0                    | 0.0                   | 18                | 2                     | 1800000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 300000005 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 300000005 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 300000005 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 300000005 | false          |
    # Kindgebonden budget gegevens
    And de volgende SVB algemene_kinderbijslagwet gegevens:
      | ouder_bsn | aantal_kinderen | kinderen_leeftijden | ontvangt_kinderbijslag |
      | 300000005 | 1               | [3]                 | true                   |
    And de volgende UWV uwv_toetsingsinkomen gegevens:
      | bsn       | toetsingsinkomen |
      | 300000005 | 1500000          |
    And de volgende BELASTINGDIENST belastingdienst_vermogen gegevens:
      | bsn       | vermogen |
      | 300000005 | 1200000  |
    # Tests
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon geen recht op WW
    When de wet_op_het_kindgebonden_budget wordt uitgevoerd door TOESLAGEN
    Then is voldaan aan de voorwaarden
    And is het ALO-kop bedrag "€3.480,00"
    And is het kindgebonden budget maximaal door laag inkomen
