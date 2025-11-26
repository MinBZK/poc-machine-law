Feature: Time Simulation Year Transition
  Als Toeslagen systeem
  Wil ik dat de tijdsimulatie correct omgaat met jaarovergang
  Zodat toeslagen die laat in het jaar worden aangevraagd correct worden verwerkt

  @year-transition
  Scenario: December aanvraag verwerkt alleen december, niet maand 1-11
    Given de datum is "2025-12-15"
    Given een persoon met BSN "100000001"
    And de volgende TOESLAGEN zorgtoeslag_data gegevens:
      | bsn       | heeft_partner | verzekerde_jaar |
      | 100000001 | false         | 2025            |
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | heeft_toeslagen_partner |
      | 100000001 | 1990-01-01    | NL            | false                   |
    And de volgende BELASTINGDIENST inkomens gegevens:
      | bsn       | jaar | toetsinkomen |
      | 100000001 | 2025 | 2500000      |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000001 | ACTIEF       |
    And de burger heeft zorgtoeslag aangevraagd voor jaar 2025
    And de aanspraak is berekend met recht op toeslag
    When de voorschotbeschikking wordt vastgesteld
    And de datum wordt gezet op "2026-01-15"

    # Controleer dat alleen december is verwerkt (niet maanden 1-11)
    Then bevat de maandelijkse berekeningen 1 berekeningen
    And bevat de maandelijkse betalingen 1 betalingen
    And bevat de maandelijkse berekeningen een berekening voor maand 12
    And bevat de maandelijkse betalingen een betaling voor maand 12

  @year-transition
  Scenario: December aanvraag doet jaar-einde verwerking bij jaarovergang
    Given de datum is "2025-12-15"
    Given een persoon met BSN "100000002"
    And de volgende TOESLAGEN zorgtoeslag_data gegevens:
      | bsn       | heeft_partner | verzekerde_jaar |
      | 100000002 | false         | 2025            |
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | heeft_toeslagen_partner |
      | 100000002 | 1990-01-01    | NL            | false                   |
    And de volgende BELASTINGDIENST inkomens gegevens:
      | bsn       | jaar | toetsinkomen |
      | 100000002 | 2025 | 2500000      |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000002 | ACTIEF       |
    And de burger heeft zorgtoeslag aangevraagd voor jaar 2025
    And de aanspraak is berekend met recht op toeslag
    When de voorschotbeschikking wordt vastgesteld
    And de datum wordt gezet op "2026-01-15"

    # De oude case moet afgerond zijn
    Then is de toeslag status "VEREFFEND"
    And is er een nieuwe toeslag case aangemaakt voor jaar 2026
    And is de nieuwe toeslag status "LOPEND"

  @year-transition @performance
  Scenario: Year transition only evaluates expected number of times
    Given de datum is "2025-12-15"
    Given een persoon met BSN "100000003"
    And de volgende TOESLAGEN zorgtoeslag_data gegevens:
      | bsn       | heeft_partner | verzekerde_jaar |
      | 100000003 | false         | 2025            |
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | heeft_toeslagen_partner |
      | 100000003 | 1990-01-01    | NL            | false                   |
    And de volgende BELASTINGDIENST inkomens gegevens:
      | bsn       | jaar | toetsinkomen |
      | 100000003 | 2025 | 2500000      |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000003 | ACTIEF       |
    And de burger heeft zorgtoeslag aangevraagd voor jaar 2025
    And de aanspraak is berekend met recht op toeslag
    When de voorschotbeschikking wordt vastgesteld
    And de datum wordt gezet op "2026-01-15"

    # For a December case crossing into January:
    # - December 2025: 1 evaluation (process_month)
    # - Year-end: 0 evaluations (no definitief_inkomen, uses sum)
    # - start_new_year: 1 evaluation (bereken_aanspraak)
    # - January 2026: 1 evaluation (process_month)
    # Total: 3 evaluations maximum
    Then bevat de maandelijkse berekeningen 1 berekeningen
    And is de vereffening correct berekend

  @year-transition
  Scenario: January aanvraag verwerkt alle maanden in volgend jaar normaal
    Given de datum is "2025-01-15"
    Given een persoon met BSN "100000004"
    And de volgende TOESLAGEN zorgtoeslag_data gegevens:
      | bsn       | heeft_partner | verzekerde_jaar |
      | 100000004 | false         | 2025            |
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | nationaliteit | heeft_toeslagen_partner |
      | 100000004 | 1990-01-01    | NL            | false                   |
    And de volgende BELASTINGDIENST inkomens gegevens:
      | bsn       | jaar | toetsinkomen |
      | 100000004 | 2025 | 2500000      |
    And de volgende RVZ verzekeringen gegevens:
      | bsn       | polis_status |
      | 100000004 | ACTIEF       |
    And de burger heeft zorgtoeslag aangevraagd voor jaar 2025
    And de aanspraak is berekend met recht op toeslag
    When de voorschotbeschikking wordt vastgesteld
    And de datum wordt gezet op "2025-06-15"

    # Controleer dat maanden 1-6 zijn verwerkt
    Then bevat de maandelijkse berekeningen 6 berekeningen
    And bevat de maandelijkse betalingen 6 betalingen
    And zijn alle maanden tot en met juni verwerkt
