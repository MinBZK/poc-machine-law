Feature: Volmacht Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een gevolmachtigde bevoegd is om te handelen namens een volmachtgever
  Zodat alleen rechtmatige gevolmachtigden namens volmachtgevers kunnen handelen

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS =====

  Scenario: Gevolmachtigde met algemene volmacht mag alle handelingen verrichten
    Given een persoon met BSN "230000001"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000001          | 230000002         |                    | ALGEMEEN      | ["*"] | 2024-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE |
      | 230000001          | 230000002         | PERSOON     |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "volmacht_artikel_60_bw"
    And is type_volmacht "ALGEMEEN"

  Scenario: Gevolmachtigde met bijzondere volmacht mag specifieke handelingen verrichten (belastingaangifte)
    Given een persoon met BSN "230000011"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                     | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000011          | 230000012         |                    | BIJZONDER     | ["belasting_aangifte", "belasting_bezwaar"] | 2023-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE                |
      | 230000011          | 230000012         | PERSOON     | belasting_aangifte   |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "volmacht_artikel_60_bw"
    And is type_volmacht "BIJZONDER"

  Scenario: Procuratiehouder mag handelen namens bedrijf
    Given een persoon met BSN "230000031"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                       | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000031          |                   | 001234567          | PROCURATIE    | ["contracten_tekenen", "bankzaken", "rechtszaken"] | 2023-06-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | RSIN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000031          | 001234567          | BEDRIJF     | contracten_tekenen |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "volmacht_artikel_60_bw"
    And is type_volmacht "PROCURATIE"

  Scenario: Accountant met volmacht mag belastingaangifte doen voor cliënt
    Given een persoon met BSN "230000061"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                                      | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000061          | 230000062         |                    | BIJZONDER     | ["belasting_aangifte", "belasting_bezwaar", "financiele_administratie"] | 2022-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000061          | 230000062         | PERSOON     | belasting_aangifte |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "volmacht_artikel_60_bw"

  Scenario: Partner met volmacht mag bankzaken regelen
    Given een persoon met BSN "230000051"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                             | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000051          | 230000052         |                    | BIJZONDER     | ["bankzaken", "belasting_aangifte", "verzekeringen"] | 2023-08-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE      |
      | 230000051          | 230000052         | PERSOON     | bankzaken  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "volmacht_artikel_60_bw"

  # ===== NEGATIEVE SCENARIOS =====

  Scenario: Gevolmachtigde met bijzondere volmacht mag GEEN handelingen verrichten buiten scope
    Given een persoon met BSN "230000011"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                     | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000011          | 230000012         |                    | BIJZONDER     | ["belasting_aangifte", "belasting_bezwaar"] | 2023-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE      |
      | 230000011          | 230000012         | PERSOON     | bankzaken  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Gevolmachtigde met herroepen volmacht mag NIET meer handelen
    Given een persoon met BSN "230000021"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000021          | 230000022         |                    | ALGEMEEN      | ["*"] | 2022-01-01   |           | true      | 2024-06-01       |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE |
      | 230000021          | 230000022         | PERSOON     |
    Then is niet voldaan aan de voorwaarden

  Scenario: Ex-accountant met herroepen volmacht mag NIET meer handelen
    Given een persoon met BSN "230000071"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                   | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000071          | 230000072         |                    | BIJZONDER     | ["belasting_aangifte"]  | 2020-01-01   |           | true      | 2024-01-15       |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000071          | 230000072         | PERSOON     | belasting_aangifte |
    Then is niet voldaan aan de voorwaarden

  Scenario: Gevolmachtigde met verlopen tijdelijke volmacht mag NIET meer handelen
    Given een persoon met BSN "230000081"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                        | ingangsdatum | einddatum  | herroepen | herroepingsdatum |
      | 230000081          | 230000082         |                    | BIJZONDER     | ["onroerend_goed_verkoop"]   | 2023-01-01   | 2023-12-31 | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE                    |
      | 230000081          | 230000082         | PERSOON     | onroerend_goed_verkoop   |
    Then is niet voldaan aan de voorwaarden

  Scenario: Niet-gevolmachtigde persoon mag NIET handelen namens ander
    Given een persoon met BSN "999999999"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000001          | 230000002         |                    | ALGEMEEN      | ["*"] | 2024-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE |
      | 999999999          | 230000002         | PERSOON     |
    Then is niet voldaan aan de voorwaarden

  # ===== EDGE CASES =====

  Scenario: Algemene volmacht geldt ook zonder specifieke actie parameter
    Given een persoon met BSN "230000001"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000001          | 230000002         |                    | ALGEMEEN      | ["*"] | 2024-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000001          | 230000002         | PERSOON     | willekeurige_actie |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true

  Scenario: Bijzondere volmacht met meerdere acties in scope mag alle genoemde acties verrichten
    Given een persoon met BSN "230000051"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                             | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000051          | 230000052         |                    | BIJZONDER     | ["bankzaken", "belasting_aangifte", "verzekeringen"] | 2023-08-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000051          | 230000052         | PERSOON     | belasting_aangifte |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true

  Scenario: Bijzondere volmacht zonder ACTIE parameter mag NIET worden gebruikt
    Given een persoon met BSN "230000011"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                     | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000011          | 230000012         |                    | BIJZONDER     | ["belasting_aangifte", "belasting_bezwaar"] | 2023-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE |
      | 230000011          | 230000012         | PERSOON     |
    Then is niet voldaan aan de voorwaarden

  Scenario: Volmacht voor bankzaken alleen mag NIET worden gebruikt voor andere acties
    Given een persoon met BSN "230000041"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope         | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000041          | 230000042         |                    | BIJZONDER     | ["bankzaken"] | 2024-02-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE              |
      | 230000041          | 230000042         | PERSOON     | belasting_aangifte |
    Then is niet voldaan aan de voorwaarden

  Scenario: Procuratie met beperkte scope mag alleen specifieke handelingen verrichten
    Given een persoon met BSN "230000031"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                       | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000031          |                   | 001234567          | PROCURATIE    | ["contracten_tekenen", "bankzaken", "rechtszaken"] | 2023-06-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | RSIN_VOLMACHTGEVER | TARGET_TYPE | ACTIE            |
      | 230000031          | 001234567          | BEDRIJF     | aandelen_uitgeven |
    Then is niet voldaan aan de voorwaarden

  Scenario: Volmacht met toekomstige ingangsdatum is nog NIET actief
    Given een persoon met BSN "230000091"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                      | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000091          | 230000092         |                    | BIJZONDER     | ["bankzaken", "administratie"] | 2026-01-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE      |
      | 230000091          | 230000092         | PERSOON     | bankzaken  |
    Then is niet voldaan aan de voorwaarden

  Scenario: Procuratie namens bedrijf vereist RSIN_VOLMACHTGEVER, niet BSN
    Given een persoon met BSN "230000031"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope                                       | ingangsdatum | einddatum | herroepen | herroepingsdatum |
      | 230000031          |                   | 001234567          | PROCURATIE    | ["contracten_tekenen", "bankzaken", "rechtszaken"] | 2023-06-01   |           | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE |
      | 230000031          | 999999999         | BEDRIJF     |
    Then is niet voldaan aan de voorwaarden

  Scenario: Volmacht met exacte einddatum (vandaag) is verlopen
    Given een persoon met BSN "230000101"
    And de volgende NOTARIS volmacht_register gegevens:
      | gevolmachtigde_bsn | volmachtgever_bsn | volmachtgever_rsin | type_volmacht | scope         | ingangsdatum | einddatum  | herroepen | herroepingsdatum |
      | 230000101          | 230000102         |                    | BIJZONDER     | ["bankzaken"] | 2023-01-01   | 2025-10-16 | false     |                  |
    When de burgerlijk_wetboek/volmacht wordt uitgevoerd door ALGEMEEN met
      | BSN_GEVOLMACHTIGDE | BSN_VOLMACHTGEVER | TARGET_TYPE | ACTIE      |
      | 230000101          | 230000102         | PERSOON     | bankzaken  |
    Then is niet voldaan aan de voorwaarden
