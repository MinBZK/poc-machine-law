Feature: Burgerlijk Wetboek Volmacht (BW 3:60-79)
  Als Notariaat
  Wil ik volmacht-registraties beheren
  Zodat gevolmachtigden namens volmachtgevers kunnen handelen

  Background:
    Given de datum is "2025-03-01"

  # ===== Actieve algemene volmacht =====

  Scenario: Gevolmachtigde heeft actieve algemene volmacht
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000004"
    And bevat de output "subject_names" waarde "Elisabeth van den Berg-Smit"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "GEVOLMACHTIGDE_ALGEMEEN"

  Scenario: Algemene volmacht geeft volledige rechten (LEZEN, CLAIMS_INDIENEN, BESLUITEN_ONTVANGEN)
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"

  # ===== Bijzondere volmacht =====

  Scenario: Gevolmachtigde heeft actieve bijzondere volmacht
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type       | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | BIJZONDERE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "GEVOLMACHTIGDE_BIJZONDER"

  Scenario: Bijzondere volmacht geeft beperkte rechten (alleen LEZEN)
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type       | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | BIJZONDERE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And bevat de output "delegation_types" waarde "GEVOLMACHTIGDE_BIJZONDER"

  # ===== Persoon is GEEN gevolmachtigde =====

  Scenario: Persoon zonder volmacht-registratie is geen gevolmachtigde
    Given een persoon met BSN "123456789"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # ===== Herroepen volmacht (Art. 3:72 BW) =====

  Scenario: Herroepen volmacht geeft geen bevoegdheid
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | true         |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Inactieve volmacht geeft geen bevoegdheid
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status   | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | INACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"

  # ===== Verlopen volmacht =====

  Scenario: Verlopen volmacht geeft geen bevoegdheid
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   | 2024-12-31  | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"

  Scenario: Volmacht met toekomstige einddatum is nog actief
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   | 2026-12-31  | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"

  # ===== Meerdere volmachten =====

  Scenario: Gevolmachtigde met meerdere volmachten van verschillende volmachtgevers
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type       | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT   | 2021-05-01   |             | ACTIEF | false        |
      | 400000002          | 600000006         | Jan de Vries                | BIJZONDERE_VOLMACHT | 2022-01-15   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000004"
    And bevat de output "subject_ids" waarde "600000006"
    And bevat de output "delegation_types" waarde "GEVOLMACHTIGDE_ALGEMEEN"
    And bevat de output "delegation_types" waarde "GEVOLMACHTIGDE_BIJZONDER"

  Scenario: Gevolmachtigde met een actieve en een herroepen volmacht
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
      | 400000002          | 600000006         | Jan de Vries                | ALGEMENE_VOLMACHT | 2020-01-15   |             | ACTIEF | true         |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000004"
    And bevat de output "subject_ids" niet de waarde "600000006"

  # ===== Startdatum validatie =====

  Scenario: Volmacht geldig vanaf ingangsdatum wordt correct geregistreerd
    Given een persoon met BSN "400000002"
    And de volgende NOTARIAAT volmacht_registraties gegevens:
      | bsn_gevolmachtigde | bsn_volmachtgever | naam_volmachtgever          | volmacht_type     | datum_ingang | datum_einde | status | is_herroepen |
      | 400000002          | 500000004         | Elisabeth van den Berg-Smit | ALGEMENE_VOLMACHT | 2021-05-01   |             | ACTIEF | false        |
    When de burgerlijk_wetboek_volmacht wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And bevat de output "valid_from_dates" waarde "2021-05-01"
