Feature: Burgerlijk Wetboek Curatele (BW 1:378-391)
  Als Rechtspraak
  Wil ik curatele-registraties beheren
  Zodat curators hun curandussen kunnen vertegenwoordigen

  Background:
    Given de datum is "2025-03-01"

  Scenario: Curator heeft actieve curatele voor curandus
    # Art. 1:386 BW: curator vertegenwoordigt curandus in alle burgerlijke handelingen
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status |
      | 400000001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000001"
    And bevat de output "subject_names" waarde "Sophie van Dam"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "CURATOR"
    And bevat de output "permissions" waarde "['LEZEN', 'CLAIMS_INDIENEN', 'BESLUITEN_ONTVANGEN']"
    And bevat de output "valid_from_dates" waarde "2022-01-15"

  Scenario: Persoon zonder curatele-registraties heeft geen delegaties
    # Persoon is niet geregistreerd als curator in het CCBR
    Given een persoon met BSN "999993653"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status |
      | 400000001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is niet voldaan aan de voorwaarden

  Scenario: Beeindigde curatele met status BEEINDIGD geeft geen delegaties
    # Art. 1:389 BW: curatele kan worden opgeheven door de rechter
    Given een persoon met BSN "400000007"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus | datum_ingang | datum_einde | status    |
      | 400000007   | 500000009    | Jan de Boer  | 2020-01-01   | 2023-12-31  | BEEINDIGD |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Curatele met einddatum in het verleden geeft geen delegaties
    # Art. 1:389 BW: curatele eindigt na opheffing door rechter
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status |
      | 400000001   | 500000001    | Sophie van Dam | 2020-01-01   | 2024-12-31  | ACTIEF |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Curator met meerdere curandussen heeft meerdere delegaties
    # Art. 1:383 BW: curator kan voor meerdere personen worden benoemd
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status |
      | 400000001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF |
      | 400000001   | 500000010    | Pieter Zwak     | 2023-06-01   |             | ACTIEF |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000001"
    And bevat de output "subject_ids" waarde "500000010"
    And bevat de output "subject_names" waarde "Sophie van Dam"
    And bevat de output "subject_names" waarde "Pieter Zwak"

  Scenario: Mix van actieve en beeindigde curatele
    # Alleen actieve curatele geeft vertegenwoordigingsbevoegdheid
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status    |
      | 400000001   | 500000001    | Sophie van Dam | 2022-01-15   |             | ACTIEF    |
      | 400000001   | 500000009    | Jan de Boer    | 2020-01-01   | 2023-12-31  | BEEINDIGD |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000001"
    And bevat de output "subject_ids" niet de waarde "500000009"

  Scenario: Curatele met toekomstige einddatum is nog actief
    # Curatele blijft actief totdat einddatum bereikt is
    Given een persoon met BSN "400000001"
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curator | bsn_curandus | naam_curandus   | datum_ingang | datum_einde | status |
      | 400000001   | 500000001    | Sophie van Dam | 2022-01-15   | 2026-12-31  | ACTIEF |
    When de burgerlijk_wetboek_curatele wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000001"
    And bevat de output "valid_until_dates" waarde "2026-12-31"
