Feature: Bepalen kiesrecht Tweede Kamer (v0.1.7)
  Als burger
  Wil ik weten of ik stemrecht heb voor de Tweede Kamerverkiezingen
  Zodat ik weet of ik mag stemmen

  Background:
    Given de datum is "2025-03-15"
    And een persoon met BSN "999993653"
    And de volgende verkiezingen gegevens:
      | type          | verkiezingsdatum |
      | TWEEDE_KAMER  | 2025-10-29       |

  Scenario: Persoon met Nederlandse nationaliteit van 18+ mag stemmen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2006-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    When de kieswet v0.1.7 wordt uitgevoerd
    Then heeft de persoon stemrecht

  Scenario: Persoon zonder Nederlandse nationaliteit mag niet stemmen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | DUITS         | Amsterdam      | NLD           |
    When de kieswet v0.1.7 wordt uitgevoerd
    Then heeft de persoon geen stemrecht

  Scenario: Persoon onder 18 mag niet stemmen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 2008-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    When de kieswet v0.1.7 wordt uitgevoerd
    Then heeft de persoon geen stemrecht

  Scenario: Persoon met uitsluiting kiesrecht mag niet stemmen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And de volgende JUSTID ontzettingen gegevens:
      | bsn       | type      | startdatum | einddatum  |
      | 999993653 | KIESRECHT | 2023-01-01 | 2024-01-01 |
      | 999993653 | KIESRECHT | 2024-06-01 | 2025-12-01 |
    When de kieswet v0.1.7 wordt uitgevoerd
    Then heeft de persoon geen stemrecht

  Scenario: Gedetineerde persoon mag wel stemmen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | NEDERLANDS    | Amsterdam      | NLD           |
    And de volgende JUSTID ontzettingen gegevens:
      | bsn       | type      | startdatum | einddatum  |
      | 999993653 | KIESRECHT | 2023-01-01 | 2024-01-01 |
    And de volgende DJI detenties gegevens:
      | bsn       | status     |
      | 999993653 | INGESLOTEN |
    When de kieswet v0.1.7 wordt uitgevoerd
    Then heeft de persoon stemrecht
