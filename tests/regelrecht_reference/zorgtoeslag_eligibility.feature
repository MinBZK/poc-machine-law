Feature: Zorgtoeslag eligibility

  Background:
    Given the calculation date is "2025-01-01"
    Given law "wet_basisregistratie_personen" is loaded
    Given law "zorgverzekeringswet" is loaded
    Given law "penitentiaire_beginselenwet" is loaded
    Given law "regeling_standaardpremie" is loaded
    Given law "algemene_wet_inkomensafhankelijke_regelingen" is loaded
    Given law "wet_inkomstenbelasting_2001" is loaded
    Given law "wet_forensische_zorg" is loaded

  Scenario: Meerderjarige met actieve polis heeft recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2005-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 79547                     | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 209692

  # NB: Engine currently returns true for minors — age check was removed (#375)
  # because AWIR Art 10 (verzekeringsplicht vs meeverzekerd) is not yet modeled.
  # This scenario asserts false as the desired outcome, not the current engine result.
  Scenario: Minderjarige heeft geen recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2008-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 0                         | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is false

  Scenario: Laag inkomen alleenstaande heeft recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1998-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 20000                     | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 10000     | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 210821

  Scenario: Student met studiefinanciering heeft recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 2004-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 15000                     | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given the following "inschrijvingen" data with key "bsn":
      | bsn       | onderwijstype |
      | 999993653 | WO            |
    Given the following "studiefinanciering" data with key "bsn":
      | bsn       | aantal_studerend_gezin |
      | 999993653 | 0                      |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 210916

  # NB: Gezamenlijk toetsingsinkomen is NOT YET implemented (#377).
  # Expected amount reflects applicant income only, not combined partner income.
  # Blocked by engine limitation: conditional cross-law input resolution.
  Scenario: Partner met gecombineerd inkomen heeft recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | HUWELIJK          | 999993654   |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 3500000                   | 0                         | 0                     | 0                               | 0            | 0                   |
      | 999993654 | 2000000                   | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
      | 999993654 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
      | 999993654 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 272845

  # NB: Toetsingsinkomen excludes box3 — Art 5.2a forfaitair rendement is not
  # yet implemented (#383). Only box1 income counts toward the toeslag amount.
  Scenario: Alleenstaande met box3 vermogen heeft recht op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 2000000                   | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 7000000   | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 173280

  Scenario: Verdragsinschrijving geeft verzekeringsdekking bij inactieve polis
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1985-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | VERLOPEN     | true                 |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 25000                     | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | null     | null                 |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 210726

  # NB: Forensische zorg exclusion was removed as scope violation (#375).
  # It belongs in Zvw Art 24 or Wfz, not in the zorgtoeslag law.
  Scenario: Forensische zorg heeft geen invloed op zorgtoeslag
    Given the following "personal_data" data with key "bsn":
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1985-01-01    | Amsterdam      | NEDERLAND     |
    Given the following "relationship_data" data with key "bsn":
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    Given the following "insurance" data with key "bsn":
      | bsn       | polis_status | verdragsinschrijving |
      | 999993653 | ACTIEF       | false                |
    Given the following "box1" data with key "bsn":
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning | buitenlands_inkomen |
      | 999993653 | 25000                     | 0                         | 0                     | 0                               | 0            | 0                   |
    Given the following "box2" data with key "bsn":
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    Given the following "box3" data with key "bsn":
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 0         | 0           | 0              | 0        |
    Given the following "detenties" data with key "bsn":
      | bsn       | detentiestatus | inrichting_type | zorgtype | juridische_grondslag |
      | 999993653 | null           | null            | GGZ      | TBS                  |
    Given parameter "bsn" is "999993653"
    When I evaluate "heeft_recht_op_zorgtoeslag" of "zorgtoeslagwet"
    Then the execution succeeds
    Then output "heeft_recht_op_zorgtoeslag" is true
    Then output "hoogte_zorgtoeslag" equals 210726
