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
      | bsn       | partnerschap_type | partner_bsn | children                                     |
      | 888888888 | GEEN              |             | [{"bsn": "111111111"}, {"bsn": "222222222"}] |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 888888888 | 3600000                   | 0                         | 0                     | 0                               | 0            |
    And de volgende UWV wet_structuur_uitvoeringsorganisatie_werk_en_inkomen gegevens:
      | BSN       | insured_years |
      | 888888888 | 5             |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 888888888 | 2024-01-15 | 2024-01-30|
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er verplichte gegevens
    And is niet voldaan aan de voorwaarden
    When de burger deze gegevens indient:
      | service   | law              | key                    | nieuwe_waarde                                                                                                                                                                                      | reden               | bewijs |
      | TOESLAGEN | wet_kinderopvang | CHILDCARE_KVK          | 12345678                                                                                                                                                                                           | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | DECLARED_HOURS         | [{"kind_bsn": "111111111", "uren_per_jaar": 2000, "uurtarief": 850, "soort_opvang": "DAGOPVANG"}, {"kind_bsn": "222222222", "uren_per_jaar": 1500, "uurtarief": 900, "soort_opvang": "DAGOPVANG"}] | verplichte gegevens |        |
      | TOESLAGEN | wet_kinderopvang | EXPECTED_PARTNER_HOURS | 0                                                                                                                                                                                                  | verplichte gegevens |        |
    When de wet_kinderopvang wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er geen verplichte gegevens
    And heeft de persoon recht op kinderopvangtoeslag
    And is het toeslagbedrag "24400.00" euro
