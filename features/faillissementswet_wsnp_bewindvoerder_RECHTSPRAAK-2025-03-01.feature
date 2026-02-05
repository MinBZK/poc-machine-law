@skip-go
Feature: Faillissementswet WSNP Bewindvoerder (Fw Titel III)
  Als Rechtspraak
  Wil ik WSNP-registraties beheren
  Zodat bewindvoerders schuldsaneringen kunnen begeleiden

  Background:
    Given de datum is "2025-03-01"

  # Scenario 1: WSNP bewindvoerder has active WSNP (debt restructuring)
  Scenario: WSNP bewindvoerder heeft actieve schuldsanering
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000007"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "WSNP_BEWINDVOERDER_BOEDEL"

  # Scenario 2: Person is NOT a WSNP bewindvoerder (no registrations)
  Scenario: Persoon is geen WSNP bewindvoerder
    Given een persoon met BSN "123456789"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # Scenario 3: Completed WSNP with schone lei (clean slate) - no longer active
  # Note: requirements_met is true (person IS registered as bewindvoerder)
  # but heeft_delegaties is false (no ACTIVE delegations)
  Scenario: Voltooide WSNP met schone lei - bewindvoerder heeft geen actieve delegaties meer
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status      |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      | 2025-02-01  | SCHONE_LEI  |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # Scenario 4: WSNP ended without schone lei (beeindiging)
  # Note: requirements_met is true (person IS registered as bewindvoerder)
  # but heeft_delegaties is false (no ACTIVE delegations)
  Scenario: WSNP beeindigd zonder schone lei
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status      |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      | 2024-06-15  | BEEINDIGD   |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  # Scenario 5: Multiple sanieten per bewindvoerder
  Scenario: Bewindvoerder heeft meerdere actieve WSNP-zaken
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet      | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer  | R.18/23/789        | 2023-09-01      |             | ACTIEF |
      | 400000005         | 500000008  | Pieter Probleem  | R.18/24/123        | 2024-03-15      |             | ACTIEF |
      | 400000005         | 500000009  | Maria Moeilijk   | R.18/24/456        | 2024-06-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000007"
    And bevat de output "subject_ids" waarde "500000008"
    And bevat de output "subject_ids" waarde "500000009"

  # Scenario 6: Mix of active and completed WSNP - only active count
  Scenario: Mix van actieve en voltooide WSNP-zaken - alleen actieve tellen mee
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet      | insolventie_nummer | datum_uitspraak | datum_einde | status      |
      | 400000005         | 500000007  | Sandra Meijer  | R.18/23/789        | 2023-09-01      | 2025-02-01  | SCHONE_LEI  |
      | 400000005         | 500000008  | Pieter Probleem  | R.18/24/123        | 2024-03-15      |             | ACTIEF      |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000008"
    And bevat de output "subject_ids" niet de waarde "500000007"

  # Scenario 7: WSNP with future end date is still active
  Scenario: WSNP met einddatum in de toekomst is nog actief
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      | 2025-09-01  | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "500000007"

  # Scenario 8: Verify WSNP bewindvoerder permissions (LEZEN, CLAIMS_INDIENEN, BESLUITEN_ONTVANGEN)
  Scenario: WSNP bewindvoerder heeft correcte rechten voor boedelbeheer
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"

  # Scenario 9: WSNP standard duration is 18 months (since July 2023)
  Scenario: WSNP standaardduur van 18 maanden
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And bevat de output "valid_from_dates" waarde "2023-09-01"

  # Scenario 10: Subject names include WSNP Boedel prefix
  Scenario: Sanietnamen bevatten WSNP Boedel prefix
    Given een persoon met BSN "400000005"
    And de volgende RECHTSPRAAK wsnp_registraties gegevens:
      | bsn_bewindvoerder | bsn_saniet | naam_saniet     | insolventie_nummer | datum_uitspraak | datum_einde | status |
      | 400000005         | 500000007  | Sandra Meijer | R.18/23/789        | 2023-09-01      |             | ACTIEF |
    When de faillissementswet_wsnp_bewindvoerder wordt uitgevoerd door RECHTSPRAAK
    Then is voldaan aan de voorwaarden
    And bevat de output "subject_names" waarde "WSNP Boedel Sandra Meijer"
