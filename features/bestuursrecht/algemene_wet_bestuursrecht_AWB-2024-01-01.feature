@skip-go
Feature: AWB Article 1:1 - Bestuursorgaan Definition
  Als burger of organisatie
  Wil ik weten of een bepaalde instantie een bestuursorgaan is
  Zodat ik weet of de AWB van toepassing is

  Background:
    Given de datum is "2024-01-01"

  # A-organen tests
  Scenario: Gemeente is bestuursorgaan (A-orgaan)
    Given een organisatie met ID "ORG001"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_orgaan_van_rechtspersoon | publiekrechtelijke_rechtspersoon_type |
      | ORG001         | true                        | GEMEENTE                              |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Provincie is bestuursorgaan (A-orgaan)
    Given een organisatie met ID "ORG002"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_orgaan_van_rechtspersoon | publiekrechtelijke_rechtspersoon_type |
      | ORG002         | true                        | PROVINCIE                             |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Waterschap is bestuursorgaan (A-orgaan)
    Given een organisatie met ID "ORG003"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_orgaan_van_rechtspersoon | publiekrechtelijke_rechtspersoon_type |
      | ORG003         | true                        | WATERSCHAP                            |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Rijksorgaan is bestuursorgaan (A-orgaan)
    Given een organisatie met ID "ORG004"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_orgaan_van_rechtspersoon | publiekrechtelijke_rechtspersoon_type |
      | ORG004         | true                        | RIJK                                  |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Openbaar lichaam is bestuursorgaan (A-orgaan)
    Given een organisatie met ID "ORG005"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_orgaan_van_rechtspersoon | publiekrechtelijke_rechtspersoon_type |
      | ORG005         | true                        | OPENBAAR_LICHAAM                      |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  # B-organen tests - non-financial benefits
  Scenario: APK-keuringsinstantie is bestuursorgaan (B-orgaan)
    Given een organisatie met ID "ORG010"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering |
      | ORG010         | true                                 | true                             | false                               |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Notaris met publieke bevoegdheid is bestuursorgaan (B-orgaan)
    Given een organisatie met ID "ORG011"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering |
      | ORG011         | true                                 | true                             | false                               |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Stichting met wettelijke toezichtstaak is bestuursorgaan (B-orgaan)
    Given een organisatie met ID "ORG012"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering |
      | ORG012         | true                                 | true                             | false                               |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  # Two-thirds funding rule tests
  Scenario: Uitkeringsinstantie met 70% overheidsfinanciering is bestuursorgaan
    Given een organisatie met ID "ORG020"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering | overheidsfinanciering_percentage | criteria_door_overheid_bepaald |
      | ORG020         | true                                 | true                             | true                                | 70.0                             | true                           |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Uitkeringsinstantie met precies 66.67% financiering is bestuursorgaan
    Given een organisatie met ID "ORG021"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering | overheidsfinanciering_percentage | criteria_door_overheid_bepaald |
      | ORG021         | true                                 | true                             | true                                | 66.67                            | true                           |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Uitkeringsinstantie met 60% overheidsfinanciering is geen bestuursorgaan
    Given een organisatie met ID "ORG022"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering | overheidsfinanciering_percentage | criteria_door_overheid_bepaald |
      | ORG022         | true                                 | true                             | true                                | 60.0                             | true                           |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: Uitkeringsinstantie met 70% financiering maar eigen criteria is geen bestuursorgaan
    Given een organisatie met ID "ORG023"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering | overheidsfinanciering_percentage | criteria_door_overheid_bepaald |
      | ORG023         | true                                 | true                             | true                                | 70.0                             | false                          |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  # Exclusion tests (Article 1:1 lid 2)
  Scenario: Tweede Kamer is geen bestuursorgaan (volksvertegenwoordiging)
    Given een organisatie met ID "ORG030"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_volksvertegenwoordigend_orgaan |
      | ORG030         | true                              |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: Rechtbank is geen bestuursorgaan (rechterlijk orgaan)
    Given een organisatie met ID "ORG031"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_rechterlijk_orgaan |
      | ORG031         | true                  |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: Nationale Ombudsman is geen bestuursorgaan (expliciet uitgezonderd)
    Given een organisatie met ID "ORG032"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_ombudsman |
      | ORG032         | true         |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: Algemene Rekenkamer is geen bestuursorgaan (expliciet uitgezonderd)
    Given een organisatie met ID "ORG033"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | is_algemene_rekenkamer |
      | ORG033         | true                   |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  # Edge cases
  Scenario: Privaat bedrijf zonder publieke bevoegdheid is geen bestuursorgaan
    Given een organisatie met ID "ORG040"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid |
      | ORG040         | false                                |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: Organisatie met publieke bevoegdheid niet bij wet is geen bestuursorgaan
    Given een organisatie met ID "ORG041"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet |
      | ORG041         | true                                 | false                            |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan

  Scenario: ZBO met publieke bevoegdheid is bestuursorgaan (B-orgaan)
    Given een organisatie met ID "ORG042"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet | is_uitsluitend_financiele_uitkering |
      | ORG042         | true                                 | true                             | false                               |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie een bestuursorgaan

  Scenario: Havenbedrijf Rotterdam is geen bestuursorgaan (privatized port authority)
    Given een organisatie met ID "ORG050"
    And de volgende AWB organisaties gegevens:
      | organisatie_id | heeft_publiekrechtelijke_bevoegdheid | bevoegdheid_bij_of_krachtens_wet |
      | ORG050         | false                                | false                            |
    When de algemene_wet_bestuursrecht wordt uitgevoerd door AWB
    Then is de organisatie geen bestuursorgaan
