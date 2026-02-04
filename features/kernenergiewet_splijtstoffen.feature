@skip-go
@skip
Feature: Kernenergiewet Vergunningverlening Splijtstoffen
  Als nucleaire operator
  Wil ik weten of ik een vergunning nodig heb en kan krijgen
  Zodat ik wettelijk mag werken met splijtstoffen

  Background:
    Given de datum is "2024-07-01"

  Scenario: Transport van splijtstoffen met voldoende dosis en financiële zekerheid
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | transport       | splijtstof     | false                 | 0.5                  | 10.0                 | 0.05                 | true                   | true           | 100000000                   | 2                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Bezit van splijtstoffen met te hoge stralingsdosis
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | bezit           | splijtstof     | false                 | 2.5                  | 10.0                 | 0.05                 | true                   | true           | 100000000                   | 2                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "bescherming_mensen_dieren_planten_goederen"

  Scenario: Nieuwe kerninstallatie zonder financiële zekerheid
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type      | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | inrichting_oprichten | splijtstof     | true                  | 0.5                  | 10.0                 | 0.05                 | true                   | true           | 50000000                    | 2                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "zekerheid_betaling_schadevergoeding"

  Scenario: Exploitatie van kerninstallatie met alle voorwaarden voldaan
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type        | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | inrichting_exploiteren | splijtstof     | false                 | 0.3                  | 5.0                  | 0.02                 | true                   | true           | 200000000                   | 5                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Transport van ertsen met lage stralingsdosis
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | transport       | erts           | false                 | 0.1                  | 1.0                  | 0.01                 | true                   | true           | 100000000                   | 1                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Meerdere weigeringsgronden tegelijk (hoge dosis en geen financiële zekerheid)
    When de kernenergiewet wordt uitgevoerd door ANVS met:
      | activiteit_type | materiaal_type | is_nieuwe_installatie | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | invoer          | splijtstof     | false                 | 3.0                  | 60.0                 | 0.5                  | true                   | true           | 10000000                    | 1                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "bescherming_mensen_dieren_planten_goederen"
