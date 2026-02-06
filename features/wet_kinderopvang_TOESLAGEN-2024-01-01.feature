Feature: Berekening Kinderopvangtoeslag
  Als ouder
  Wil ik weten of ik recht heb op kinderopvangtoeslag
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given de datum is "2025-01-15"
    And een persoon met BSN "888888888"

  Scenario: Alleenstaande ouder met jonge kinderen heeft recht op kinderopvangtoeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 888888888 | 1990-05-15    | Amsterdam      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn | kinderen                                     |
      | 888888888 | GEEN              |             | [{"bsn": "111111111"}, {"bsn": "222222222"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 3600000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | verzekerde_jaren |
      | 888888888 | 5             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 888888888 | 2024-01-15 | 2024-01-30 |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er verplichte gegevens
    And is niet voldaan aan de voorwaarden
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                                                                                      | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | KINDEROPVANG_KVK          | 12345678                                                                                                                                                                                           | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | AANGEGEVEN_UREN         | [{"kind_bsn": "111111111", "uren_per_jaar": 2000, "uurtarief": 850, "soort_opvang": "DAGOPVANG"}, {"kind_bsn": "222222222", "uren_per_jaar": 1500, "uurtarief": 900, "soort_opvang": "DAGOPVANG"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | VERWACHTE_PARTNER_UREN | 0                                                                                                                                                                                                  | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er geen verplichte gegevens
    And is de output "is_gerechtigd" waar
    And is het toeslagbedrag "24400.00" euro

  Scenario: Tweeverdieners met hoger inkomen ontvangen lagere toeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 888888888 | 1985-03-10    | Utrecht        | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type   | partner_bsn | kinderen               |
      | 888888888 | HUWELIJK            | 999999999   | [{"bsn": "333333333"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 4500000                   | 0                         | 0                     | 0                               | 0            |
      | 999999999 | 3800000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | verzekerde_jaren |
      | 888888888 | 8             |
      | 999999999 | 6             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date |
      | 888888888 | 2023-01-01 |          |
      | 999999999 | 2023-01-01 |          |
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                           | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | KINDEROPVANG_KVK          | 87654321                                                                                                                                | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | AANGEGEVEN_UREN         | [{"kind_bsn": "333333333", "uren_per_jaar": 2500, "uurtarief": 895, "soort_opvang": "DAGOPVANG", "LRK_registratienummer": "123456789"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | VERWACHTE_PARTNER_UREN | 30                                                                                                                                      | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then is de output "is_gerechtigd" waar
    And is het toeslagbedrag "7383.75" euro

  Scenario: Ouder met BSO en overschrijding van het maximale uurtarief
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 888888888 | 1988-11-21    | Rotterdam      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn | kinderen                                     |
      | 888888888 | GEEN              |             | [{"bsn": "444444444"}, {"bsn": "555555555"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 3200000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | verzekerde_jaren |
      | 888888888 | 4             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date |
      | 888888888 | 2023-03-01 |          |
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                                                                                                                                                      | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | KINDEROPVANG_KVK          | 23456789                                                                                                                                                                                                                                                           | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | AANGEGEVEN_UREN         | [{"kind_bsn": "444444444", "uren_per_jaar": 1200, "uurtarief": 790, "soort_opvang": "BSO", "LRK_registratienummer": "234567890"}, {"kind_bsn": "555555555", "uren_per_jaar": 1200, "uurtarief": 790, "soort_opvang": "BSO", "LRK_registratienummer": "234567890"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | VERWACHTE_PARTNER_UREN | 0                                                                                                                                                                                                                                                                  | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then is de output "is_gerechtigd" waar
    And is het toeslagbedrag "17648.64" euro

  Scenario: Partner werkt minder dan vereiste uren, geen recht op toeslag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 888888888 | 1990-07-05    | Den Haag       | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type   | partner_bsn | kinderen               |
      | 888888888 | HUWELIJK            | 777777777   | [{"bsn": "666666666"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 2900000                   | 0                         | 0                     | 0                               | 0            |
      | 777777777 | 1200000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | verzekerde_jaren |
      | 888888888 | 3             |
      | 777777777 | 2             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 888888888 | 2022-09-01 |            |
      | 777777777 | 2023-01-01 | 2023-01-15 |
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                           | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | KINDEROPVANG_KVK          | 34567890                                                                                                                                | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | AANGEGEVEN_UREN         | [{"kind_bsn": "666666666", "uren_per_jaar": 1800, "uurtarief": 880, "soort_opvang": "DAGOPVANG", "LRK_registratienummer": "345678901"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | VERWACHTE_PARTNER_UREN | 15                                                                                                                                      | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then is de output "is_gerechtigd" onwaar

  Scenario: Gezin met meerdere soorten opvang
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 888888888 | 1987-02-18    | Groningen      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type   | partner_bsn | kinderen                                     |
      | 888888888 | HUWELIJK            | 888888880   | [{"bsn": "888888881"}, {"bsn": "888888882"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 2800000                   | 0                         | 0                     | 0                               | 0            |
      | 888888880 | 2100000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | verzekerde_jaren |
      | 888888888 | 7             |
      | 888888880 | 5             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date |
      | 888888888 | 2020-02-01 |          |
      | 888888880 | 2020-02-01 |          |
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                                                                                                                                                            | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | KINDEROPVANG_KVK          | 56789012                                                                                                                                                                                                                                                                 | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | AANGEGEVEN_UREN         | [{"kind_bsn": "888888881", "uren_per_jaar": 2000, "uurtarief": 899, "soort_opvang": "DAGOPVANG", "LRK_registratienummer": "567890123"}, {"kind_bsn": "888888882", "uren_per_jaar": 1000, "uurtarief": 750, "soort_opvang": "BSO", "LRK_registratienummer": "567890124"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | VERWACHTE_PARTNER_UREN | 30                                                                                                                                                                                                                                                                       | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then is de output "is_gerechtigd" waar
    And is het toeslagbedrag "20384.00" euro
