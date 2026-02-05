@skip-go
Feature: Bepalen adviesplicht ICT-projecten
  Als verantwoordelijk ministerie of organisatie
  Wil ik weten of mijn ICT-project onder de adviesplicht valt
  Zodat ik tijdig advies kan aanvragen bij het Adviescollege ICT-toetsing

  Background:
    Given de datum is "2024-10-01"

  Scenario: ICT-project ministerie van €10 miljoen valt onder adviesplicht
    Given een ICT-project met ID "PROJ-001"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-001   | 1000000000    | MINISTERIE       | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project onder adviesplicht
    And zijn de project kosten "10000000.00" euro

  Scenario: ICT-project ZBO van €6 miljoen valt onder adviesplicht
    Given een ICT-project met ID "PROJ-002"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-002   | 600000000     | ZBO              | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project onder adviesplicht
    And zijn de project kosten "6000000.00" euro

  Scenario: ICT-project politie van €5 miljoen valt precies op drempel
    Given een ICT-project met ID "PROJ-003"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-003   | 500000000     | POLITIE          | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project onder adviesplicht
    And zijn de project kosten "5000000.00" euro

  Scenario: ICT-project ministerie van €4 miljoen valt niet onder adviesplicht
    Given een ICT-project met ID "PROJ-004"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-004   | 400000000     | MINISTERIE       | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project niet onder adviesplicht
    And zijn de project kosten "4000000.00" euro

  Scenario: Wapensysteem defensie van €20 miljoen valt niet onder adviesplicht
    Given een ICT-project met ID "PROJ-005"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-005   | 2000000000    | MINISTERIE       | WAPENSYSTEEM |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project niet onder adviesplicht
    And zijn de project kosten "20000000.00" euro

  Scenario: ICT-project rechterlijke macht van €8 miljoen valt onder adviesplicht
    Given een ICT-project met ID "PROJ-006"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type  | project_type |
      | PROJ-006   | 800000000     | RECHTERLIJKE_MACHT | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project onder adviesplicht
    And zijn de project kosten "8000000.00" euro

  Scenario: ICT-project gemeente van €10 miljoen valt niet onder adviesplicht
    Given een ICT-project met ID "PROJ-007"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-007   | 1000000000    | GEMEENTE         | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project niet onder adviesplicht
    And zijn de project kosten "10000000.00" euro

  Scenario: Complex ICT-project ZBO met hoge kosten valt onder adviesplicht
    Given een ICT-project met ID "PROJ-008"
    And de volgende ACICT ict_projecten gegevens:
      | project_id | totale_kosten | organisatie_type | project_type |
      | PROJ-008   | 5000000000    | ZBO              | REGULIER     |
    When de wet_adviescollege_ict_toetsing wordt uitgevoerd door ACICT
    Then valt het project onder adviesplicht
    And zijn de project kosten "50000000.00" euro
