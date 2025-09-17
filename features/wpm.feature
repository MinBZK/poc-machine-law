Feature: WPM Rapportageverplichting
  Als werkgever
  Wil ik weten of ik verplicht ben om te rapporteren over werkgebonden personenmobiliteit
  Zodat ik voldoe aan de wettelijke verplichtingen

  Background:
    Given de datum is "2024-07-01"

  Scenario: Organisatie met 100 werknemers is verplicht te rapporteren
    Given een organisatie met KVK-nummer "12345678"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status | aantal_werknemers | datum_telling |
      | 12345678   | BV         | ACTIEF | 100               | 2024-07-01    |
    When de wpm wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de rapportageverplichting "true"
    And is de rapportage_deadline "2025-06-30"
    And is het aantal_werknemers "100"

  Scenario: Organisatie met 99 werknemers is niet verplicht te rapporteren
    Given een organisatie met KVK-nummer "87654321"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status | aantal_werknemers | datum_telling |
      | 87654321   | BV         | ACTIEF | 99                | 2024-07-01    |
    When de wpm wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de rapportageverplichting "false"
    And is het aantal_werknemers "99"

  Scenario: Organisatie met meer dan 100 werknemers is verplicht te rapporteren
    Given een organisatie met KVK-nummer "11111111"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status | aantal_werknemers | datum_telling |
      | 11111111   | BV         | ACTIEF | 150               | 2024-07-01    |
    When de wpm wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de rapportageverplichting "true"
    And is de rapportage_deadline "2025-06-30"
    And is het aantal_werknemers "150"

  Scenario: Niet-actieve organisatie hoeft niet te rapporteren
    Given een organisatie met KVK-nummer "22222222"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status    | aantal_werknemers | datum_telling |
      | 22222222   | BV         | INACTIEF  | 120               | 2024-07-01    |
    When de wpm wordt uitgevoerd door RVO
    Then is niet voldaan aan de voorwaarden

  Scenario: Organisatie met werknemers bepaling vanaf 2025
    Given een organisatie met KVK-nummer "33333333"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status | aantal_werknemers | datum_telling |
      | 33333333   | BV         | ACTIEF | 105               | 2024-07-01    |
    When de wpm wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de rapportageverplichting "true"
    And is de rapportage_deadline "2025-06-30"
    And is het aantal_werknemers "105"

  Scenario: Organisatie verzamelt gegevens voor rapportage
    Given een organisatie met KVK-nummer "44444444"
    And de volgende KVK bedrijfsgegevens:
      | kvk_nummer | rechtsvorm | status | aantal_werknemers | datum_telling |
      | 44444444   | BV         | ACTIEF | 150               | 2024-07-01    |
    When de werkgever deze WPM gegevens indient:
      | service | law | key                      | nieuwe_waarde | reden               | bewijs |
      | RVO     | wpm | WOON_WERK_AUTO_BENZINE   | 50000        | verplichte gegevens |        |
      | RVO     | wpm | WOON_WERK_AUTO_DIESEL    | 30000        | verplichte gegevens |        |
      | RVO     | wpm | ZAKELIJK_AUTO_BENZINE    | 25000        | verplichte gegevens |        |
      | RVO     | wpm | ZAKELIJK_AUTO_DIESEL     | 15000        | verplichte gegevens |        |
      | RVO     | wpm | WOON_WERK_OV             | 20000        | verplichte gegevens |        |
    When de wpm wordt uitgevoerd door RVO met wijzigingen
    Then ontbreken er geen verplichte gegevens
    And is voldaan aan de voorwaarden
    And is de co2_uitstoot_totaal groter dan 0
