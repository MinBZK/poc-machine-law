@skip-go
Feature: Anw - Nabestaandenuitkering
  Als nabestaande van een verzekerde
  Wil ik weten of ik recht heb op een nabestaandenuitkering
  Zodat ik mijn financiële situatie kan plannen

  Background:
    Given de datum is "2026-07-01"
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |

  Scenario: Nabestaande met kind onder 18 jaar zonder inkomen
    Given een persoon met BSN "300000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000001 | 1985-06-15    | Amsterdam      |
    And de volgende RvIG kinderen gegevens:
      | bsn       | kind_bsn  | geboortedatum |
      | 300000001 | 300000101 | 2015-03-20    |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000001 | true              | 2026-01-15               | 0             | true                    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000001 | 0                         | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is voldaan aan de voorwaarden
    And is de output "is_gerechtigd" waar
    And heeft de output "bruto_uitkering" waarde "146500"
    And heeft de output "inkomenskorting" waarde "0"
    And heeft de output "netto_uitkering" waarde "146500"

  Scenario: Nabestaande met arbeidsongeschiktheid 45% of meer
    Given een persoon met BSN "300000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000002 | 1975-09-20    | Rotterdam      |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000002 | true              | 2026-02-01               | 50            | false                   |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000002 | 0                         | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is voldaan aan de voorwaarden
    And is de output "is_gerechtigd" waar
    And heeft de output "netto_uitkering" waarde "146500"

  Scenario: Nabestaande met inkomen boven vrijlating
    Given een persoon met BSN "300000003"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000003 | 1980-01-10    | Utrecht        |
    And de volgende RvIG kinderen gegevens:
      | bsn       | kind_bsn  | geboortedatum |
      | 300000003 | 300000103 | 2012-07-15    |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000003 | true              | 2026-03-01               | 0             | true                    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000003 | 2400000                   | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is voldaan aan de voorwaarden
    And is de output "is_gerechtigd" waar
    # Maandelijks inkomen: 2400000 / 12 = 200000 eurocent = €2000
    # Korting: 200000 - 77000 = 123000 eurocent
    And heeft de output "inkomenskorting" waarde "123000"
    # Netto: 146500 - 123000 = 23500 eurocent
    And heeft de output "netto_uitkering" waarde "23500"

  Scenario: Nabestaande zonder kinderen en zonder arbeidsongeschiktheid
    Given een persoon met BSN "300000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000004 | 1970-04-25    | Den Haag       |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000004 | true              | 2026-04-01               | 30            | false                   |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000004 | 3000000                   | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is niet voldaan aan de voorwaarden

  Scenario: Nabestaande van niet-verzekerde partner
    Given een persoon met BSN "300000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000005 | 1982-11-30    | Eindhoven      |
    And de volgende RvIG kinderen gegevens:
      | bsn       | kind_bsn  | geboortedatum |
      | 300000005 | 300000105 | 2018-02-10    |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000005 | false             | 2026-05-01               | 0             | true                    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000005 | 0                         | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is niet voldaan aan de voorwaarden

  Scenario: Nabestaande die AOW-leeftijd heeft bereikt
    Given een persoon met BSN "300000006"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 300000006 | 1958-01-15    | Groningen      |
    And de volgende RvIG kinderen gegevens:
      | bsn       | kind_bsn  | geboortedatum |
      | 300000006 | 300000106 | 2015-06-20    |
    And de volgende SVB anw_dossiers gegevens:
      | bsn       | partner_verzekerd | overlijdensdatum_partner | ao_percentage | heeft_kinderen_onder_18 |
      | 300000006 | true              | 2026-06-01               | 0             | true                    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 300000006 | 0                         | 0                         | 0                     | 0                               | 0            |
    When de algemene_nabestaandenwet wordt uitgevoerd door SVB
    Then is niet voldaan aan de voorwaarden
