Feature: KVK Vertegenwoordiging
  Als overheidsorganisatie
  Wil ik kunnen valideren of een persoon bevoegd is om te handelen namens een bedrijf
  Zodat alleen rechtmatige vertegenwoordigers namens bedrijven kunnen handelen

  Background:
    Given de datum is "2025-10-16"

  # ===== POSITIEVE SCENARIOS =====

  Scenario: Directeur-grootaandeelhouder mag handelen namens eigen BV (zelfstandig bevoegd)
    Given een persoon met BSN "100000001"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 001234567  | 12345678   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 100000001 | 001234567  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2020-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 100000001   | 001234567 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"
    And is functie "BESTUURDER"

  Scenario: Bestuurder mag handelen namens stichting
    Given een persoon met BSN "200000001"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 003456789  | 34567890   | STICHTING  | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 200000001 | 003456789  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2018-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 200000001   | 003456789 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"

  Scenario: Vennoot mag handelen namens VOF (gezamenlijk bevoegd)
    Given een persoon met BSN "100000011"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 002345678  | 23456789   | VOF        | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie  | bevoegdheid  | status  | ingangsdatum | einddatum |
      | 100000011 | 002345678  | VENNOOT  | GEZAMENLIJK  | ACTIEF  | 2019-06-01   | null      |
      | 300000001 | 002345678  | VENNOOT  | GEZAMENLIJK  | ACTIEF  | 2019-06-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 100000011   | 002345678 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "GEZAMENLIJK"
    And is functie "VENNOOT"

  Scenario: Enig bestuurder NV mag handelen namens NV
    Given een persoon met BSN "300000022"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 005678901  | 56789012   | NV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000022 | 005678901  | DIRECTEUR  | ZELFSTANDIG | ACTIEF  | 2021-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000022   | 005678901 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"
    And is functie "DIRECTEUR"

  Scenario: Beherend vennoot mag handelen namens CV
    Given een persoon met BSN "300000041"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 007890123  | 78901234   | CV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie          | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000041 | 007890123  | BEHEREND_VENNOOT | ZELFSTANDIG | ACTIEF  | 2020-09-01   | null      |
      | 300000042 | 007890123  | STILLE_VENNOOT   | GEEN        | ACTIEF  | 2020-09-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000041   | 007890123 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"
    And is functie "BEHEREND_VENNOOT"

  Scenario: Zaakvoerder mag handelen namens Maatschap
    Given een persoon met BSN "300000031"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 006789012  | 67890123   | MAATSCHAP  | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie      | bevoegdheid  | status  | ingangsdatum | einddatum |
      | 300000031 | 006789012  | ZAAKVOERDER  | GEZAMENLIJK  | ACTIEF  | 2017-03-15   | null      |
      | 300000032 | 006789012  | ZAAKVOERDER  | GEZAMENLIJK  | ACTIEF  | 2017-03-15   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000031   | 006789012 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "GEZAMENLIJK"
    And is functie "ZAAKVOERDER"

  # ===== NEGATIEVE SCENARIOS =====

  Scenario: Ex-bestuurder mag NIET handelen namens BV (einddatum = vorig jaar)
    Given een persoon met BSN "300000011"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 004567890  | 45678901   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status     | ingangsdatum | einddatum  |
      | 300000011 | 004567890  | BESTUURDER | ZELFSTANDIG | BEËINDIGD  | 2020-01-01   | 2023-12-31 |
      | 300000012 | 004567890  | BESTUURDER | ZELFSTANDIG | ACTIEF     | 2024-01-01   | null       |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000011   | 004567890 |
    Then is niet voldaan aan de voorwaarden

  Scenario: Aandeelhouder zonder bestuursfunctie mag NIET handelen namens BV
    Given een persoon met BSN "300000072"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 000123456  | 01234567   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie       | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000071 | 000123456  | BESTUURDER    | ZELFSTANDIG | ACTIEF  | 2020-03-01   | null      |
      | 300000072 | 000123456  | AANDEELHOUDER | GEEN        | ACTIEF  | 2020-03-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000072   | 000123456 |
    Then is niet voldaan aan de voorwaarden

  Scenario: Commissaris mag NIET handelen namens NV (toezicht, geen vertegenwoordiging)
    Given een persoon met BSN "300000021"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 005678901  | 56789012   | NV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie     | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000021 | 005678901  | COMMISSARIS | GEEN        | ACTIEF  | 2021-01-01   | null      |
      | 300000022 | 005678901  | DIRECTEUR   | ZELFSTANDIG | ACTIEF  | 2021-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000021   | 005678901 |
    Then is niet voldaan aan de voorwaarden

  Scenario: Stille vennoot mag NIET handelen namens CV (geen vertegenwoordiging)
    Given een persoon met BSN "300000042"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 007890123  | 78901234   | CV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie          | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000041 | 007890123  | BEHEREND_VENNOOT | ZELFSTANDIG | ACTIEF  | 2020-09-01   | null      |
      | 300000042 | 007890123  | STILLE_VENNOOT   | GEEN        | ACTIEF  | 2020-09-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000042   | 007890123 |
    Then is niet voldaan aan de voorwaarden

  Scenario: Gewezen functionaris mag NIET handelen namens BV (status = BEËINDIGD)
    Given een persoon met BSN "300000011"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 004567890  | 45678901   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status     | ingangsdatum | einddatum  |
      | 300000011 | 004567890  | BESTUURDER | ZELFSTANDIG | BEËINDIGD  | 2020-01-01   | 2023-12-31 |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000011   | 004567890 |
    Then is niet voldaan aan de voorwaarden

  # ===== EDGE CASES =====

  Scenario: Bestuurder met beperkte bevoegdheid mag ALLEEN met anderen handelen (niet zelfstandig)
    Given een persoon met BSN "300000063"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 009012345  | 90123456   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000061 | 009012345  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2019-01-01   | null      |
      | 300000062 | 009012345  | BESTUURDER | GEZAMENLIJK | ACTIEF  | 2020-01-01   | null      |
      | 300000063 | 009012345  | BESTUURDER | BEPERKT     | ACTIEF  | 2021-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000063   | 009012345 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "BEPERKT"
    And is functie "BESTUURDER"

  Scenario: Persoon zonder enige functie in bedrijf mag NIET handelen
    Given een persoon met BSN "999999999"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 001234567  | 12345678   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 100000001 | 001234567  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2020-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 999999999   | 001234567 |
    Then is niet voldaan aan de voorwaarden

  Scenario: Eigenaar eenmanszaak mag handelen namens eigen bedrijf
    Given een persoon met BSN "300000051"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm    | status  |
      | 008901234  | 89012345   | EENMANSZAAK   | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie   | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000051 | 008901234  | EIGENAAR  | ZELFSTANDIG | ACTIEF  | 2022-05-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000051   | 008901234 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"
    And is functie "EIGENAAR"

  Scenario: Procuratiehouder mag handelen namens NV (beperkte bevoegdheid)
    Given een persoon met BSN "230000031"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 001122334  | 11223344   | NV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie           | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000081 | 001122334  | DIRECTEUR         | ZELFSTANDIG | ACTIEF  | 2018-06-01   | null      |
      | 230000031 | 001122334  | PROCURATIEHOUDER  | BEPERKT     | ACTIEF  | 2023-06-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 230000031   | 001122334 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "BEPERKT"
    And is functie "PROCURATIEHOUDER"

  Scenario: Bestuurder met einddatum in toekomst mag nog steeds handelen
    Given een persoon met BSN "300000101"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 010101010  | 10101010   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum  |
      | 300000101 | 010101010  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2020-01-01   | 2026-12-31 |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000101   | 010101010 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"

  Scenario: Meerdere bestuurders met verschillende bevoegdheden - zelfstandig bevoegde mag handelen
    Given een persoon met BSN "300000061"
    And de volgende KVK inschrijvingen gegevens:
      | rsin       | kvk_nummer | rechtsvorm | status  |
      | 009012345  | 90123456   | BV         | ACTIEF  |
    And de volgende KVK functionarissen gegevens:
      | bsn       | rsin       | functie    | bevoegdheid | status  | ingangsdatum | einddatum |
      | 300000061 | 009012345  | BESTUURDER | ZELFSTANDIG | ACTIEF  | 2019-01-01   | null      |
      | 300000062 | 009012345  | BESTUURDER | GEZAMENLIJK | ACTIEF  | 2020-01-01   | null      |
      | 300000063 | 009012345  | BESTUURDER | BEPERKT     | ACTIEF  | 2021-01-01   | null      |
    When de handelsregisterwet/vertegenwoordiging wordt uitgevoerd door KVK met
      | BSN_PERSOON | RSIN      |
      | 300000061   | 009012345 |
    Then is voldaan aan de voorwaarden
    And is mag_vertegenwoordigen true
    And is bevoegdheid "ZELFSTANDIG"
