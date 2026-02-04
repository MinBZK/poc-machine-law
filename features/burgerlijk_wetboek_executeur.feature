@skip-go
@skip
Feature: Burgerlijk Wetboek Executeur (BW 4:144-150)
  Als Notariaat
  Wil ik executeur-registraties beheren
  Zodat executeurs nalatenschappen kunnen afwikkelen

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "400000003"

  Scenario: Executeur heeft actieve nalatenschap
    # Art. 4:144 BW: executeur is benoemd bij uiterste wilsbeschikking
    # Art. 4:145 BW: executeur beheert goederen der nalatenschap
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       | 2024-06-15        |             | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "NAL-2024-00123"
    And bevat de output "subject_names" waarde "Nalatenschap Karel Posthumus"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "EXECUTEUR_NALATENSCHAP"

  Scenario: Persoon is geen executeur
    # Persoon heeft geen executeur-registraties
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater  | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 999999999     | 888888888    | Andere Erflater| NAL-2024-99999   | 2024-01-01       | 2024-01-15        |             | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is niet voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Nalatenschap is afgewikkeld (status AFGEWIKKELD)
    # Art. 4:149 BW: taak executeur eindigt bij voltooiing
    # Note: registratie bestaat nog, maar is niet meer actief
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status      |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       | 2024-06-15        | 2025-01-15  | AFGEWIKKELD |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Executeur heeft benoeming afgewezen
    # Art. 4:144 lid 2 BW: executeur kan benoeming niet aanvaarden
    # Note: registratie bestaat, maar status is AFGEWEZEN dus geen actieve delegatie
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status     |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       |                   |             | AFGEWEZEN  |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Executeur met meerdere actieve nalatenschappen
    # Een executeur kan voor meerdere nalatenschappen benoemd zijn
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater   | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 400000003     | 500000005    | Karel Posthumus    | NAL-2024-00123   | 2024-06-01       | 2024-06-15        |             | ACTIEF |
      | 400000003     | 500000006    | Marie de Vries  | NAL-2024-00456   | 2024-08-01       | 2024-08-10        |             | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "NAL-2024-00123"
    And bevat de output "subject_ids" waarde "NAL-2024-00456"

  Scenario: Executeur met mix van actieve en afgewikkelde nalatenschappen
    # Alleen actieve nalatenschappen worden meegenomen
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater   | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status      |
      | 400000003     | 500000005    | Karel Posthumus    | NAL-2024-00123   | 2024-06-01       | 2024-06-15        |             | ACTIEF      |
      | 400000003     | 500000006    | Marie de Vries  | NAL-2023-00789   | 2023-02-01       | 2023-02-15        | 2024-03-01  | AFGEWIKKELD |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "NAL-2024-00123"
    And bevat de output "subject_ids" niet de waarde "NAL-2023-00789"

  Scenario: Executeurschap met einddatum in de toekomst blijft actief
    # Executeurschap is nog geldig als einddatum in de toekomst ligt
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       | 2024-06-15        | 2026-06-15  | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "NAL-2024-00123"

  Scenario: Executeurschap met einddatum in het verleden is niet meer actief
    # Art. 4:149 BW: taak executeur eindigt
    # Note: registratie bestaat maar einddatum is verstreken
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       | 2024-06-15        | 2025-01-01  | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Executeur heeft correct rechten voor nalatenschap beheer
    # Art. 4:145 lid 1 BW: executeur heeft privatieve beheers- en beschikkingsbevoegdheid
    Given de volgende NOTARIAAT executeur_registraties gegevens
      | bsn_executeur | bsn_erflater | naam_erflater | nalatenschap_id  | datum_overlijden | datum_aanvaarding | datum_einde | status |
      | 400000003     | 500000005    | Karel Posthumus  | NAL-2024-00123   | 2024-06-01       | 2024-06-15        |             | ACTIEF |
    When de burgerlijk_wetboek_executeur wordt uitgevoerd door NOTARIAAT
    Then is voldaan aan de voorwaarden
    And bevat de output "permissions" waarde "['LEZEN', 'CLAIMS_INDIENEN', 'BESLUITEN_ONTVANGEN']"
