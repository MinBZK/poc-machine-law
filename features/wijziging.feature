Feature: Wijzigen gegevens
  Als burger
  Wil ik een gegevens kunnen wijzigen.

  Background:
    Given de datum is "2024-02-01"
    And een persoon met BSN "999993653"
    And alle aanvragen worden beoordeeld

  Scenario: Burger corrigeert geboortedatum via claim voor AOW aanvraag
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1960-02-15    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende SVB verzekerde_tijdvakken gegevens:
      | bsn       | woonperiodes |
      | 999993653 | 50           |
    When de algemene_ouderdomswet wordt uitgevoerd door SVB met wijzigingen
    Then is niet voldaan aan de voorwaarden
    When de burger een wijziging indient:
      | service | law     | key        | nieuwe_waarde | reden                                    | bewijs           |
      | RvIG    | wet_brp | BIRTH_DATE | 1948-02-15    | Geboortedatum onjuist in BRP registratie | geboorteakte.pdf |
    When de algemene_ouderdomswet wordt uitgevoerd door SVB met wijzigingen
    Then is voldaan aan de voorwaarden
