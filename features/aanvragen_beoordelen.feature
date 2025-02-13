Feature: Aanvraag Zorgtoeslag
  Als burger
  Wil ik een aanvraag voor zorgtoeslag kunnen indienen
  En in bezwaar kunnen gaan als ik het niet eens ben met de beslissing
  Zodat ik de juiste toeslag kan ontvangen

  Background:
    Given de datum is "2024-02-01"
    And een persoon met BSN "999993653"
    And alle aanvragen worden beoordeeld

  Scenario: Aanvraag valt in handmatige beoordeling en wordt afgewezen
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1998-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 79547                     | 0                         | 0                     | 0                               | 0            |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    And de persoon dit aanvraagt
    Then wordt de aanvraag toegevoegd aan handmatige beoordeling
    When de beoordelaar de aanvraag afwijst met reden "Inkomen niet correct opgegeven"
    Then is de status "DECIDED"
    And is de aanvraag afgewezen

  Scenario: Burger gaat in bezwaar en krijgt gelijk
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1998-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 20000                     | 0                         | 0                     | 0                               | 0            |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    And de persoon dit aanvraagt
    Then wordt de aanvraag toegevoegd aan handmatige beoordeling
    When de beoordelaar de aanvraag afwijst met reden "Inkomen niet correct opgegeven"
    Then kan de burger in bezwaar gaan
    When de burger bezwaar maakt met reden "Inkomen is wel correct, zie bijgevoegde jaaropgave"
    Then is de status "OBJECTED"
    When de beoordelaar het bezwaar toewijst met reden "Inkomen correct na controle jaaropgave"
    Then is de status "DECIDED"
    And is de aanvraag toegekend
    And is het toeslagbedrag "1811.28" euro


  Scenario: Burger gaat in bezwaar en krijgt geen gelijk
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | land_verblijf |
      | 999993653 | 1998-01-01    | Amsterdam      | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 999993653 | ACTIEF       |
    And de volgende BELASTINGDIENST box1 gegevens:
      | bsn       | loon_uit_dienstbetrekking | uitkeringen_en_pensioenen | winst_uit_onderneming | resultaat_overige_werkzaamheden | eigen_woning |
      | 999993653 | 20000                     | 0                         | 0                     | 0                               | 0            |
    When de zorgtoeslagwet wordt uitgevoerd door TOESLAGEN
    And de persoon dit aanvraagt
    Then wordt de aanvraag toegevoegd aan handmatige beoordeling
    When de beoordelaar de aanvraag afwijst met reden "Inkomen niet correct opgegeven"
    Then kan de burger in bezwaar gaan
    When de burger bezwaar maakt met reden "Inkomen is wel correct, zie bijgevoegde jaaropgave"
    And de beoordelaar het bezwaar afwijst met reden "Inkomen nog steeds niet correct na controle jaaropgave"
    Then is de aanvraag afgewezen
    And kan de burger niet in bezwaar gaan met reden "er is al eerder bezwaar gemaakt tegen dit besluit"
