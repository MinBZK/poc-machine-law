Feature: Besluit basisveiligheidsnormen stralingsbescherming
  Als nucleaire operator
  Wil ik weten of mijn verwachte stralingsdosis binnen de wettelijke limieten blijft
  Zodat ik een vergunning kan krijgen

  Background:
    Given de datum is "2024-07-01"

  Scenario: Stralingsdosis onder alle limieten
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.5                  | 20.0                 | 0.05                 |
    Then is het veld "dosislimiet_overschreden" gelijk aan "false"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "true"
    And is het veld "overschreden_limieten" een lege lijst

  Scenario: Effectieve dosis net op de limiet (1 mSv/jaar)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 1.0                  | 30.0                 | 0.08                 |
    Then is het veld "dosislimiet_overschreden" gelijk aan "false"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "true"
    And is het veld "overschreden_limieten" een lege lijst

  Scenario: Effectieve dosis overschrijdt algemene limiet (>1 mSv/jaar)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 1.5                  | 30.0                 | 0.08                 |
    Then is het veld "dosislimiet_overschreden" gelijk aan "true"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "false"
    And bevat het veld "overschreden_limieten" de waarde "effectieve_dosis_algemeen"

  Scenario: Dosis buiten locatie overschrijdt limiet (>0.1 mSv/jaar)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.8                  | 40.0                 | 0.15                 |
    Then is het veld "dosislimiet_overschreden" gelijk aan "true"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "false"
    And bevat het veld "overschreden_limieten" de waarde "effectieve_dosis_buiten_locatie"

  Scenario: Huiddosis overschrijdt limiet (>50 mSv/jaar)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.7                  | 55.0                 | 0.05                 |
    Then is het veld "dosislimiet_overschreden" gelijk aan "true"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "false"
    And bevat het veld "overschreden_limieten" de waarde "equivalente_dosis_huid"

  Scenario: Meerdere dosislimieten overschreden
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 2.5                  | 60.0                 | 0.3                  |
    Then is het veld "dosislimiet_overschreden" gelijk aan "true"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "false"
    And bevat het veld "overschreden_limieten" de waarde "effectieve_dosis_algemeen"

  Scenario: Zeer lage stralingsdosis (optimalisatie)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar | verwachte_dosis_huid | dosis_buiten_locatie |
      | 0.001                | 0.1                  | 0.0001               |
    Then is het veld "dosislimiet_overschreden" gelijk aan "false"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "true"
    And is het veld "overschreden_limieten" een lege lijst

  Scenario: Alleen algemene dosis opgegeven (andere waarden niet ingevuld)
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar |
      | 0.8                  |
    Then is het veld "dosislimiet_overschreden" gelijk aan "false"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "true"
    And is het veld "overschreden_limieten" een lege lijst

  Scenario: Hoge algemene dosis met alleen algemene waarde opgegeven
    When de besluit_basisveiligheidsnormen_stralingsbescherming wordt uitgevoerd door ANVS met:
      | verwachte_dosis_jaar |
      | 1.2                  |
    Then is het veld "dosislimiet_overschreden" gelijk aan "true"
    And is het veld "vergunning_toegestaan_straling" gelijk aan "false"
    And bevat het veld "overschreden_limieten" de waarde "effectieve_dosis_algemeen"
