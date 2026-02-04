@skip-go
@skip
Feature: Burgerlijk Wetboek Mentorschap (BW 1:450-462)
  Als Rechtspraak
  Wil ik mentorschap-registraties beheren
  Zodat mentors beslissingen kunnen nemen over verzorging, verpleging en behandeling

  # Mentorschap is voor niet-vermogensrechtelijke zaken (zorg, behandeling, begeleiding).
  # De betrokkene blijft handelingsbekwaam - alleen de mentor neemt beslissingen over zorg.
  # Data komt uit het Centraal Curatele- en Bewindregister (CCBR) bij de Rechtspraak.

  Background:
    Given de datum is "2025-03-01"

  Scenario: Mentor heeft actief mentorschap
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   |             | ACTIEF |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000003"
    And bevat de output "subject_names" waarde "Willem Jansen"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "MENTOR"
    And bevat de output "valid_from_dates" waarde "2023-06-15"

  Scenario: Persoon is geen mentor
    Given een persoon met BSN "999999999"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   |             | ACTIEF |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg
    And is de output "subject_names" leeg

  Scenario: Beeindigd mentorschap geeft geen actieve delegaties
    # Persoon staat geregistreerd in CCBR, maar mentorschap is beeindigd
    # Requirements zijn voldaan (persoon is bekend in register), maar heeft_delegaties is false
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status    |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   | 2024-12-31  | BEEINDIGD |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Mentor met meerdere betrokkenen
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   |             | ACTIEF |
      | 400000001   | 500000004      | Anna Hulpbehoevend  | 2024-01-01   |             | ACTIEF |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000003"
    And bevat de output "subject_ids" waarde "500000004"
    And bevat de output "subject_names" waarde "Willem Jansen"
    And bevat de output "subject_names" waarde "Anna Hulpbehoevend"

  Scenario: Mentor met mix van actief en beeindigd mentorschap
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status    |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   |             | ACTIEF    |
      | 400000001   | 500000004      | Anna Hulpbehoevend  | 2022-01-01   | 2024-06-30  | BEEINDIGD |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000003"
    And bevat de output "subject_ids" niet de waarde "500000004"
    And bevat de output "subject_names" waarde "Willem Jansen"
    And bevat de output "subject_names" niet de waarde "Anna Hulpbehoevend"

  Scenario: Mentorschap met einddatum in de toekomst is nog actief
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK mentorschap_registraties gegevens:
      | bsn_mentor  | bsn_betrokkene | naam_betrokkene     | datum_ingang | datum_einde | status |
      | 400000001   | 500000003      | Willem Jansen | 2023-06-15   | 2026-12-31  | ACTIEF |
    When de burgerlijk_wetboek_mentorschap wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000003"
