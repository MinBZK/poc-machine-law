@skip-go
Feature: WPM Rapportageverplichting
  Als werkgever
  Wil ik weten of ik verplicht ben om te rapporteren over werkgebonden personenmobiliteit
  Zodat ik voldoe aan de wettelijke verplichtingen volgens de Omgevingswet

  Background:
    Given de datum is "2024-07-01"

  Scenario: Organisatie met 100 werknemers is verplicht te rapporteren
    Given een organisatie met KVK-nummer "12345678"
    And de volgende RVO wpm_gegevens gegevens:
      | kvk_nummer | aantal_werknemers | verstrekt_mobiliteitsvergoeding |
      | 12345678   | 100               | true                            |
    When de omgevingswet/werkgebonden_personenmobiliteit wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de output "rapportageverplichting" waar
    And heeft de output "aantal_werknemers" waarde "100"

  Scenario: Organisatie met 99 werknemers is niet verplicht te rapporteren
    Given een organisatie met KVK-nummer "87654321"
    And de volgende RVO wpm_gegevens gegevens:
      | kvk_nummer | aantal_werknemers | verstrekt_mobiliteitsvergoeding |
      | 87654321   | 99                | true                            |
    When de omgevingswet/werkgebonden_personenmobiliteit wordt uitgevoerd door RVO
    Then is niet voldaan aan de voorwaarden

  Scenario: Organisatie zonder mobiliteitsvergoeding hoeft niet te rapporteren
    Given een organisatie met KVK-nummer "44444444"
    And de volgende RVO wpm_gegevens gegevens:
      | kvk_nummer | aantal_werknemers | verstrekt_mobiliteitsvergoeding |
      | 44444444   | 150               | false                           |
    When de omgevingswet/werkgebonden_personenmobiliteit wordt uitgevoerd door RVO
    Then is niet voldaan aan de voorwaarden

  Scenario: Organisatie rapporteert reisgegevens en CO2-uitstoot
    Given een organisatie met KVK-nummer "55555555"
    And de volgende RVO wpm_gegevens gegevens:
      | kvk_nummer | aantal_werknemers | verstrekt_mobiliteitsvergoeding |
      | 55555555   | 120               | true                            |
    And de volgende RVO wpm_reisgegevens gegevens:
      | kvk_nummer | woon_werk_auto_benzine | woon_werk_auto_diesel | zakelijk_auto_benzine | zakelijk_auto_diesel | woon_werk_openbaar_vervoer |
      | 55555555   | 10000                  | 5000                  | 3000                  | 2000                 | 8000                       |
    When de omgevingswet/werkgebonden_personenmobiliteit wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And is de output "rapportageverplichting" waar
    When de omgevingswet/werkgebonden_personenmobiliteit/gegevens wordt uitgevoerd door RVO
    Then is voldaan aan de voorwaarden
    And heeft de output "woon_werk_auto_benzine" waarde "10000"
    And heeft de output "woon_werk_auto_diesel" waarde "5000"
    And heeft de output "zakelijk_auto_benzine" waarde "3000"
    And heeft de output "zakelijk_auto_diesel" waarde "2000"
    And heeft de output "woon_werk_openbaar_vervoer" waarde "8000"
    And heeft de output "co2_uitstoot_totaal" waarde "3500000"
