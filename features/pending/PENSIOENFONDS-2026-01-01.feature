Feature: Pensioenwet - Pensioenuitkering berekening
  Als pensioengerechtigde
  Wil ik weten wat mijn pensioenuitkering is
  Zodat ik mijn inkomen na pensionering kan plannen

  Background:
    Given de datum is "2026-07-01"

  Scenario: Gepensioneerde met beschikbare premieregeling
    Given een persoon met BSN "100000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000001 | 1959-03-15    | Amsterdam      |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling      | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000001 | 30000000         | 40            | beschikbare_premie | 67               | 1750000   | 6000000             |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is voldaan aan de voorwaarden
    And heeft de output "is_gepensioneerd" waarde "true"
    And heeft de output "pensioenkapitaal" waarde "30000000"
    And is het pensioen "15000.00" euro

  Scenario: Gepensioneerde met middelloonregeling
    Given een persoon met BSN "100000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000002 | 1958-06-20    | Rotterdam      |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000002 | 25000000         | 35            | middelloon    | 67               | 1750000   | 5500000             |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is voldaan aan de voorwaarden
    And heeft de output "is_gepensioneerd" waarde "true"
    # Berekening: 0.0175 * 35 * (5500000 - 1750000) = 0.6125 * 3750000 = 2296875 eurocent = 22968.75 euro
    And is het pensioen "22968.75" euro

  Scenario: Gepensioneerde met eindloonregeling
    Given een persoon met BSN "100000003"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000003 | 1957-01-10    | Utrecht        |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000003 | 40000000         | 40            | eindloon      | 67               | 1750000   | 7000000             |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is voldaan aan de voorwaarden
    And heeft de output "is_gepensioneerd" waarde "true"
    # Berekening: 0.0167 * 40 * (7000000 - 1750000) = 0.668 * 5250000 = 3507000 eurocent = 35070.00 euro
    And is het pensioen "35070.00" euro

  Scenario: Persoon nog niet pensioengerechtigd
    Given een persoon met BSN "100000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000004 | 1970-08-25    | Den Haag       |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling      | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000004 | 15000000         | 20            | beschikbare_premie | 67               | 1750000   | 5000000             |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is niet voldaan aan de voorwaarden

  Scenario: Persoon zonder pensioenkapitaal
    Given een persoon met BSN "100000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000005 | 1958-12-01    | Eindhoven      |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling      | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000005 | 0                | 0             | beschikbare_premie | 67               | 0         | 0                   |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is niet voldaan aan de voorwaarden

  Scenario: Vervroegd pensioen bij lagere pensioenleeftijd
    Given een persoon met BSN "100000006"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 100000006 | 1961-04-15    | Groningen      |
    And de volgende PENSIOENFONDS pensioen_deelnemers gegevens:
      | bsn       | pensioenkapitaal | pensioenjaren | type_regeling      | pensioenleeftijd | franchise | pensioengevend_loon |
      | 100000006 | 20000000         | 30            | beschikbare_premie | 65               | 1750000   | 5000000             |
    When de pensioenwet wordt uitgevoerd door PENSIOENFONDS
    Then is voldaan aan de voorwaarden
    And heeft de output "pensioenleeftijd" waarde "65"
    And is het pensioen "10000.00" euro
