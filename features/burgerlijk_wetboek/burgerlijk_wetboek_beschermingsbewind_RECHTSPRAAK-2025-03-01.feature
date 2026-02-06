@skip-go
Feature: Burgerlijk Wetboek Beschermingsbewind (BW 1:431-449)
  Als Rechtspraak
  Wil ik bewind-registraties beheren
  Zodat bewindvoerders hun rechthebbenden kunnen vertegenwoordigen in financiele zaken

  Background:
    Given de datum is "2025-03-01"

  # ===== Scenario's voor actief bewind =====

  Scenario: Bewindvoerder heeft actief volledig bewind voor rechthebbende
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type       | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND   | 2023-03-01   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000002"
    And bevat de output "subject_names" waarde "Bart Willems"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "BEWINDVOERDER"
    And bevat de output "valid_from_dates" waarde "2023-03-01"

  Scenario: Bewindvoerder met meerdere rechthebbenden
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type        | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND    | 2023-03-01   |             | ACTIEF |
      | 400000001         | 500000003         | Maria Hulpbehoevend| GEDEELTELIJK_BEWIND| 2024-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000002"
    And bevat de output "subject_ids" waarde "500000003"
    And bevat de output "subject_names" waarde "Bart Willems"
    And bevat de output "subject_names" waarde "Maria Hulpbehoevend"

  # ===== Scenario's voor geen bewind =====

  Scenario: Persoon is geen bewindvoerder - geen registraties
    Given een persoon met BSN "600000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND | 2023-03-01   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is niet voldaan aan de voorwaarden

  # ===== Scenario's voor beeindigd bewind =====

  Scenario: Bewind is beeindigd door datum_einde in het verleden
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND | 2023-03-01   | 2024-12-31  | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" onwaar
    And is de output "subject_ids" leeg

  Scenario: Bewind is beeindigd door status BEEINDIGD
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status    |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND | 2023-03-01   |             | BEEINDIGD |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" onwaar
    And is de output "subject_ids" leeg

  Scenario: Bewind met toekomstige einddatum is nog actief
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND | 2023-03-01   | 2026-12-31  | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000002"

  # ===== Scenario's voor verschillende bewind types =====

  Scenario: Gedeeltelijk bewind - beperkt tot specifieke goederen
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende  | bewind_type         | datum_ingang | datum_einde | status |
      | 400000001         | 500000004         | Jan Beperkt         | GEDEELTELIJK_BEWIND | 2024-06-01   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000004"
    And bevat de output "delegation_types" waarde "BEWINDVOERDER"

  Scenario: Combinatie van actief en beeindigd bewind
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type         | datum_ingang | datum_einde | status    |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND     | 2020-01-01   | 2022-12-31  | BEEINDIGD |
      | 400000001         | 500000005         | Anna Actief        | GEDEELTELIJK_BEWIND | 2024-01-01   |             | ACTIEF    |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000005"
    And bevat de output "subject_ids" niet de waarde "500000002"

  # ===== Scenario's voor bewindvoerder rechten =====

  Scenario: Bewindvoerder krijgt volledige rechten voor financiele zaken (Art. 1:441 BW)
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000002         | Bart Willems  | VOLLEDIG_BEWIND | 2023-03-01   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar

  # ===== Randgevallen =====

  Scenario: Bewind ingegaan voor peildatum is actief
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000006         | Kees Vandaag       | VOLLEDIG_BEWIND | 2024-06-15   |             | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "500000006"

  Scenario: Bewind met einddatum na peildatum is nog actief
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK bewind_registraties gegevens:
      | bsn_bewindvoerder | bsn_rechthebbende | naam_rechthebbende | bewind_type     | datum_ingang | datum_einde | status |
      | 400000001         | 500000007         | Lisa Vandaag       | VOLLEDIG_BEWIND | 2023-01-01   | 2026-06-01  | ACTIEF |
    When de burgerlijk_wetboek_beschermingsbewind wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And is de output "heeft_delegaties" waar
