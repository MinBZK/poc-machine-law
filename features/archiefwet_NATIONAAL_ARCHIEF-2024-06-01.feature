@skip-go
Feature: Archiefwet 1995 - Beheer en openbaarheid van archiefbescheiden
  Als archivaris
  Wil ik weten of archiefbescheiden overgebracht, openbaar of vernietigd moeten worden
  Zodat ik kan voldoen aan de verplichtingen uit de Archiefwet 1995

  Background:
    Given de datum is "2024-06-01"

  # ===== Artikel 12: Overbrenging =====

  Scenario: Document van 21 jaar oud moet overgebracht worden
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging |
      | DOC-001        | 2003-01-01   | false             |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" waar
    And heeft de output "uiterste_overbrengdatum" waarde "2033-01-01"

  Scenario: Document van 19 jaar oud hoeft nog niet overgebracht te worden
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging |
      | DOC-002        | 2005-01-01   | false             |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" onwaar

  Scenario: Document voor vernietiging wordt niet overgebracht
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging |
      | DOC-003        | 2000-01-01   | true              |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" onwaar

  Scenario: Overbrenging kan opgeschort worden bij veelvuldig gebruik met machtiging
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging | veelvuldig_gebruik | opschortingsmachtiging |
      | DOC-004        | 2000-01-01   | false             | true               | true                   |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" onwaar

  Scenario: Overbrenging kan niet opgeschort worden zonder machtiging
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging | veelvuldig_gebruik | opschortingsmachtiging |
      | DOC-005        | 2000-01-01   | false             | true               | false                  |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" waar

  # ===== Artikel 15: Openbaarheid =====

  Scenario: Overgebracht document zonder beperking is openbaar
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type |
      | DOC-101        | 2000-01-01   | 2020-01-01     | null           |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" waar

  Scenario: Document met privacybeperking is niet openbaar binnen de termijn
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type | beperking_termijn_jaren |
      | DOC-102        | 2000-01-01   | 2020-01-01     | PRIVACY        | 75                      |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" onwaar
    And heeft de output "beperking_reden" waarde "Beperkt vanwege eerbiediging van de persoonlijke levenssfeer"
    And heeft de output "openbaar_vanaf_datum" waarde "2075-01-01"

  Scenario: Document met privacybeperking wordt openbaar na 75 jaar
    Given de datum is "2076-01-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type | beperking_termijn_jaren |
      | DOC-103        | 2000-01-01   | 2020-01-01     | PRIVACY        | 75                      |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" waar

  Scenario: Document met staatsbelang beperking en ministerraadsbesluit blijft beperkt na 75 jaar
    Given de datum is "2076-01-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type | beperking_termijn_jaren | ministerraad_besluit_staatsbelang |
      | DOC-104        | 2000-01-01   | 2020-01-01     | STAATSBELANG   | 75                      | true                              |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" onwaar
    And heeft de output "beperking_reden" waarde "Beperkt vanwege het belang van de Staat of zijn bondgenoten"

  Scenario: Document met staatsbelang beperking zonder ministerraadsbesluit wordt openbaar na 75 jaar
    Given de datum is "2076-01-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type | beperking_termijn_jaren | ministerraad_besluit_staatsbelang |
      | DOC-105        | 2000-01-01   | 2020-01-01     | STAATSBELANG   | 75                      | false                             |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" waar

  Scenario: Document met korte beperking wordt openbaar na termijn
    Given de datum is "2030-01-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | overbrengdatum | beperking_type           | beperking_termijn_jaren |
      | DOC-106        | 2000-01-01   | 2020-01-01     | ONEVENREDIGE_GEVOLGEN    | 10                      |
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" waar

  # ===== Artikel 5: Vernietiging =====

  Scenario: Document op selectielijst mag vernietigd worden na bewaartermijn
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | documenttype   | op_selectielijst_vernietiging | bewaartermijn_jaren | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-201        | 2015-01-01   | FACTUUR        | true                          | 7                   | true                      | true                       |
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" waar
    And heeft de output "vernietig_vanaf_datum" waarde "2022-01-01"

  Scenario: Document op selectielijst mag nog niet vernietigd worden voor einde bewaartermijn
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | documenttype   | op_selectielijst_vernietiging | bewaartermijn_jaren | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-202        | 2020-01-01   | FACTUUR        | true                          | 7                   | true                      | true                       |
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" onwaar
    And heeft de output "reden_niet_vernietigen" waarde "Bewaartermijn is nog niet verstreken"

  Scenario: Document niet op selectielijst mag niet vernietigd worden
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | documenttype      | op_selectielijst_vernietiging | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-203        | 2000-01-01   | BELEIDSDOCUMENT   | false                         | true                      | true                       |
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" onwaar
    And heeft de output "reden_niet_vernietigen" waarde "Archiefstuk komt niet voor op een selectielijst voor vernietiging (mogelijk blijvend te bewaren)"

  Scenario: Document mag niet vernietigd worden als selectielijst niet is vastgesteld
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | documenttype | op_selectielijst_vernietiging | bewaartermijn_jaren | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-204        | 2015-01-01   | FACTUUR      | true                          | 7                   | false                     | true                       |
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" onwaar
    And heeft de output "reden_niet_vernietigen" waarde "Selectielijst is niet formeel vastgesteld volgens artikel 5 lid 2 Archiefwet"

  Scenario: Document mag niet vernietigd worden als selectielijst niet is gepubliceerd
    Given een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | documenttype | op_selectielijst_vernietiging | bewaartermijn_jaren | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-205        | 2015-01-01   | FACTUUR      | true                          | 7                   | true                      | false                      |
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" onwaar
    And heeft de output "reden_niet_vernietigen" waarde "Selectielijst is niet bekendgemaakt in de Staatscourant volgens artikel 5 lid 3 Archiefwet"

  # ===== Geïntegreerde scenario's =====

  Scenario: Document blijvend bewaren: niet voor vernietiging, moet overgebracht, wordt openbaar
    Given de datum is "2024-06-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging | op_selectielijst_vernietiging | overbrengdatum | beperking_type |
      | DOC-301        | 2000-01-01   | false             | false                         | 2020-01-01     | null           |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" waar
    When de archiefwet/openbaarheid wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "is_openbaar" waar
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" onwaar

  Scenario: Document tijdelijk bewaren: voor vernietiging na 10 jaar
    Given de datum is "2026-01-01"
    And een archiefstuk met de volgende eigenschappen:
      | archiefstuk_id | aanmaakdatum | voor_vernietiging | op_selectielijst_vernietiging | bewaartermijn_jaren | selectielijst_vastgesteld | selectielijst_gepubliceerd |
      | DOC-302        | 2015-01-01   | true              | true                          | 10                  | true                      | true                       |
    When de archiefwet/overbrenging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "moet_overgebracht_worden" onwaar
    When de archiefwet/vernietiging wordt uitgevoerd door NATIONAAL_ARCHIEF
    Then is de output "mag_vernietigd_worden" waar
    And heeft de output "vernietig_vanaf_datum" waarde "2025-01-01"
