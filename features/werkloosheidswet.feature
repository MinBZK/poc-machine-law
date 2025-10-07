Feature: Berekening Werkloosheidsuitkering (WW)
  Als werknemer
  Wil ik weten of ik recht heb op WW
  Zodat ik mijn financiële situatie kan inschatten

  Background:
    Given de datum is "2025-02-01"

  Scenario: Werknemer met voldoende arbeidsverleden krijgt WW
    Given een persoon met BSN "100000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000001 | 1985-05-15    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000001 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000001 | 40.0                    | 0.0                   | 30                | 10                    | 4200000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000001 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000001 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000001 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000001 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW duur "10" maanden
    And is de WW uitkering per maand ongeveer "€2.625,00"

  Scenario: Werknemer met te weinig arbeidsverleden krijgt geen WW
    Given een persoon met BSN "100000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000002 | 1998-03-20    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000002 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000002 | 32.0                    | 0.0                   | 20                | 1                     | 2800000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000002 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000002 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000002 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000002 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon geen recht op WW

  Scenario: Werknemer boven AOW-leeftijd krijgt geen WW
    Given een persoon met BSN "100000003"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000003 | 1955-08-10    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000003 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000003 | 40.0                    | 0.0                   | 35                | 40                    | 5000000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000003 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000003 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000003 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000003 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon geen recht op WW

  Scenario: Werknemer met ziektewet krijgt geen WW
    Given een persoon met BSN "100000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000004 | 1990-11-25    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000004 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000004 | 36.0                    | 0.0                   | 32                | 8                     | 3800000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000004 | true                      |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000004 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000004 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000004 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon geen recht op WW

  Scenario: Maximale WW-uitkering bij hoog inkomen
    Given een persoon met BSN "100000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000005 | 1980-02-14    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000005 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000005 | 40.0                    | 0.0                   | 36                | 15                    | 10000000  |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000005 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000005 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000005 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000005 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW uitkering per maand maximaal "€4.741,55"
    And is de WW duur "12" maanden

  Scenario: Deeltijd werkloosheid (minimaal 5 uur minder)
    Given een persoon met BSN "100000006"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | land_verblijf |
      | 100000006 | 1992-07-08    | NEDERLANDS   | NEDERLAND     |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 100000006 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon  |
      | 100000006 | 32.0                    | 26.0                  | 28                | 6                     | 3400000   |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 100000006 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 100000006 | false               |
    And de volgende IND vreemdelingenwet gegevens:
      | bsn       | verblijfsvergunning_type |
      | 100000006 | null                     |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 100000006 | false          |
    When de werkloosheidswet wordt uitgevoerd door UWV
    Then heeft de persoon recht op WW
    And is de WW duur "6" maanden
