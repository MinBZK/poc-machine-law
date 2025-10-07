Feature: Besluit kerninstallaties, splijtstoffen en ertsen
  Als nucleaire operator
  Wil ik weten of mijn kerninstallatie voldoet aan de administratieve eisen
  Zodat ik een vergunning kan krijgen

  Background:
    Given de datum is "2024-07-01"

  Scenario: Alle administratieve eisen voldaan
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 2                  |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "true"
    And is het veld "beveiligingsplan_voldoet" gelijk aan "true"
    And is het veld "noodplan_voldoet" gelijk aan "true"
    And is het veld "deskundigheid_voldoende" gelijk aan "true"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "true"

  Scenario: Financiële zekerheid te laag
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 50000000                    | 2                  |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"

  Scenario: Geen beveiligingsplan
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | false                  | true           | 100000000                   | 2                  |
    Then is het veld "beveiligingsplan_voldoet" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"

  Scenario: Geen noodplan
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | false          | 100000000                   | 2                  |
    Then is het veld "noodplan_voldoet" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"

  Scenario: Onvoldoende deskundigen
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 0                  |
    Then is het veld "deskundigheid_voldoende" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"

  Scenario: Meerdere eisen niet voldaan
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | false                  | false          | 10000000                    | 0                  |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "false"
    And is het veld "beveiligingsplan_voldoet" gelijk aan "false"
    And is het veld "noodplan_voldoet" gelijk aan "false"
    And is het veld "deskundigheid_voldoende" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"

  Scenario: Minimale financiële zekerheid precies voldoende
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 100000000                   | 1                  |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "true"
    And is het veld "deskundigheid_voldoende" gelijk aan "true"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "true"

  Scenario: Ruim voldoende financiële zekerheid en deskundigen
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | true                   | true           | 500000000                   | 10                 |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "true"
    And is het veld "deskundigheid_voldoende" gelijk aan "true"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "true"

  Scenario: Zeer hoge financiële zekerheid maar geen plannen
    When het besluit_kerninstallaties wordt uitgevoerd door ANVS met parameters:
      | heeft_beveiligingsplan | heeft_noodplan | financiele_zekerheid_bedrag | aantal_deskundigen |
      | false                  | false          | 1000000000                  | 5                  |
    Then is het veld "financiele_zekerheid_gesteld" gelijk aan "true"
    And is het veld "deskundigheid_voldoende" gelijk aan "true"
    And is het veld "beveiligingsplan_voldoet" gelijk aan "false"
    And is het veld "noodplan_voldoet" gelijk aan "false"
    And is het veld "administratieve_eisen_voldaan" gelijk aan "false"
