Feature: Wet-synthese uit simulatieresultaten
  Als beleidsmaker
  Wil ik een vereenvoudigde wet kunnen genereren uit simulatieresultaten
  Zodat ik complexe toeslagwetten kan harmoniseren

  Background:
    Given de simulatie omgeving is geinitialiseerd

  Scenario: Genereer geharmoniseerde toeslag
    Given een gesimuleerde populatie van 500 personen
    When de wet-synthese wordt uitgevoerd
    Then wordt een model getraind met eligibility regels
    And wordt een model getraind met bedrag formules
    And de eligibility accuracy is minstens 80 procent

  Scenario: Genereer valide Machine Law YAML
    Given een gesimuleerde populatie van 500 personen
    And de wet-synthese is uitgevoerd
    When de YAML wordt gegenereerd
    Then bevat de YAML geldige requirements
    And bevat de YAML geldige actions
    And kan de YAML worden geparsed

  Scenario: Valideer gesynthetiseerde wet
    Given een gesimuleerde populatie van 500 personen
    And de wet-synthese is uitgevoerd
    When de validatie wordt uitgevoerd
    Then worden per-groep metrics berekend
    And worden aanbevelingen gegenereerd
    And wordt een validatierapport gemaakt

  Scenario: Genereer Nederlandse uitleg
    Given een gesimuleerde populatie van 500 personen
    And de wet-synthese is uitgevoerd
    When de Nederlandse uitleg wordt gegenereerd
    Then bevat de uitleg voorwaarden in begrijpelijke taal
    And bevat de uitleg een berekeningsuitleg
