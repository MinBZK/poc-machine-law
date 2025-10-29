Feature: Mentorschap Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een mentor bevoegd is om te handelen namens een betrokkene
  Zodat alleen rechtmatige vertegenwoordigers namens personen onder mentorschap kunnen handelen voor persoonlijke aangelegenheden

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS (Mentor MAG handelen voor persoonlijke zaken) =====

  Scenario: Mentor met volledige bevoegdheden mag medische beslissingen nemen
    Given een persoon met BSN "220000001"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000001  | 220000002      | true              | true         | true      | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE |
      | 220000001  | 220000002      | medisch    |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is vertegenwoordigings_grondslag "mentorschap_artikel_450_bw"
    And is scope "persoonlijk_alleen"
    And bevat bevoegdheden "medisch"

  Scenario: Mentor mag zorginstelling kiezen voor betrokkene
    Given een persoon met BSN "220000001"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000001  | 220000002      | true              | true         | true      | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE |
      | 220000001  | 220000002      | zorg       |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "persoonlijk_alleen"
    And bevat bevoegdheden "zorg"

  Scenario: Mentor mag woonplaats bepalen voor betrokkene
    Given een persoon met BSN "220000001"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000001  | 220000002      | true              | true         | true      | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE |
      | 220000001  | 220000002      | wonen      |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "persoonlijk_alleen"
    And bevat bevoegdheden "wonen"

  Scenario: Mentor mag toestemming geven voor medische behandeling
    Given een persoon met BSN "220000011"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden | heeft_bevoegdheden | peildatum  |
      | 220000011  | 220000012      | true              | true         | true      | medisch      | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE           |
      | 220000011  | 220000012      | medische_behandeling |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "persoonlijk_alleen"
    And bevat bevoegdheden "medisch"

  # ===== NEGATIEVE SCENARIOS (Mentor MAG NIET handelen) =====

  Scenario: Mentor mag NIET handelen voor financiële transacties (buiten scope)
    Given een persoon met BSN "220000001"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000001  | 220000002      | true              | true         | true      | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE |
      | 220000001  | 220000002      | financieel |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "persoonlijk_alleen"
    # Notitie: Wet zegt wel mag_vertegenwoordigen=true, maar scope="persoonlijk_alleen"
    # Applicatie moet scope checken - financiële zaken zijn NIET binnen scope mentorschap

  Scenario: Ex-mentor (mentorschap beëindigd) mag NIET meer handelen
    Given een persoon met BSN "220000031"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000031  | 220000032      | true              | true         | false     | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE |
      | 220000031  | 220000032      |
    Then is niet voldaan aan de voorwaarden

  Scenario: Mentor mag NIET handelen voor belastingaangifte (financiële aangelegenheid)
    Given een persoon met BSN "220000021"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden | heeft_bevoegdheden | peildatum  |
      | 220000021  | 220000022      | true              | true         | true      | medisch,zorg | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE | ACTIE_TYPE        |
      | 220000021  | 220000022      | belastingaangifte |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is scope "persoonlijk_alleen"
    # Notitie: Belastingaangifte is financieel, NIET persoonlijk
    # Mentorschap dekt ALLEEN persoonlijke aangelegenheden

  Scenario: Niet-mentor mag NIET handelen namens persoon met mentorschap
    Given een persoon met BSN "999999999"
    And de volgende RECHTSPRAAK mentorschap_register gegevens:
      | mentor_bsn | betrokkene_bsn | uitspraak_bestaat | mentor_match | is_actief | bevoegdheden           | heeft_bevoegdheden | peildatum  |
      | 220000001  | 220000002      | true              | false        | true      | medisch,zorg,wonen     | true               | 2025-10-16 |
    When de burgerlijk_wetboek/mentorschap wordt uitgevoerd door RECHTSPRAAK met
      | BSN_MENTOR | BSN_BETROKKENE |
      | 999999999  | 220000002      |
    Then is niet voldaan aan de voorwaarden
