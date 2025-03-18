Feature: Bepalen recht op bijstand Amsterdam
  Als inwoner van Amsterdam
  Wil ik weten of ik recht heb op bijstand
  Zodat ik weet of ik financiële ondersteuning kan krijgen

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2025 | 20.5           |
    And de volgende IND verblijfsvergunningen gegevens:
      | bsn       | type                     | status   | ingangsdatum | einddatum |
      | 999993653 | ONBEPAALDE_TIJD_REGULIER | VERLEEND | 2015-01-01   | null      |

  Scenario: Standaard bijstandsuitkering voor alleenstaande
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1990-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 0                         | 0                         | 0                     | 0                               | 0            |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000      | 0           | 0              | 0        |
    And de volgende RvIG verblijfplaats gegevens:
      | bsn       | straat       | huisnummer | postcode | woonplaats | type      |
      | 999993653 | Kalverstraat | 1          | 1012NX   | Amsterdam  | WOONADRES |
    And de volgende GEMEENTE_AMSTERDAM werk_en_re_integratie gegevens:
      | bsn       | arbeidsvermogen | re_integratie_traject |
      | 999993653 | VOLLEDIG        | Werkstage             |
    When de participatiewet/bijstand wordt uitgevoerd door GEMEENTE_AMSTERDAM
    Then is voldaan aan de voorwaarden
    And is het bijstandsuitkeringsbedrag "1089.00" euro
