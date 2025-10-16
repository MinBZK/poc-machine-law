Feature: Curatele Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een curator bevoegd is om te handelen namens een curandus
  Zodat alleen rechtmatige vertegenwoordigers namens personen onder curatele kunnen handelen

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS =====

  Scenario: Curator met volledige curatele mag handelen namens curandus
    Given een persoon met BSN "200000001"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000001   | 200000002    | true              | VOLLEDIG      | 2023-01-15   | null      | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000001   | 200000002    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "curatele_artikel_378_bw"
    And is type_curatele "VOLLEDIG"

  Scenario: Curator met beperkte curatele (financieel) mag handelen voor financiële zaken
    Given een persoon met BSN "200000011"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen  |
      | 200000011   | 200000012    | true              | BEPERKT       | 2024-03-01   | null      | ["financieel"] |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000011   | 200000012    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "curatele_artikel_378_bw"
    And is type_curatele "BEPERKT"
    And bevat beperkingen "financieel"

  Scenario: Co-curator mag handelen namens curandus (gezamenlijk met andere co-curator)
    Given een persoon met BSN "200000031"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000031   | 200000033    | true              | VOLLEDIG      | 2023-09-01   | null      | []          |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000032   | 200000033    | true              | VOLLEDIG      | 2023-09-01   | null      | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000031   | 200000033    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "curatele_artikel_378_bw"
    And is type_curatele "VOLLEDIG"

  Scenario: Curator met tijdelijke curatele (nog niet verlopen) mag handelen
    Given een persoon met BSN "200000041"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum  | beperkingen |
      | 200000041   | 200000042    | true              | VOLLEDIG      | 2024-01-01   | 2026-01-01 | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000041   | 200000042    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "curatele_artikel_378_bw"
    And is type_curatele "VOLLEDIG"

  # ===== NEGATIEVE SCENARIOS =====

  Scenario: Curator met beperkte curatele (alleen financieel) heeft beperkte bevoegdheid
    Given een persoon met BSN "200000011"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen  |
      | 200000011   | 200000012    | true              | BEPERKT       | 2024-03-01   | null      | ["financieel"] |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000011   | 200000012    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is type_curatele "BEPERKT"
    And bevat beperkingen "financieel"

  Scenario: Ex-curator (curatele beëindigd) mag NIET meer handelen
    Given een persoon met BSN "200000021"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum  | beperkingen |
      | 200000021   | 200000022    | true              | VOLLEDIG      | 2022-01-01   | 2024-01-01 | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000021   | 200000022    |
    Then is niet voldaan aan de voorwaarden
    And is mag_vertegenwoordigen false

  Scenario: Niet-curator mag NIET handelen namens persoon onder curatele
    Given een persoon met BSN "999999999"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000001   | 200000002    | true              | VOLLEDIG      | 2023-01-15   | null      | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 999999999   | 200000002    |
    Then is niet voldaan aan de voorwaarden
    And is mag_vertegenwoordigen false

  Scenario: Curator met tijdelijke curatele (verlopen) mag NIET meer handelen
    Given een persoon met BSN "200000021"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum  | beperkingen |
      | 200000021   | 200000022    | true              | VOLLEDIG      | 2022-01-01   | 2024-01-01 | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000021   | 200000022    |
    Then is niet voldaan aan de voorwaarden
    And is mag_vertegenwoordigen false

  # ===== EDGE CASES =====

  Scenario: Curator met beperkte curatele (financieel en medisch) mag handelen voor beide domeinen
    Given een persoon met BSN "200000013"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen            |
      | 200000013   | 200000014    | true              | BEPERKT       | 2023-06-01   | null      | ["financieel", "medisch"] |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000013   | 200000014    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is type_curatele "BEPERKT"
    And bevat beperkingen "medisch"
    And bevat beperkingen "financieel"

  Scenario: Co-curator 2 kan ook zelfstandig handelen (beide co-curatoren zijn bevoegd)
    Given een persoon met BSN "200000032"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000031   | 200000033    | true              | VOLLEDIG      | 2023-09-01   | null      | []          |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000032   | 200000033    | true              | VOLLEDIG      | 2023-09-01   | null      | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000032   | 200000033    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "curatele_artikel_378_bw"

  Scenario: Curatele met ingangsdatum in de toekomst is nog NIET actief
    Given een persoon met BSN "200000051"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen |
      | 200000051   | 200000052    | true              | VOLLEDIG      | 2026-01-01   | null      | []          |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000051   | 200000052    |
    Then is niet voldaan aan de voorwaarden
    And is mag_vertegenwoordigen false

  Scenario: Curator met beperkte curatele zonder specifieke actie type mag handelen binnen beperkingen
    Given een persoon met BSN "200000011"
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | curator_bsn | curandus_bsn | uitspraak_bestaat | type_curatele | ingangsdatum | einddatum | beperkingen  |
      | 200000011   | 200000012    | true              | BEPERKT       | 2024-03-01   | null      | ["financieel"] |
    When de burgerlijk_wetboek/curatele wordt uitgevoerd door RECHTSPRAAK met
      | BSN_CURATOR | BSN_CURANDUS |
      | 200000011   | 200000012    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is type_curatele "BEPERKT"
