Feature: Berekening Werkgeversbijdrage Zorgverzekeringswet 2024
  Als werkgever
  Wil ik weten hoeveel werkgeversbijdrage Zvw ik moet afdragen
  Zodat ik de juiste premies kan afdragen aan de Belastingdienst

  Background:
    Given de datum is "2024-06-01"

  # Casussen gebaseerd op Zorgverzekeringswet artikel 42 en 43
  # Percentage werkgeversbijdrage 2024: 6,57%
  # Maximum bijdrage-inkomen 2024: EUR 71.628 (7.162.800 eurocent)

  Scenario: Werknemer met modaal inkomen - volledige berekening
    # Werknemer verdient EUR 40.000 bruto per jaar
    # Bijdrage-inkomen: EUR 40.000 (onder maximum)
    # Werkgeversbijdrage: 40.000 x 6,57% = EUR 2.628
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "40000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "4000000" eurocent
    And is de werkgeversbijdrage "262800" eurocent

  Scenario: Werknemer met laag inkomen (minimumloon)
    # Werknemer verdient EUR 24.000 bruto per jaar (rond minimumloon)
    # Bijdrage-inkomen: EUR 24.000 (onder maximum)
    # Werkgeversbijdrage: 24.000 x 6,57% = EUR 1.576,80
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "24000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "2400000" eurocent
    And is de werkgeversbijdrage "157680" eurocent

  Scenario: Werknemer met hoog inkomen - aftopping op maximum bijdrage-inkomen
    # Werknemer verdient EUR 100.000 bruto per jaar
    # Bijdrage-inkomen: afgetopt op EUR 71.628 (maximum 2024)
    # Werkgeversbijdrage: 71.628 x 6,57% = EUR 4.705,96
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "100000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "7162800" eurocent
    And is de werkgeversbijdrage "470565" eurocent

  Scenario: Werknemer met inkomen precies op maximum
    # Werknemer verdient EUR 71.628 bruto per jaar (precies het maximum)
    # Bijdrage-inkomen: EUR 71.628 (gelijk aan maximum)
    # Werkgeversbijdrage: 71.628 x 6,57% = EUR 4.705,96
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "71628" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "7162800" eurocent
    And is de werkgeversbijdrage "470565" eurocent

  Scenario: Werknemer met inkomen net onder maximum
    # Werknemer verdient EUR 71.627 bruto per jaar (1 euro onder maximum)
    # Bijdrage-inkomen: EUR 71.627 (onder maximum, dus volledig)
    # Werkgeversbijdrage: 71.627 x 6,57% = EUR 4.705,89
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "71627" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "7162700" eurocent
    And is de werkgeversbijdrage "470489" eurocent

  Scenario: Werknemer met zeer hoog inkomen - maximale werkgeversbijdrage
    # Werknemer verdient EUR 200.000 bruto per jaar
    # Bijdrage-inkomen: afgetopt op EUR 71.628 (maximum 2024)
    # Werkgeversbijdrage: maximaal EUR 4.705,96
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "200000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "7162800" eurocent
    And is de werkgeversbijdrage "470565" eurocent

  Scenario: Werknemer met nul inkomen
    # Werknemer heeft EUR 0 bruto loon (bijv. onbetaald verlof)
    # Bijdrage-inkomen: EUR 0
    # Werkgeversbijdrage: EUR 0
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "0" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "0" eurocent
    And is de werkgeversbijdrage "0" eurocent

  Scenario: Werknemer parttime - proportioneel inkomen
    # Parttime werknemer verdient EUR 20.000 bruto per jaar
    # Bijdrage-inkomen: EUR 20.000 (onder maximum)
    # Werkgeversbijdrage: 20.000 x 6,57% = EUR 1.314
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "20000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "2000000" eurocent
    And is de werkgeversbijdrage "131400" eurocent

  Scenario: Directeur-grootaandeelhouder (DGA) met gebruikelijk loon
    # DGA met gebruikelijk loon van EUR 56.000 (2024)
    # Bijdrage-inkomen: EUR 56.000 (onder maximum)
    # Werkgeversbijdrage: 56.000 x 6,57% = EUR 3.679,20
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "56000" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "5600000" eurocent
    And is de werkgeversbijdrage "367920" eurocent

  Scenario: Berekening met decimalen in bruto loon
    # Werknemer verdient EUR 45.123,45 bruto per jaar
    # Bijdrage-inkomen: EUR 45.123,45 (onder maximum)
    # Werkgeversbijdrage: 45.123,45 x 6,57% = EUR 2.964,61
    Given een werkgever met loonheffingennummer "123456789L01"
    And een werknemer met bruto jaarloon "45123.45" euro
    When de zvw wordt uitgevoerd door BELASTINGDIENST
    Then is het bijdrage-inkomen "4512345" eurocent
    And is de werkgeversbijdrage "296461" eurocent
