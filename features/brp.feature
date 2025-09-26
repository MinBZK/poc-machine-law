Feature: Bepalen kiesrecht Tweede Kamer
  Als burger
  Wil ik weten of ik stemrecht heb voor de Tweede Kamerverkiezingen
  Zodat ik weet of ik mag stemmen

  Background:
    Given de datum is "2025-03-15"
    And een persoon met BSN "999993653"
    And de volgende KIESRAAD verkiezingen gegevens:
      | type          | verkiezingsdatum |
      | TWEEDE_KAMER  | 2025-10-29       |

  Scenario: Persoon met Nederlandse nationaliteit heeft nederlandse nationaliteit
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    When de wet_brp_nationaliteit wordt uitgevoerd door RvIG
    Then heeft Nederlandse nationaliteit

  Scenario: Persoon met Duitse nationaliteit heeft geen nederlandse nationaliteit
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | DUITS         | Amsterdam      | NLD           |
    And een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    When de wet_brp_nationaliteit wordt uitgevoerd door RvIG
    Then heeft geen Nederlandse nationaliteit

  Scenario: Persoon met Nederlandse nationaliteit heeft volgens NRML nederlandse nationaliteit
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And een gevraagde uitvoer "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft Nederlandse nationaliteit

  Scenario: Persoon met Duitse nationaliteit heeft volgens NRML geen nederlandse nationaliteit
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | DUITS         | Amsterdam      | NLD           |
    And een gevraagde uitvoer "#/facts/f1e2d3c4-5b6a-7c8d-9e0f-1a2b3c4d5e6f/items/a2f3e4d5-6c7b-8d9e-0f1a-2b3c4d5e6f78"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft geen Nederlandse nationaliteit