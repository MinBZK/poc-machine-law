Feature: Ouderlijk Gezag Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een ouder bevoegd is om te handelen namens een minderjarig kind
  Zodat alleen rechtmatige vertegenwoordigers namens kinderen kunnen handelen

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS =====

  Scenario: Ouder met ouderlijk gezag mag handelen namens minderjarig kind
    Given een persoon met BSN "100000001"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000001 | 100000003  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000003 | 9        |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000001 | 100000003  | true        |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000001 | 100000003  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000001 | 100000003  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "ouderlijk_gezag_artikel_245_bw"

  Scenario: Moeder met gezamenlijk gezag mag handelen namens kind
    Given een persoon met BSN "100000002"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000002 | 100000003  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000003 | 9        |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000002 | 100000003  | true        |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000002 | 100000003  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000002 | 100000003  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true

  Scenario: Ouder mag handelen namens 17-jarig kind (bijna meerderjarig)
    Given een persoon met BSN "100000001"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000001 | 100000004  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000004 | 17       |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000001 | 100000004  | true        |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000001 | 100000004  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000001 | 100000004  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true

  # ===== NEGATIEVE SCENARIOS =====

  Scenario: Ouder mag NIET handelen namens meerderjarig kind (18+)
    Given een persoon met BSN "100000001"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000001 | 100000005  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000005 | 18       |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000001 | 100000005  | false       |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000001 | 100000005  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000001 | 100000005  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Niet-ouder mag NIET handelen namens kind (geen ouder-kind relatie)
    Given een persoon met BSN "200000001"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 200000001 | 100000003  | false    |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000003 | 9        |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 200000001 | 100000003  | false       |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 200000001 | 100000003  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 200000001 | 100000003  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Ouder zonder ouderlijk gezag mag NIET handelen (gescheiden, geen gezag)
    Given een persoon met BSN "100000012"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000012 | 100000013  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000013 | 12       |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000012 | 100000013  | false       |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000012 | 100000013  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000012 | 100000013  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Ouder met ontzet ouderlijk gezag mag NIET handelen
    Given een persoon met BSN "100000021"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000021 | 100000023  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000023 | 14       |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000021 | 100000023  | false       |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000021 | 100000023  | true                       |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000021 | 100000023  |
    Then is niet voldaan aan de voorwaarden

  # ===== EDGE CASES =====

  Scenario: Grootouder zonder voogdij mag NIET handelen namens kleinkind
    Given een persoon met BSN "100000031"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000031 | 100000033  | false    |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000033 | 8        |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000031 | 100000033  | false       |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000031 | 100000033  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000031 | 100000033  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Voogd na adoptie MAG handelen namens geadopteerd kind
    Given een persoon met BSN "100000041"
    And de volgende RvIG brp_relaties gegevens:
      | bsn_ouder | bsn_kind   | is_ouder |
      | 100000041 | 100000043  | true     |
    And de volgende RvIG brp_personen gegevens:
      | bsn       | leeftijd |
      | 100000043 | 7        |
    And de volgende RvIG brp_gezagsrelaties gegevens:
      | bsn_ouder | bsn_kind   | heeft_gezag |
      | 100000041 | 100000043  | true        |
    And de volgende RECHTSPRAAK curatele_register gegevens:
      | bsn_ouder | bsn_kind   | ontzetting_ouderlijk_gezag |
      | 100000041 | 100000043  | false                      |
    When de burgerlijk_wetboek/ouderlijk_gezag wordt uitgevoerd door RvIG met
      | BSN_OUDER | BSN_KIND   |
      | 100000041 | 100000043  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
