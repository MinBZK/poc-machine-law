@ui
Feature: Burgerlijk Wetboek Handelingsonbekwaamheid (BW 1:378-391)
  Als RECHTSPRAAK
  Wil ik bepalen of een persoon handelingsonbekwaam is
  Zodat hun rechten correct worden beperkt

  Background:
    Given de datum is "2025-03-01"

  # ===== Curatele =====
  # Art. 1:381 BW - curandus is handelingsonbekwaam

  Scenario: Persoon onder curatele is handelingsonbekwaam
    # Art. 1:381 lid 1 BW: curandus kan geen rechtshandelingen zelfstandig verrichten
    Given een persoon met BSN "500000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "is_onder_curatele" waarde "true"
    And heeft de output "is_handelingsonbekwaam" waarde "true"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" niet de waarde "CLAIMS_INDIENEN"
    And bevat de output "base_permissions" niet de waarde "BESLUITEN_ONTVANGEN"

  Scenario: Persoon zonder curatele is handelingsbekwaam
    # Geen curatele registratie = volledige handelingsbekwaamheid
    Given een persoon met BSN "999993653"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "is_onder_curatele" waarde "false"
    And heeft de output "is_handelingsonbekwaam" waarde "false"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"
    And bevat de output "base_permissions" waarde "BESLUITEN_ONTVANGEN"

  Scenario: Beeindigde curatele - persoon is weer handelingsbekwaam
    # Art. 1:389 BW: curatele kan worden opgeheven
    Given een persoon met BSN "500000009"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus | datum_ingang | datum_einde | status    |
      | 400100007   | 500000009    | Jan de Boer   | 2020-01-01   | 2023-12-31  | BEEINDIGD |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "is_onder_curatele" waarde "false"
    And heeft de output "is_handelingsonbekwaam" waarde "false"
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"

  Scenario: Curatele met einddatum in verleden - persoon is weer handelingsbekwaam
    # Art. 1:389 BW: curatele eindigt na opheffing
    Given een persoon met BSN "500000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2020-01-01   | 2024-12-31  | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "is_onder_curatele" waarde "false"
    And heeft de output "is_handelingsonbekwaam" waarde "false"
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"

  Scenario: Curatele met toekomstige einddatum - nog handelingsonbekwaam
    # Curatele blijft actief totdat einddatum bereikt is
    Given een persoon met BSN "500000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2022-01-15   | 2026-12-31  | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "is_onder_curatele" waarde "true"
    And heeft de output "is_handelingsonbekwaam" waarde "true"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" niet de waarde "CLAIMS_INDIENEN"

  # ===== SELF Delegatie =====
  # Handelingsonbekwamen hebben beperkte SELF permissions

  Scenario: Handelingsonbekwame heeft SELF delegatie met alleen leesrecht
    Given een persoon met BSN "500000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000001"
    And bevat de output "subject_types" waarde "SELF"
    And bevat de output "delegation_types" waarde "EIGEN_ZAKEN"
    And bevat de output "permissions" waarde "['LEZEN']"

  Scenario: Handelingsbekwame heeft SELF delegatie met volledige rechten
    Given een persoon met BSN "999993653"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus  | datum_ingang | datum_einde | status |
      | 400100001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_handelingsonbekwaamheid wordt uitgevoerd door RECHTSPRAAK
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "999993653"
    And bevat de output "permissions" waarde "['LEZEN', 'CLAIMS_INDIENEN', 'BESLUITEN_ONTVANGEN']"
