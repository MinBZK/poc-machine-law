@skip-go
@ui
Feature: Bibob-advies Landelijk Bureau Bibob
  Als bestuursorgaan
  Wil ik een Bibob-advies opvragen bij het LBB
  Zodat ik een integriteitsbeoordeling kan meewegen bij mijn besluit over een vergunning

  Background:
    Given de datum is "2024-06-01"

  # Casussen gebaseerd op Wet Bibob artikelen 3 en 9
  # Bron: Justis Leidraad voor de gevaarsbeoordeling

  Scenario: Geen Bibob-advies aangevraagd - verlening niet belemmerd
    # Als er geen advies is aangevraagd, vormt de Wet Bibob geen belemmering
    Given een onderneming met KVK nummer "12345678"
    And er is geen Bibob-advies uitgebracht voor deze onderneming
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er geen advies uitgebracht
    And wordt verlening geadviseerd
    And is weigering niet mogelijk
    And zijn voorschriften niet mogelijk

  Scenario: Bibob-advies uitgebracht - geen gevaar gebleken
    # Het LBB constateert geen gevaar; de Wet Bibob vormt geen belemmering
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | geen_gevaar     | 2024-05-15   | false                    | false               | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "geen_gevaar"
    And wordt verlening geadviseerd
    And is weigering niet mogelijk
    And zijn voorschriften niet mogelijk

  Scenario: Bibob-advies uitgebracht - mindere mate van gevaar
    # Het LBB constateert een mindere mate van gevaar; voorschriften zijn mogelijk
    # Artikel 3 lid 7: bij mindere mate kunnen voorschriften worden verbonden
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | mindere_mate    | 2024-05-15   | true                     | false               | true                      |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "mindere_mate"
    And wordt verlening niet geadviseerd
    And is weigering niet mogelijk
    And zijn voorschriften mogelijk

  Scenario: Bibob-advies uitgebracht - ernstig gevaar (weigering mogelijk)
    # Het LBB constateert ernstig gevaar; weigering of intrekking is mogelijk
    # Artikel 3 lid 1: bij ernstig gevaar kan worden geweigerd of ingetrokken
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | ernstig_gevaar  | 2024-05-15   | true                     | true                | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "ernstig_gevaar"
    And wordt verlening niet geadviseerd
    And is weigering mogelijk
    And zijn voorschriften niet mogelijk

  Scenario: Bibob-advies uitgebracht - ernstig gevaar maar weigering niet proportioneel
    # Het LBB constateert ernstig gevaar, maar weigering is niet proportioneel
    # Sinds wijziging 1 augustus 2020: bij ernstig gevaar kunnen ook voorschriften worden gesteld
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | ernstig_gevaar  | 2024-05-15   | true                     | false               | true                      |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "ernstig_gevaar"
    And is weigering mogelijk
    And zijn voorschriften mogelijk

  Scenario: Bibob-advies voor natuurlijk persoon (exploitant)
    # Bibob-onderzoek naar de exploitant als natuurlijk persoon
    Given een persoon met BSN "999999990"
    And de volgende LBB bibob_adviezen gegevens:
      | bsn       | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 999999990 | true               | geen_gevaar     | 2024-05-15   | false                    | false               | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "geen_gevaar"
    And wordt verlening geadviseerd

  Scenario: Bibob-advies met financieringsrisico (witwassen)
    # Artikel 3 lid 1 sub a: ernstig gevaar dat beschikking wordt misbruikt
    # voor witwassen of financiering uit criminele herkomst
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | ernstig_gevaar  | 2024-05-15   | false                    | true                | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "ernstig_gevaar"
    And is weigering mogelijk
    And is er sprake van financieringsrisico

  Scenario: Bibob-advies met relatie tot strafbare feiten
    # Artikel 3 lid 1 sub b: ernstig gevaar als betrokkene in relatie staat
    # tot strafbare feiten gepleegd bij activiteiten die overeenkomen met
    # activiteiten waarvoor de beschikking wordt gevraagd
    Given een onderneming met KVK nummer "12345678"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 12345678   | true               | ernstig_gevaar  | 2024-05-15   | true                     | false               | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "ernstig_gevaar"
    And is weigering mogelijk
    And is er een relatie tot strafbare feiten

  Scenario: Bibob-advies voor horecavergunning
    # Bibob-toets specifiek voor horecavergunning (exploitatievergunning)
    Given een onderneming met KVK nummer "85234567"
    And de aanvraag betreft een "vergunning"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 85234567   | true               | geen_gevaar     | 2024-05-20   | false                    | false               | false                     |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "geen_gevaar"
    And wordt verlening geadviseerd

  Scenario: Bibob-advies voor vastgoedtransactie
    # Bibob-toets voor vastgoedtransactie (verkoop gemeentelijk vastgoed)
    Given een onderneming met KVK nummer "98765432"
    And de aanvraag betreft een "vastgoedtransactie"
    And de volgende LBB bibob_adviezen gegevens:
      | kvk_nummer | advies_uitgebracht | mate_van_gevaar | advies_datum | relatie_strafbare_feiten | financieringsrisico | voorschriften_geadviseerd |
      | 98765432   | true               | mindere_mate    | 2024-04-10   | false                    | true                | true                      |
    When de wet_bibob wordt uitgevoerd door LBB
    Then is er een advies uitgebracht
    And is de mate van gevaar "mindere_mate"
    And zijn voorschriften mogelijk
