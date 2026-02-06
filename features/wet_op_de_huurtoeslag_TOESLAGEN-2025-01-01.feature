Feature: Berekening Huurtoeslag
  Als burger
  Wil ik weten of ik recht heb op huurtoeslag
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given de datum is "2025-02-01"

  Scenario: Persoon onder 18 heeft geen recht op huurtoeslag
    Given een persoon met BSN "111111111"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 111111111 | 2008-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 111111111 | GEEN              | null        |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN
    Then is niet voldaan aan de voorwaarden

  Scenario: Alleenstaande met laag inkomen en hogere huur
    Given een persoon met BSN "222222222"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 222222222 | 1990-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 222222222 | GEEN              | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 222222222 | 1400000                   |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er verplichte gegevens
    And is niet voldaan aan de voorwaarden
    When de burger deze gegevens indient:
      | service   | law                   | key                    | nieuwe_waarde | reden               | bewijs |
      | TOESLAGEN | wet_op_de_huurtoeslag | HUURPRIJS            | 72000         | verplichte gegevens |        |
      | TOESLAGEN | wet_op_de_huurtoeslag | SERVICEKOSTEN          | 5000          | verplichte gegevens |        |
      | TOESLAGEN | wet_op_de_huurtoeslag | SUBSIDIABELE_SERVICEKOSTEN | 4800          | verplichte gegevens |        |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then ontbreken er geen verplichte gegevens
    And is voldaan aan de voorwaarden
    And is de huurtoeslag "406.95" euro

  Scenario: Te hoog inkomen voor huurtoeslag
    Given een persoon met BSN "333333333"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres        | land_verblijf |
      | 333333333 | 1980-01-01    | Voorstraat 1, Utrecht | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 333333333 | GEEN              | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking |
      | 333333333 | 4500000                   |
    When de burger deze gegevens indient:
      | service   | law                   | key                    | nieuwe_waarde | reden               | bewijs |
      | TOESLAGEN | wet_op_de_huurtoeslag | HUURPRIJS            | 65000         | verplichte gegevens |        |
      | TOESLAGEN | wet_op_de_huurtoeslag | SERVICEKOSTEN          | 5000          | verplichte gegevens |        |
      | TOESLAGEN | wet_op_de_huurtoeslag | SUBSIDIABELE_SERVICEKOSTEN | 4800          | verplichte gegevens |        |
    When de wet_op_de_huurtoeslag wordt uitgevoerd door TOESLAGEN met wijzigingen
    Then is niet voldaan aan de voorwaarden
