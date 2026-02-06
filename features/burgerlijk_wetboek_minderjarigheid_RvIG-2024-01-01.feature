@skip-go
Feature: Burgerlijk Wetboek Minderjarigheid - Handelingsbekwaamheid
  Als minderjarige
  Wil ik weten wat mijn rechten zijn
  Zodat ik weet wat ik zelf kan doen

  Background:
    Given de datum is "2025-03-01"

  Scenario: Minderjarige (14 jaar) heeft alleen leesrecht
    # Art. 1:234 BW: minderjarigen handelingsonbekwaam zonder toestemming
    Given een persoon met BSN "200000001"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting |
      | 200000001 | 2011-06-15    | false              |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" waar
    And heeft de output "leeftijd" waarde "13"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" niet de waarde "CLAIMS_INDIENEN"

  Scenario: Meerderjarige (19 jaar) heeft volledige rechten
    # Art. 1:233 BW: meerderjarigen zijn volledig handelingsbekwaam
    Given een persoon met BSN "300000001"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting |
      | 300000001 | 2006-01-01    | false              |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" onwaar
    And heeft de output "leeftijd" waarde "19"
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"
    And bevat de output "base_permissions" waarde "BESLUITEN_ONTVANGEN"

  Scenario: Minderjarige (17 jaar) met handlichting heeft volledige rechten
    # Art. 1:235 BW: handlichting voor 16/17 jarigen
    Given een persoon met BSN "400000001"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting | handlichting_gebieden     |
      | 400000001 | 2008-03-20    | true               | ["BEROEP_BEDRIJF"]        |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" waar
    And heeft de output "leeftijd" waarde "16"
    And is de output "heeft_handlichting" waar
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"
    And bevat de output "handlichting_gebieden" waarde "BEROEP_BEDRIJF"

  Scenario: Net 18 geworden - meerderjarig
    # Art. 1:233 BW: precies 18 = meerderjarig
    Given een persoon met BSN "500000001"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting |
      | 500000001 | 2007-03-01    | false              |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" onwaar
    And heeft de output "leeftijd" waarde "18"
    And bevat de output "base_permissions" waarde "CLAIMS_INDIENEN"

  Scenario: Bijna 18 - nog minderjarig
    # Art. 1:233 BW: 17 jaar en 364 dagen = nog minderjarig
    Given een persoon met BSN "600000001"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting |
      | 600000001 | 2007-03-02    | false              |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" waar
    And heeft de output "leeftijd" waarde "17"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" niet de waarde "CLAIMS_INDIENEN"

  Scenario: Kind van 5 jaar heeft alleen leesrecht
    Given een persoon met BSN "200000002"
    And de volgende RvIG personen gegevens
      | bsn       | geboortedatum | heeft_handlichting |
      | 200000002 | 2020-01-01    | false              |
    When de burgerlijk_wetboek_minderjarigheid wordt uitgevoerd door RvIG
    Then is de output "is_minderjarig" waar
    And heeft de output "leeftijd" waarde "5"
    And bevat de output "base_permissions" waarde "LEZEN"
    And bevat de output "base_permissions" niet de waarde "CLAIMS_INDIENEN"
