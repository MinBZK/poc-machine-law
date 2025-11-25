Feature: Berichten aan burgers (AWB Art. 3:40-3:45)
  Als overheidsinstantie
  Wil ik burgers informeren over beschikkingen
  Zodat zij weten wat er besloten is en welke rechtsmiddelen er zijn

  Wettelijke grondslag:
  - AWB Art. 3:40: Een besluit treedt niet in werking voordat het is bekendgemaakt
  - AWB Art. 3:41: Bekendmaking geschiedt door toezending of uitreiking aan belanghebbende
  - AWB Art. 3:45: Vermelding van rechtsmiddelenclausule bij beschikkingen
  - AWIR Art. 13: Elektronisch berichtenverkeer
  - AWIR Art. 16: Voorschotbeschikking
  - AWIR Art. 19: Definitieve toekenning

  Background:
    Given de datum is "2025-01-15"

  # === Berichten bij voorschotbeschikking ===

  Scenario: Bericht wordt aangemaakt bij voorschotbeschikking toekenning (AWIR Art. 16)
    Given een persoon met BSN "100000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000001 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000001 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000001 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000001 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    Then is de toeslag status "VOORSCHOT"
    And is er een bericht aangemaakt voor BSN "100000001"
    And is het bericht type "VOORSCHOT_BESCHIKKING"
    And bevat het bericht onderwerp "Voorschotbeschikking"
    And bevat het bericht de rechtsmiddelenclausule

  Scenario: Bericht wordt aangemaakt bij afwijzing - persoon niet verzekerd (AWIR Art. 16 lid 4)
    Given een persoon met BSN "100000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000002 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000002 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000002 | BEEINDIGD    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000002 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    Then is de toeslag status "AFGEWEZEN"
    And is er een bericht aangemaakt voor BSN "100000002"
    And is het bericht type "AFWIJZING"
    And bevat het bericht onderwerp "Beslissing"
    And bevat het bericht de rechtsmiddelenclausule

  # === Bericht status workflow ===

  Scenario: Nieuw bericht heeft status SENT (AWB Art. 3:41)
    Given een persoon met BSN "100000003"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000003 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000003 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000003 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000003 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    And is er een bericht aangemaakt voor BSN "100000003"
    Then is het bericht status "SENT"
    And is het bericht ongelezen

  Scenario: Bericht markeren als gelezen
    Given een persoon met BSN "100000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000004 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000004 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000004 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000004 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    And is er een bericht aangemaakt voor BSN "100000004"
    And de burger het bericht leest
    Then is het bericht status "READ"
    And is het bericht gelezen

  Scenario: Bericht archiveren
    Given een persoon met BSN "100000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000005 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000005 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000005 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000005 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    And is er een bericht aangemaakt voor BSN "100000005"
    And de burger het bericht archiveert
    Then is het bericht status "ARCHIVED"

  # === Meerdere berichten en ongelezen telling ===

  Scenario: Ongelezen berichten tellen voor notificatie badge
    Given een persoon met BSN "100000006"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000006 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000006 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000006 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000006 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    And is er een bericht aangemaakt voor BSN "100000006"
    Then is het aantal ongelezen berichten 1 voor BSN "100000006"
    When de burger het bericht leest
    Then is het aantal ongelezen berichten 0 voor BSN "100000006"

  # === Berichten per zaak ===

  Scenario: Berichten zijn gekoppeld aan een zaak
    Given een persoon met BSN "100000007"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 100000007 | 1990-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 100000007 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000007 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 100000007 | 35000                     | 0                         | 0                     | 0                               | 0           |
    When de burger zorgtoeslag aanvraagt voor jaar 2025
    And de aanspraak wordt berekend
    And de voorschotbeschikking wordt vastgesteld
    Then is er een bericht gekoppeld aan de zaak
    And zijn er 1 berichten voor de zaak
