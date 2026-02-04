@skip-go
@skip
Feature: Faillissementswet Curator (Fw Art. 64-71)
  Als Rechtspraak
  Wil ik faillissement-registraties beheren
  Zodat curatoren failliete boedels kunnen beheren

  Background:
    Given de datum is "2025-03-01"

  # ===== Scenario 1: Curator voor natuurlijk persoon (NATUURLIJK_PERSOON) =====

  Scenario: Curator heeft actief faillissement natuurlijk persoon
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      |             | ACTIEF |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000006"
    And bevat de output "subject_names" waarde "Boedel Henk Visser"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "CURATOR_BOEDEL"
    And bevat de output "valid_from_dates" waarde "2024-03-15"

  # ===== Scenario 2: Curator voor rechtspersoon (RECHTSPERSOON) =====

  Scenario: Curator heeft actief faillissement rechtspersoon
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000004   | 87654321        | Failliete BV      | RECHTSPERSOON     | F.10/24/456        | 2024-06-01      |             | ACTIEF |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "87654321"
    And bevat de output "subject_names" waarde "Boedel Failliete BV"
    And bevat de output "subject_types" waarde "BUSINESS"
    And bevat de output "delegation_types" waarde "CURATOR_BOEDEL"
    And bevat de output "valid_from_dates" waarde "2024-06-01"

  # ===== Scenario 3: Meerdere faillissementen per curator =====

  Scenario: Curator beheert meerdere failliete boedels
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      |             | ACTIEF |
      | 400000004   | 87654321        | Failliete BV      | RECHTSPERSOON      | F.10/24/456        | 2024-06-01      |             | ACTIEF |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000006"
    And bevat de output "subject_ids" waarde "87654321"
    And bevat de output "subject_names" waarde "Boedel Henk Visser"
    And bevat de output "subject_names" waarde "Boedel Failliete BV"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "subject_types" waarde "BUSINESS"

  # ===== Scenario 4: Opgeheven faillissement =====

  Scenario: Curator met opgeheven faillissement heeft geen actieve delegatie
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status    |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      | 2025-01-15  | OPGEHEVEN |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # ===== Scenario 5: Persoon is geen faillissementscurator =====

  Scenario: Persoon zonder curator-registraties heeft geen delegaties
    Given een persoon met BSN "999993653"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      |             | ACTIEF |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # ===== Scenario 6: Mix van actieve en opgeheven faillissementen =====

  Scenario: Curator met mix van actieve en opgeheven faillissementen
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status    |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      | 2025-01-15  | OPGEHEVEN |
      | 400000004   | 87654321        | Failliete BV      | RECHTSPERSOON      | F.10/24/456        | 2024-06-01      |             | ACTIEF    |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "87654321"
    And bevat de output "subject_ids" niet de waarde "500000006"
    And bevat de output "subject_names" waarde "Boedel Failliete BV"
    And bevat de output "subject_names" niet de waarde "Boedel Henk Visser"

  # ===== Scenario 7: Rechten van de curator =====

  Scenario: Curator krijgt juiste rechten voor boedelbeheer
    Given een persoon met BSN "400000004"
    And de volgende RECHTSPRAAK faillissement_registraties gegevens:
      | bsn_curator | gefailleerde_id | gefailleerde_naam | gefailleerde_type  | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000004   | 500000006       | Henk Visser     | NATUURLIJK_PERSOON | F.10/24/123        | 2024-03-15      |             | ACTIEF |
    When de faillissementswet_curator wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And bevat de output "permissions" waarde "["LEZEN", "CLAIMS_INDIENEN", "BESLUITEN_ONTVANGEN"]"
