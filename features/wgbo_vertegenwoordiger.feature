Feature: WGBO Vertegenwoordiger (BW 7:465)
  Als RvIG
  Wil ik medische vertegenwoordigingsrelaties bepalen
  Zodat wilsonbekwame patienten vertegenwoordigd kunnen worden bij medische beslissingen

  Background:
    Given de datum is "2025-03-01"

  # ===== Scenario 1: Echtgenoot als WGBO vertegenwoordiger =====

  Scenario: Echtgenoot is WGBO vertegenwoordiger voor wilsonbekwame partner
    Given een persoon met BSN "400000006"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient        | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000006      | 500000008   | Gerda Groen-van Dijk | ECHTGENOOT   | true             | 2024-01-10              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000008"
    And bevat de output "subject_names" waarde "Gerda Groen-van Dijk"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_PARTNER"
    And bevat de output "subject_types" waarde "CITIZEN"

  Scenario: Geregistreerd partner is WGBO vertegenwoordiger voor wilsonbekwame partner
    Given een persoon met BSN "400000010"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient    | relatie_type         | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000010      | 500000010   | Jan Geregistreerd | GEREGISTREERD_PARTNER | true             | 2024-02-15              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000010"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_PARTNER"

  # ===== Scenario 2: Patient is wilsbekwaam - geen vertegenwoordiging nodig =====

  Scenario: Patient is wilsbekwaam - geen WGBO vertegenwoordiging
    Given een persoon met BSN "400000011"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient   | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000011      | 500000011   | Henk Wilsbekwaam | ECHTGENOOT   | false            |                         |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # ===== Scenario 3: Hierarchie van vertegenwoordigers (Art. 7:465 lid 3 BW) =====
  # Volgorde: curator/mentor > schriftelijke volmacht > echtgenoot/partner > ouder/kind/broer/zus

  Scenario: Ouder is WGBO vertegenwoordiger voor wilsonbekwaam meerderjarig kind
    Given een persoon met BSN "400000012"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient     | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000012      | 500000012   | Marie Dochter    | OUDER        | true             | 2023-06-01              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_OUDER"

  Scenario: Kind is WGBO vertegenwoordiger voor wilsonbekwame ouder
    Given een persoon met BSN "400000013"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient   | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000013      | 500000013   | Piet Vader     | KIND         | true             | 2024-03-20              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_KIND"

  Scenario: Broer is WGBO vertegenwoordiger voor wilsonbekwame zus
    Given een persoon met BSN "400000014"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000014      | 500000014   | Anna Zus     | BROER        | true             | 2024-05-10              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_SIBLING"

  Scenario: Zus is WGBO vertegenwoordiger voor wilsonbekwame broer
    Given een persoon met BSN "400000015"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000015      | 500000015   | Klaas Broer  | ZUS          | true             | 2024-04-01              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_SIBLING"

  Scenario: Levensgezel is WGBO vertegenwoordiger (gelijk aan partner in hierarchie)
    Given een persoon met BSN "400000016"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient    | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000016      | 500000016   | Sara Levensgezel | LEVENSGEZEL  | true             | 2024-06-15              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "WGBO_VERTEGENWOORDIGER_PARTNER"

  # ===== Scenario 4: Geen familierelatie - geen delegatie =====

  Scenario: Persoon zonder familierelatie met wilsonbekwame heeft geen WGBO vertegenwoordiging
    Given een persoon met BSN "400000017"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient     | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 999999999      | 500000099   | Andere Familie   | ECHTGENOOT   | true             | 2024-01-01              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"

  # ===== Scenario 5: Meerdere wilsonbekwame familieleden =====

  Scenario: Persoon is vertegenwoordiger voor meerdere wilsonbekwame familieleden
    Given een persoon met BSN "400000018"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient    | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000018      | 500000018   | Moeder Martha   | KIND         | true             | 2023-01-15              |
      | 400000018      | 500000019   | Vader Victor    | KIND         | true             | 2024-02-20              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000018"
    And bevat de output "subject_ids" waarde "500000019"

  # ===== Scenario 6: Ongeldige relatietype wordt niet geaccepteerd =====

  Scenario: Neef/nicht is geen geldige WGBO vertegenwoordiger
    Given een persoon met BSN "400000019"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000019      | 500000020   | Oom Jan      | NEEF         | true             | 2024-01-01              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # ===== Scenario 7: Verificatie van vertegenwoordigingsrechten =====

  Scenario: WGBO vertegenwoordiger krijgt volledige medische beslissingsrechten
    Given een persoon met BSN "400000006"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient        | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000006      | 500000008   | Gerda Groen-van Dijk | ECHTGENOOT   | true             | 2024-01-10              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And bevat de output "valid_from_dates" waarde "2024-01-10"

  # ===== Scenario 8: Combinatie van wilsbekwaam en wilsonbekwaam =====

  Scenario: Persoon met zowel wilsbekwame als wilsonbekwame familieleden
    Given een persoon met BSN "400000020"
    And de volgende RvIG wgbo_familie_relaties gegevens:
      | bsn_familielid | bsn_patient | naam_patient      | relatie_type | is_wilsonbekwaam | datum_wilsonbekwaamheid |
      | 400000020      | 500000021   | Emma Wilsbekwaam  | ECHTGENOOT   | false            |                         |
      | 400000020      | 500000022   | Opa Wilsonbekwaam | KIND         | true             | 2024-07-01              |
    When de wgbo_vertegenwoordiger wordt uitgevoerd door RvIG
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000022"
    And bevat de output "subject_ids" niet de waarde "500000021"
