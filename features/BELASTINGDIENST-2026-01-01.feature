Feature: Zorgverzekeringswet - Inkomensafhankelijke bijdrage
  Als belastingplichtige
  Wil ik weten wat mijn inkomensafhankelijke bijdrage Zvw is
  Zodat ik mijn zorgkosten kan plannen

  Background:
    Given de datum is "2026-07-01"

  Scenario: Werknemer met hoog tarief (werkgeversheffing)
    Given een persoon met BSN "200000001"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 200000001 | 1985-05-20    | Amsterdam      |
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 200000001 | 2015-01-01 | null       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 200000001 | 5000000                   | 0                         | 0                     | 0                               | 0            |
    When de zorgverzekeringswet/bijdrage wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And heeft de output "bijdrage_type" waarde "HOOG"
    And heeft de output "bijdrage_inkomen" waarde "5000000"
    # 5000000 * 0.0650 = 325000 eurocent = 3250.00 euro
    And heeft de output "verschuldigde_bijdrage" waarde "325000"

  Scenario: AOW-gerechtigde met laag tarief
    Given een persoon met BSN "200000002"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 200000002 | 1958-03-15    | Rotterdam      |
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 200000002 | null       | null       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 200000002 | 0                         | 3000000                   | 0                     | 0                               | 0            |
    When de zorgverzekeringswet/bijdrage wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And heeft de output "bijdrage_type" waarde "LAAG"
    And heeft de output "is_aow_gerechtigd" waarde "true"
    # 3000000 * 0.0525 = 157500 eurocent = 1575.00 euro
    And heeft de output "verschuldigde_bijdrage" waarde "157500"

  Scenario: Zelfstandige zonder werkgever
    # NOTE: In werkelijkheid zouden zelfstandigen het lage tarief (5,25%) moeten betalen.
    # De huidige law implementatie maakt dit onderscheid nog niet - dit is een TODO.
    # Voor nu wordt het hoge tarief toegepast voor alle niet-AOW-gerechtigden.
    Given een persoon met BSN "200000003"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 200000003 | 1975-08-10    | Utrecht        |
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 200000003 | null       | null       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 200000003 | 0                         | 0                         | 7000000               | 0                               | 0            |
    When de zorgverzekeringswet/bijdrage wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And heeft de output "bijdrage_type" waarde "HOOG"
    # 7000000 * 0.0650 = 455000 eurocent = 4550.00 euro
    And heeft de output "verschuldigde_bijdrage" waarde "455000"

  Scenario: Werknemer met inkomen boven maximum
    Given een persoon met BSN "200000004"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 200000004 | 1980-01-01    | Den Haag       |
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 200000004 | 2010-01-01 | null       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 200000004 | 10000000                  | 0                         | 0                     | 0                               | 0            |
    When de zorgverzekeringswet/bijdrage wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And heeft de output "bijdrage_type" waarde "HOOG"
    # Maximum is 7541200, dus: 7541200 * 0.0650 = 490178 eurocent = 4901.78 euro
    And heeft de output "bijdrage_inkomen_begrensd" waarde "7541200"
    And heeft de output "verschuldigde_bijdrage" waarde "490178"

  Scenario: Persoon zonder inkomen voldoet niet aan voorwaarden
    Given een persoon met BSN "200000005"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 200000005 | 1990-06-15    | Eindhoven      |
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2026 | 20.5           |
    And de volgende UWV dienstverbanden gegevens:
      | bsn       | start_date | end_date   |
      | 200000005 | null       | null       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 200000005 | 0                         | 0                         | 0                     | 0                               | 0            |
    When de zorgverzekeringswet/bijdrage wordt uitgevoerd door BELASTINGDIENST
    Then is niet voldaan aan de voorwaarden
