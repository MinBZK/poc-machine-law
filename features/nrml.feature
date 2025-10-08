Feature: Bepalen kiesrecht Tweede Kamer
  Als burger
  Wil ik weten of ik stemrecht heb voor de Tweede Kamerverkiezingen
  Zodat ik weet of ik mag stemmen

  Background:
    Given de datum is "2025-03-15"
    And een persoon met BSN "999993653"

  Scenario: Persoon met Duitse nationaliteit heeft volgens NRML geen nederlandse nationaliteit
    Given een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    And de parameter "nationaliteit" is "DUITS"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft output heeft_nederlandse_nationaliteit met waarde False

  Scenario: Persoon met Nederlandse nationaliteit heeft volgens NRML nederlandse nationaliteit
    Given een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    And de parameter "nationaliteit" is "NEDERLANDS"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft output heeft_nederlandse_nationaliteit met waarde True

  Scenario: Persoon met Duitse nationaliteit heeft volgens NRML geen nederlandse nationaliteit via BSN
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | DUITS         | Amsterdam      | NLD           |
    And een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft output heeft_nederlandse_nationaliteit met waarde False

  Scenario: Persoon met Nederlandse nationaliteit heeft volgens NRML nederlandse nationaliteit via BSN
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And een gevraagde uitvoer "heeft_nederlandse_nationaliteit"
    When de brp_nationaliteit_nrml wordt uitgevoerd door NRML
    Then heeft output heeft_nederlandse_nationaliteit met waarde True

  Scenario: Persoon met jonge kinderen heeft volgens NRML jonge kinderen
    Given de volgende NRML personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And een gevraagde uitvoer "aantal_jonge_kinderen"
    When de kinderbijslag_nrml wordt uitgevoerd door NRML
    Then heeft output aantal_jonge_kinderen met waarde 99
