@skip-go
Feature: Machtigingenwet - Delegation provider for KVK
  Als ondernemer
  Wil ik namens mijn bedrijf kunnen handelen
  Zodat ik regelingen kan aanvragen voor mijn onderneming

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"

  Scenario: Ondernemer met actieve inschrijving heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam       | rechtsvorm  | status | functie  | bevoegdheid |
      | 999993653 | 12345678   | Test Onderneming  | EENMANSZAAK | ACTIEF | EIGENAAR | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "12345678"
    And bevat de output "subject_names" waarde "Test Onderneming"
    And bevat de output "subject_types" waarde "BUSINESS"
    And bevat de output "delegation_types" waarde "EIGENAAR"

  Scenario: Persoon zonder inschrijvingen heeft geen delegaties
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam | rechtsvorm  | status | functie  | bevoegdheid |
      | 111111111 | 00000000   | Leeg        | EENMANSZAAK | ACTIEF | EIGENAAR | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" onwaar

  Scenario: Ondernemer met meerdere bedrijven heeft meerdere delegaties
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam    | rechtsvorm  | status | functie  | bevoegdheid |
      | 999993653 | 11111111   | Bedrijf Een    | EENMANSZAAK | ACTIEF | EIGENAAR | VOLLEDIG    |
      | 999993653 | 22222222   | Bedrijf Twee   | VOF         | ACTIEF | VENNOOT  | BEPERKT     |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "11111111"
    And bevat de output "subject_ids" waarde "22222222"

  Scenario: Commissaris heeft geen vertegenwoordigingsbevoegdheid
    # Art. 2:240 BW: alleen bestuurders, eigenaren en gemachtigden zijn bevoegd
    # Commissarissen zijn toezichthouders en hebben GEEN vertegenwoordigingsbevoegdheid
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam      | rechtsvorm | status | functie     | bevoegdheid |
      | 999993653 | 33333333   | Holdings BV      | BV         | ACTIEF | COMMISSARIS | GEEN        |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" onwaar
    And is de output "subject_ids" leeg

  Scenario: Gemengde rollen - alleen bevoegde functies krijgen delegatie
    # Persoon heeft meerdere functies bij verschillende bedrijven
    # Alleen EIGENAAR en VENNOOT zijn bevoegd, COMMISSARIS niet
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam           | rechtsvorm  | status | functie     | bevoegdheid |
      | 999993653 | 44444444   | Eigen Bedrijf         | EENMANSZAAK | ACTIEF | EIGENAAR    | VOLLEDIG    |
      | 999993653 | 55555555   | Zorggroep VOF         | VOF         | ACTIEF | VENNOOT     | BEPERKT     |
      | 999993653 | 66666666   | Toezicht Holdings BV  | BV          | ACTIEF | COMMISSARIS | GEEN        |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "44444444"
    And bevat de output "subject_ids" waarde "55555555"
    And bevat de output "subject_ids" niet de waarde "66666666"
    And bevat de output "subject_names" waarde "Eigen Bedrijf"
    And bevat de output "subject_names" waarde "Zorggroep VOF"
    And bevat de output "subject_names" niet de waarde "Toezicht Holdings BV"
    And bevat de output "delegation_types" waarde "EIGENAAR"
    And bevat de output "delegation_types" waarde "VENNOOT"
    And bevat de output "delegation_types" niet de waarde "COMMISSARIS"

  Scenario: Bestuurder van BV heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam      | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 77777777   | Tech Solutions BV| BV         | ACTIEF | BESTUURDER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "77777777"
    And bevat de output "delegation_types" waarde "BESTUURDER"

  Scenario: Gemachtigde heeft delegatie
    # Art. 2:240 lid 4 BW: statuten kunnen ook aan anderen bevoegdheid toekennen
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam    | rechtsvorm | status | functie     | bevoegdheid |
      | 999993653 | 88888888   | Groot Bedrijf BV| BV        | ACTIEF | GEMACHTIGDE | BEPERKT     |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "88888888"
    And bevat de output "delegation_types" waarde "GEMACHTIGDE"

  # ===== NV (Naamloze Vennootschap) =====
  # Art. 2:130 BW - representation authority for NV

  Scenario: Bestuurder van NV heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam      | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000001   | Grote Holding NV | NV         | ACTIEF | BESTUURDER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000001"
    And bevat de output "delegation_types" waarde "BESTUURDER"

  Scenario: Directeur van NV heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam       | rechtsvorm | status | functie   | bevoegdheid |
      | 999993653 | 90000002   | Beursgenoteerd NV | NV         | ACTIEF | DIRECTEUR | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "delegation_types" waarde "DIRECTEUR"

  # ===== Stichting (Foundation) =====
  # Art. 2:291-292 BW - representation by foundation board

  Scenario: Bestuurder van Stichting heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam            | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000003   | Stichting Goede Doelen | STICHTING  | ACTIEF | BESTUURDER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000003"
    And bevat de output "subject_names" waarde "Stichting Goede Doelen"
    And bevat de output "delegation_types" waarde "BESTUURDER"

  Scenario: Stichting met beperkte bevoegdheid
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam         | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000004   | Stichting Onderwijs | STICHTING  | ACTIEF | BESTUURDER | BEPERKT     |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "permissions" waarde "['LEZEN']"

  # ===== Vereniging (Association) =====
  # Art. 2:45 BW - representation by association board

  Scenario: Bestuurder van Vereniging heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam             | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000005   | Sportvereniging De Hoop | VERENIGING | ACTIEF | BESTUURDER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000005"
    And bevat de output "delegation_types" waarde "BESTUURDER"

  Scenario: Voorzitter van Vereniging heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam      | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000006   | Muziekvereniging | VERENIGING | ACTIEF | VOORZITTER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "delegation_types" waarde "VOORZITTER"

  # ===== Coöperatie (Cooperative) =====
  # Art. 2:53a BW - representation by cooperative board

  Scenario: Bestuurder van Coöperatie heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam           | rechtsvorm | status | functie    | bevoegdheid |
      | 999993653 | 90000007   | Coöperatie Boeren U.A.| COOPERATIE | ACTIEF | BESTUURDER | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000007"
    And bevat de output "delegation_types" waarde "BESTUURDER"

  # ===== Maatschap (Professional Partnership) =====
  # Art. 7A:1655 BW - representation by partners

  Scenario: Maat in Maatschap heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam              | rechtsvorm | status | functie | bevoegdheid |
      | 999993653 | 90000008   | Advocatenmaatschap Recht | MAATSCHAP  | ACTIEF | MAAT    | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000008"
    And bevat de output "delegation_types" waarde "MAAT"

  # ===== Commanditaire Vennootschap (CV) =====
  # Art. 19 Wetboek van Koophandel - only beherend vennoot represents

  Scenario: Beherend vennoot van CV heeft delegatie
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam  | rechtsvorm              | status | functie          | bevoegdheid |
      | 999993653 | 90000009   | Investeer CV | COMMANDITAIRE_VENNOOTSCHAP | ACTIEF | BEHEREND_VENNOOT | VOLLEDIG    |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" waar
    And bevat de output "subject_ids" waarde "90000009"
    And bevat de output "delegation_types" waarde "BEHEREND_VENNOOT"

  Scenario: Commanditair vennoot van CV heeft GEEN delegatie
    # Stille vennoot mag niet naar buiten treden (art. 20 WvK)
    Given de volgende KVK functionarissen gegevens
      | bsn       | kvk_nummer | handelsnaam | rechtsvorm                 | status | functie              | bevoegdheid |
      | 999993653 | 90000010   | Kapitaal CV | COMMANDITAIRE_VENNOOTSCHAP | ACTIEF | COMMANDITAIR_VENNOOT | GEEN        |
    When de machtigingenwet wordt uitgevoerd door KVK
    Then is de output "heeft_delegaties" onwaar
