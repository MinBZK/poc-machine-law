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
      | bsn       | status            |
      | 999993800 | WILSONBEKWAAM     |
    And de volgende JenV vertegenwoordiging gegevens:
      | bsn       | vertegenwoordigers              | type          |
      | 999993800 | [{"bsn": "999993801", "naam": "Jan Vertegenwoordiger"}] | CURATELE      |
    When de wet_vertegenwoordiging wordt uitgevoerd door JenV
    Then is "is_wilsonbekwaam" gelijk aan "true"
    And is "has_legal_representative" gelijk aan "true"

  Scenario: Vertegenwoordiger kan namens een wilsonbekwame persoon handelen
    Given een persoon met BSN "999993801"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | nationaliteit |
      | 999993800 | 1960-05-15    | Amsterdam      | NEDERLANDS    |
      | 999993801 | 1965-03-20    | Amsterdam      | NEDERLANDS    |
    And de volgende JenV vertegenwoordiging gegevens:
      | bsn       | vertegenwoordigt_voor                                                                | type          |
      | 999993801 | [{"bsn": "999993800", "naam": "Wim Wilsonbekwaam", "type": "CURATELE"}] | CURATELE      |
    When de wet_vertegenwoordiging wordt uitgevoerd door JenV
    Then is "is_representative_for" gelijk aan "true"
    And is "representing_bsns" gelijk aan ["999993800"]

  Scenario: Ouder kan handelen namens minderjarig kind
    Given een persoon met BSN "999993901"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | nationaliteit |
      | 999993901 | 1980-05-15    | Amsterdam      | NEDERLANDS    |
      | 999993902 | 2015-03-20    | Amsterdam      | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | children |
      | 999993901 | [{"bsn": "999993902", "geboortedatum": "2015-03-20", "naam": "Kind Minderjarig"}] |
    When de wet_vertegenwoordiging wordt uitgevoerd door JenV
    Then is "parent_of_minor" gelijk aan "true"
    And is "minor_children" van lengte 1
