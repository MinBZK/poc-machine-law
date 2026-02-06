@skip-go
Feature: Landelijke Aanpak Adreskwaliteit (LAA)
  Als RvIG
  Wil ik signalen genereren over mogelijk onjuiste adresregistraties
  Zodat gemeenten de adreskwaliteit in de BRP kunnen verbeteren

  Background:
    Given de datum is "2025-03-01"

  Scenario: Belastingdienst meldt twijfel over adres - genereert signaal type MELDING
    Given een persoon met BSN "999993653"
    And de volgende BELASTINGDIENST terugmelding gegevens:
      | bsn       | postcode | huisnummer | heeft_gerede_twijfel_adres |
      | 999993653 | 1234AB   | 10         | true                       |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel | is_woonfunctie |
      | 1234AB   | 10         | woonfunctie  | true           |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "1234AB", "huisnummer": "10"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" waar
    And heeft de output "signaal_type" waarde "MELDING"
    And heeft de output "reactietermijn_weken" waarde "4"
    And heeft de output "onderzoekstermijn_maanden" waarde "6"

  Scenario: Toeslagen meldt twijfel over adres - genereert signaal type MELDING
    Given een persoon met BSN "999993654"
    And de volgende TOESLAGEN terugmelding gegevens:
      | bsn       | postcode | huisnummer | heeft_gerede_twijfel_adres |
      | 999993654 | 5678CD   | 25         | true                       |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel | is_woonfunctie |
      | 5678CD   | 25         | woonfunctie  | true           |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "5678CD", "huisnummer": "25"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" waar
    And heeft de output "signaal_type" waarde "MELDING"

  Scenario: CJIB meldt twijfel over adres - genereert signaal type MELDING
    Given een persoon met BSN "999993655"
    And de volgende CJIB terugmelding gegevens:
      | bsn       | postcode | huisnummer | heeft_gerede_twijfel_adres |
      | 999993655 | 9012EF   | 42         | true                       |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel | is_woonfunctie |
      | 9012EF   | 42         | woonfunctie  | true           |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "9012EF", "huisnummer": "42"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" waar
    And heeft de output "signaal_type" waarde "MELDING"

  Scenario: Profiel "Overbewoning" - hoog aantal bewoners op adres zonder woonfunctie
    Given een persoon met BSN "999993657"
    And de volgende RvIG brp_adressen gegevens:
      | postcode | huisnummer | aantal_bewoners |
      | 3456GH   | 100        | 8               |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | adres                                                    | gebruiksdoel      | is_woonfunctie |
      | 3456GH   | 100        | {"postcode": "3456GH", "huisnummer": "100"}              | kantoorfunctie    | false          |
    And de volgende BELASTINGDIENST belasting_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993657 | 3456GH   | 100        |
    And de volgende TOESLAGEN toeslagen_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993657 | 3456GH   | 100        |
    And de volgende CJIB post_onbestelbaar gegevens:
      | bsn       | postcode | huisnummer | onbestelbaar |
      | 999993657 | 3456GH   | 100        | false        |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "3456GH", "huisnummer": "100"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" waar
    And heeft de output "signaal_type" waarde "PROFIEL"
    And heeft de output "reactietermijn_weken" waarde "4"
    And heeft de output "onderzoekstermijn_maanden" waarde "6"

  Scenario: Normaal adres zonder meldingen of profielen - geen signaal
    Given een persoon met BSN "999993658"
    And de volgende RvIG brp_adressen gegevens:
      | postcode | huisnummer | aantal_bewoners |
      | 7890IJ   | 15         | 3               |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel | is_woonfunctie |
      | 7890IJ   | 15         | woonfunctie  | true           |
    And de volgende BELASTINGDIENST belasting_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993658 | 7890IJ   | 15         |
    And de volgende TOESLAGEN toeslagen_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993658 | 7890IJ   | 15         |
    And de volgende CJIB post_onbestelbaar gegevens:
      | bsn       | postcode | huisnummer | onbestelbaar |
      | 999993658 | 7890IJ   | 15         | false        |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "7890IJ", "huisnummer": "15"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" onwaar

  Scenario: Hoog aantal bewoners maar met woonfunctie - geen signaal
    Given een persoon met BSN "999993659"
    And de volgende RvIG brp_adressen gegevens:
      | postcode | huisnummer | aantal_bewoners |
      | 2345KL   | 200        | 8               |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | adres                                                    | gebruiksdoel | is_woonfunctie |
      | 2345KL   | 200        | {"postcode": "2345KL", "huisnummer": "200"}              | woonfunctie  | true           |
    And de volgende BELASTINGDIENST belasting_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993659 | 2345KL   | 200        |
    And de volgende TOESLAGEN toeslagen_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993659 | 2345KL   | 200        |
    And de volgende CJIB post_onbestelbaar gegevens:
      | bsn       | postcode | huisnummer | onbestelbaar |
      | 999993659 | 2345KL   | 200        | false        |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "2345KL", "huisnummer": "200"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" onwaar

  Scenario: Adres zonder woonfunctie maar met laag aantal bewoners - geen signaal
    Given een persoon met BSN "999993660"
    And de volgende RvIG brp_adressen gegevens:
      | postcode | huisnummer | aantal_bewoners |
      | 6789MN   | 50         | 2               |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel      | is_woonfunctie |
      | 6789MN   | 50         | kantoorfunctie    | false          |
    And de volgende BELASTINGDIENST belasting_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993660 | 6789MN   | 50         |
    And de volgende TOESLAGEN toeslagen_adressen gegevens:
      | bsn       | postcode | huisnummer |
      | 999993660 | 6789MN   | 50         |
    And de volgende CJIB post_onbestelbaar gegevens:
      | bsn       | postcode | huisnummer | onbestelbaar |
      | 999993660 | 6789MN   | 50         | false        |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "6789MN", "huisnummer": "50"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" onwaar

  Scenario: Combinatie van melding en profiel - signaal type blijft MELDING
    Given een persoon met BSN "999993656"
    And de volgende BELASTINGDIENST terugmelding gegevens:
      | bsn       | postcode | huisnummer | heeft_gerede_twijfel_adres |
      | 999993656 | 4567OP   | 75         | true                       |
    And de volgende RvIG brp_adressen gegevens:
      | postcode | huisnummer | aantal_bewoners |
      | 4567OP   | 75         | 10              |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | postcode | huisnummer | gebruiksdoel      | is_woonfunctie |
      | 4567OP   | 75         | kantoorfunctie    | false          |
    When de wet_brp/laa wordt uitgevoerd door RvIG met
      | ADRES |
      | {"postcode": "4567OP", "huisnummer": "75"} |
    Then is voldaan aan de voorwaarden
    And is de output "genereer_signaal" waar
    And heeft de output "signaal_type" waarde "MELDING"
