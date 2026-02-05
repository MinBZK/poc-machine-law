Feature: Burgerlijk Wetboek Gezag - Delegation provider for minors
  Als ouder of voogd
  Wil ik namens mijn minderjarige kind kunnen handelen
  Zodat ik regelingen kan aanvragen voor mijn kind

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"

  Scenario: Ouder met ouderlijk gezag heeft delegatie
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind    | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 888887654 | Jan Jansen   | 2015-03-15         | OUDERLIJK_GEZAG | 2015-03-15   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "888887654"
    And bevat de output "subject_names" waarde "Jan Jansen"
    And bevat de output "subject_types" waarde "CITIZEN"
    And bevat de output "delegation_types" waarde "OUDERLIJK_GEZAG"

  Scenario: Persoon zonder gezagsrelaties heeft geen delegaties
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 111111111       | 222222222 | Kind Test | 2015-03-15         | OUDERLIJK_GEZAG | 2015-03-15   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "false"

  Scenario: Ouder met meerdere kinderen heeft meerdere delegaties
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind    | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 888887654 | Jan Jansen   | 2015-03-15         | OUDERLIJK_GEZAG | 2015-03-15   |             | ACTIEF | false              |
      | 999993653       | 777776543 | Marie Jansen | 2018-06-20         | OUDERLIJK_GEZAG | 2018-06-20   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "888887654"
    And bevat de output "subject_ids" waarde "777776543"

  Scenario: Kind van 18 jaar of ouder wordt niet meegenomen
    # Art. 1:233 BW: minderjarigen zijn personen onder 18 jaar
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind      | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 666665432 | Piet Jansen    | 2006-01-01         | OUDERLIJK_GEZAG | 2006-01-01   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "false"
    And is de output "subject_ids" leeg

  Scenario: Voogd heeft delegatie
    # Art. 1:295 BW: voogdij door niet-ouder
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind     | geboortedatum_kind | type_gezag | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 555554321 | Anna de Vries | 2017-09-10         | VOOGDIJ    | 2020-01-15   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "555554321"
    And bevat de output "delegation_types" waarde "VOOGDIJ"

  Scenario: Gezamenlijk gezag - ouder heeft delegatie
    # Art. 1:253b BW: gezamenlijk gezag
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind    | geboortedatum_kind | type_gezag        | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 444443210 | Sophie Klein | 2019-04-25         | GEZAMENLIJK_GEZAG | 2019-04-25   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "delegation_types" waarde "GEZAMENLIJK_GEZAG"

  Scenario: Inactief gezag wordt niet meegenomen
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind    | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status   | heeft_handlichting |
      | 999993653       | 333332109 | Tim Bakker   | 2016-11-30         | OUDERLIJK_GEZAG | 2016-11-30   |             | INACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "false"

  Scenario: Beeindigd gezag wordt niet meegenomen
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind    | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 222220987 | Lisa Smit    | 2014-08-12         | OUDERLIJK_GEZAG | 2014-08-12   | 2023-06-01  | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "false"

  Scenario: Mix van minderjarige en meerderjarige kinderen
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind      | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 111110876 | Mark Jansen    | 2003-02-28         | OUDERLIJK_GEZAG | 2003-02-28   |             | ACTIEF | false              |
      | 999993653       | 999990765 | Eva Jansen     | 2012-07-14         | OUDERLIJK_GEZAG | 2012-07-14   |             | ACTIEF | false              |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "999990765"
    And bevat de output "subject_ids" niet de waarde "111110876"

  Scenario: Kind met handlichting - ouder heeft beperkte rechten
    # Art. 1:235 BW: handlichting voor 16/17 jarigen
    # Kind kan dan zelf handelen, ouder heeft beperkte rechten
    Given de volgende RvIG gezag_relaties gegevens
      | bsn_gezagdrager | bsn_kind  | naam_kind      | geboortedatum_kind | type_gezag      | datum_ingang | datum_einde | status | heeft_handlichting |
      | 999993653       | 123456789 | Tom de Jong    | 2008-06-15         | OUDERLIJK_GEZAG | 2008-06-15   |             | ACTIEF | true               |
    When de burgerlijk_wetboek_gezag wordt uitgevoerd door RvIG
    Then heeft de output "heeft_delegaties" waarde "true"
    And bevat de output "subject_ids" waarde "123456789"
    And bevat de output "permissions" waarde "['LEZEN']"
