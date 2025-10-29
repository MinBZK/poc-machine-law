Feature: Bewindvoering Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een bewindvoerder bevoegd is om te handelen namens een rechthebbende
  Zodat alleen rechtmatige vertegenwoordigers namens personen onder bewind kunnen handelen voor financiële zaken

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS (Bewindvoerder MAG handelen voor financiële zaken) =====

  Scenario: Bewindvoerder met volledig bewind mag handelen voor financiële zaken
    Given een persoon met BSN "210000001"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000001         | 210000002         | true              | true                | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE  |
      | 210000001         | 210000002         | financieel  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "bewindvoering_artikel_431_bw"
    And is type_bewind "VOLLEDIG_BEWIND"
    And is scope "financieel_alleen"

  Scenario: Bewindvoerder mag banktransacties uitvoeren namens rechthebbende
    Given een persoon met BSN "210000031"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000031         | 210000032         | true              | true                | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE      |
      | 210000031         | 210000032         | banktransactie  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "financieel_alleen"

  Scenario: Bewindvoerder mag belastingaangifte doen namens rechthebbende
    Given een persoon met BSN "210000031"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000031         | 210000032         | true              | true                | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE           |
      | 210000031         | 210000032         | belastingaangifte    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "financieel_alleen"

  Scenario: Bewindvoerder met beperkt bewind (nog actief) mag handelen
    Given een persoon met BSN "210000011"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000011         | 210000012         | true              | true                | BEPERKT_BEWIND  | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE  |
      | 210000011         | 210000012         | financieel  |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is type_bewind "BEPERKT_BEWIND"
    And is scope "financieel_alleen"

  # ===== NEGATIEVE SCENARIOS (Bewindvoerder MAG NIET handelen) =====

  Scenario: Bewindvoerder mag NIET handelen voor medische beslissingen (buiten scope)
    Given een persoon met BSN "210000001"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000001         | 210000002         | true              | true                | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE |
      | 210000001         | 210000002         | medisch    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "financieel_alleen"
    # Notitie: Wet zegt wel mag_vertegenwoordigen=true, maar scope="financieel_alleen"
    # Applicatie moet scope checken voor medische beslissingen

  Scenario: Ex-bewindvoerder (bewind beëindigd) mag NIET meer handelen
    Given een persoon met BSN "210000021"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000021         | 210000022         | true              | true                | VOLLEDIG_BEWIND | false     | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE |
      | 210000021         | 210000022         |
    Then is niet voldaan aan de voorwaarden

  Scenario: Bewindvoerder mag NIET handelen voor huwelijkstoestemming (persoonlijke aangelegenheid)
    Given een persoon met BSN "210000001"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000001         | 210000002         | true              | true                | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE | ACTIE_TYPE             |
      | 210000001         | 210000002         | huwelijkstoestemming   |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "financieel_alleen"
    # Notitie: Bewindvoerder mag WEL vertegenwoordigen, maar alleen voor financiële zaken
    # Huwelijkstoestemming is persoonlijk, niet financieel, dus NIET binnen scope

  Scenario: Niet-bewindvoerder mag NIET handelen namens persoon onder bewind
    Given een persoon met BSN "999999999"
    And de volgende RECHTSPRAAK bewind_register gegevens:
      | bewindvoerder_bsn | rechthebbende_bsn | uitspraak_bestaat | bewindvoerder_match | type_bewind     | is_actief | peildatum  |
      | 210000001         | 210000002         | true              | false               | VOLLEDIG_BEWIND | true      | 2025-10-16 |
    When de burgerlijk_wetboek/bewindvoering wordt uitgevoerd door RECHTSPRAAK met
      | BSN_BEWINDVOERDER | BSN_RECHTHEBBENDE |
      | 999999999         | 210000002         |
    Then is niet voldaan aan de voorwaarden
