Feature: Wettelijke Vertegenwoordiging
  Als burger met wilsonbekwaamheid
  Wil ik dat mijn wettelijke vertegenwoordiger namens mij kan handelen
  Zodat mijn zaken goed worden behartigd

  Background:
    Given de datum is "2024-06-01"

  Scenario: Wilsonbekwame persoon heeft een wettelijke vertegenwoordiger
    Given een persoon met BSN "999993800"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | nationaliteit |
      | 999993800 | 1960-05-15    | Amsterdam      | NEDERLANDS    |
      | 999993801 | 1965-03-20    | Amsterdam      | NEDERLANDS    |
    And de volgende JenV wilsbekwaamheid gegevens:
      | bsn       | status        |
      | 999993800 | WILSONBEKWAAM |
    And de volgende JenV vertegenwoordiging gegevens:
      | bsn       | vertegenwoordigers                                      | type     |
      | 999993800 | [{"bsn": "999993801", "naam": "Jan Vertegenwoordiger"}] | CURATELE |
    When de wet_vertegenwoordiging wordt uitgevoerd door JenV
    Then is "is_wilsonbekwaam" gelijk aan "true"
    And is "has_legal_representative" gelijk aan "true"
