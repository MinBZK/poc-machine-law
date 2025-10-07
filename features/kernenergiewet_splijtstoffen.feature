Feature: Kernenergiewet Vergunningverlening Splijtstoffen
  Als nucleaire operator
  Wil ik weten of ik een vergunning nodig heb en kan krijgen
  Zodat ik wettelijk mag werken met splijtstoffen

  Background:
    Given de datum is "2024-07-01"

  Scenario: Transport van splijtstoffen met voldoende dosis en financiële zekerheid
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.5                  | 10.0                 | 0.05                 |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 2                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type | materiaal_type | is_nieuwe_installatie |
      | transport       | splijtstof     | false                 |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Bezit van splijtstoffen met te hoge stralingsdosis
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 2.5                  | 10.0                 | 0.05                 |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 2                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type | materiaal_type | is_nieuwe_installatie |
      | bezit           | splijtstof     | false                 |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "bescherming_mensen_dieren_planten_goederen"

  Scenario: Nieuwe kerninstallatie zonder financiële zekerheid
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.5                  | 10.0                 | 0.05                 |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 50000000                    | 2                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type            | materiaal_type | is_nieuwe_installatie |
      | inrichting_oprichten       | splijtstof     | true                  |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "zekerheid_betaling_schadevergoeding"

  Scenario: Exploitatie van kerninstallatie met alle voorwaarden voldaan
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.3                  | 5.0                  | 0.02                 |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 200000000                   | 5                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type            | materiaal_type | is_nieuwe_installatie |
      | inrichting_exploiteren     | splijtstof     | false                 |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Transport van ertsen met lage stralingsdosis
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.1                  | 1.0                  | 0.01                 |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 1                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type | materiaal_type | is_nieuwe_installatie |
      | transport       | erts           | false                 |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "true"
    And is het veld "weigeringsgronden" een lege lijst

  Scenario: Meerdere weigeringsgronden tegelijk (hoge dosis en geen financiële zekerheid)
    Given de volgende ANVS stralingsbescherming gegevens:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 3.0                  | 60.0                 | 0.5                  |
    And de volgende ANVS kerninstallaties gegevens:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 10000000                    | 1                  |
    When de kernenergiewet wordt uitgevoerd door ANVS met parameters:
      | activiteit_type | materiaal_type | is_nieuwe_installatie |
      | invoer          | splijtstof     | false                 |
    Then is het veld "vergunning_vereist" gelijk aan "true"
    And is het veld "vergunning_toegestaan" gelijk aan "false"
    And bevat het veld "weigeringsgronden" de waarde "bescherming_mensen_dieren_planten_goederen"
    And bevat het veld "weigeringsgronden" de waarde "zekerheid_betaling_schadevergoeding"
