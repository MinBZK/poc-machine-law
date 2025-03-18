Feature: Berekening Inkomstenbelasting
  Als burger
  Wil ik weten hoeveel inkomstenbelasting ik verschuldigd ben
  Zodat ik mijn financiën kan plannen

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"

  Scenario: Berekening inkomstenbelasting voor alleenstaande met inkomen uit verschillende boxen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 999993653 | 1985-05-15    | Amsterdam      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 4800000                   | 0                         | 1200000               | 500000                          | -120000      |
    And de volgende BELASTINGDIENST box2 gegevens:
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 300000              | 200000                 |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld  | beleggingen | onroerend_goed | schulden |
      | 999993653 | 10000000   | 5000000     | 15000000       | 4000000  |
    And de volgende BELASTINGDIENST aftrekposten gegevens:
      | bsn       | persoonsgebonden_aftrek |
      | 999993653 | 350000                  |
    When de wet_inkomstenbelasting wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And is het box1_income "6380000" eurocent
    And is het box2_income "500000" eurocent
    And is het box3_income "1213626" eurocent
    And is het taxable_income "7743626" eurocent
    And is het total_tax_due "2309416" eurocent

  Scenario: Berekening inkomstenbelasting voor gepensioneerde met AOW
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 999993653 | 1955-05-15    | Amsterdam      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 0                         | 2300000                   | 0                     | 0                               | -50000       |
    And de volgende BELASTINGDIENST box2 gegevens:
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 8000000   | 2000000     | 0              | 0        |
    When de wet_inkomstenbelasting wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And is het box1_income "2250000" eurocent
    And is het box2_income "0" eurocent
    And is het box3_income "253626" eurocent
    And is het total_tax_due "40075" eurocent

  Scenario: Berekening inkomstenbelasting voor werkende ouder met heffingskortingen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf | nationaliteit |
      | 999993653 | 1998-05-15    | Amsterdam      | NEDERLAND     | NEDERLANDS    |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RvIG kinderen gegevens:
      | bsn       | geboortedatum |
      | 111111111 | 2020-01-01    |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 3000000                   | 0                         | 0                     | 0                               | -90000       |
    And de volgende BELASTINGDIENST box2 gegevens:
      | bsn       | reguliere_voordelen | vervreemdingsvoordelen |
      | 999993653 | 0                   | 0                      |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 2000000   | 0           | 0              | 0        |
    When de wet_inkomstenbelasting wordt uitgevoerd door BELASTINGDIENST
    Then is voldaan aan de voorwaarden
    And is het box1_income "2910000" eurocent
    And is het box2_income "0" eurocent
    And is het box3_income "0" eurocent
    And is het total_tax_credits "727646" eurocent
    And is het total_tax_due "347017" eurocent
