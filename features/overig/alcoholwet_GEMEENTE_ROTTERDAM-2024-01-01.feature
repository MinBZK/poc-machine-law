@skip-go
Feature: Bepalen recht op Alcoholwetvergunning horeca Rotterdam
  Als horecaondernemer in Rotterdam
  Wil ik weten of ik een Alcoholwetvergunning kan krijgen
  Zodat ik alcoholhoudende dranken mag verstrekken voor gebruik ter plaatse

  # Gebaseerd op de Alcoholwet (BWBR0002458), met name:
  # - Artikel 3: Vergunningplicht
  # - Artikel 8: Eisen aan leidinggevenden (21 jaar, niet van slecht levensgedrag, niet onder curatele, SVH)
  # - Artikel 10: Inrichtingseisen (min. 35 m2 vloeroppervlakte)
  # - Artikel 27: Weigeringsgronden

  Background:
    Given de datum is "2024-06-01"

  # ====================
  # SUCCESVOLLE AANVRAGEN
  # ====================

  Scenario: Succesvolle aanvraag - alle eisen artikel 8 en 10 voldaan
    # Casus: Exploitant van 25 jaar met alle vereiste documenten en een
    # horecalokaliteit van 50 m2 vraagt een Alcoholwetvergunning aan.
    # Verwachting: Vergunning wordt verleend (artikel 27 lid 1 - geen weigeringsgrond)
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1999-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm |
      | 85234567   | Actief | VOF        |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 25       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 50                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    And de volgende SVH registraties gegevens:
      | bsn       | is_geregistreerd |
      | 999999990 | true             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" waar

  Scenario: Succesvolle aanvraag - precies 21 jaar (grenswaarde artikel 8 lid 1 onder a)
    # Casus: Exploitant is precies 21 jaar oud op datum van aanvraag.
    # Artikel 8 lid 1 onder a: "de leeftijd van eenentwintig jaar hebben bereikt"
    # Verwachting: Vergunning wordt verleend
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 2003-06-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 21       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 40                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    And de volgende SVH registraties gegevens:
      | bsn       | is_geregistreerd |
      | 999999990 | true             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" waar

  Scenario: Succesvolle aanvraag - precies 35 m2 vloeroppervlakte (grenswaarde artikel 10 lid 2)
    # Casus: Horecalokaliteit heeft precies de minimaal vereiste 35 m2.
    # Artikel 10 lid 2: "ten minste 35 m2"
    # Verwachting: Vergunning wordt verleend
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1990-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 34       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 35                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    And de volgende SVH registraties gegevens:
      | bsn       | is_geregistreerd |
      | 999999990 | true             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" waar

  # ====================
  # AFWIJZINGEN - LEEFTIJD (ARTIKEL 8 LID 1 ONDER A)
  # ====================

  Scenario: Afwijzing - exploitant is 20 jaar (niet voldaan aan artikel 8 lid 1 onder a)
    # Casus: Een 20-jarige ondernemer vraagt een Alcoholwetvergunning aan.
    # Artikel 8 lid 1 onder a: leidinggevenden moeten "de leeftijd van eenentwintig jaar hebben bereikt"
    # Verwachting: Vergunning wordt GEWEIGERD op grond van artikel 27 lid 1 onder a
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 2004-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 20       | false                      | false             | true                         | 0                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 50                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  Scenario: Afwijzing - exploitant is 18 jaar (significant onder minimumleeftijd)
    # Casus: Een 18-jarige ondernemer denkt dat de leeftijdsgrens gelijk is aan
    # die voor alcoholconsumptie (18 jaar), maar de Alcoholwet stelt 21 jaar als eis.
    # Verwachting: Vergunning wordt GEWEIGERD
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 2006-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 18       | false                      | false             | true                         | 0                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 50                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  # ====================
  # AFWIJZINGEN - CURATELE (ARTIKEL 8 LID 1 ONDER C)
  # ====================

  Scenario: Afwijzing - exploitant staat onder curatele (artikel 8 lid 1 onder c)
    # Casus: Een ondernemer die onder curatele is gesteld vraagt een vergunning aan.
    # Artikel 8 lid 1 onder c: leidinggevenden mogen "niet onder curatele" staan
    # Verwachting: Vergunning wordt GEWEIGERD
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1985-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 39       | false                      | true              | true                         | 0                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 50                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | true              |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  # ====================
  # AFWIJZINGEN - INRICHTINGSEISEN (ARTIKEL 10)
  # ====================

  Scenario: Afwijzing - vloeroppervlakte horecalokaliteit kleiner dan 35 m2 (artikel 10 lid 2)
    # Casus: Een ondernemer wil een kleine kroeg openen met 30 m2 vloeroppervlakte.
    # Artikel 10 lid 2: "ten minste 35 m2"
    # Verwachting: Vergunning wordt GEWEIGERD op grond van artikel 27 lid 1 onder a
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1990-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 34       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 30                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  Scenario: Afwijzing - vloeroppervlakte net onder minimum (34 m2)
    # Casus: Horecalokaliteit is 34 m2, net 1 m2 onder het minimum.
    # Dit test de grenswaarde.
    # Verwachting: Vergunning wordt GEWEIGERD
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1990-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm  |
      | 85234567   | Actief | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 34       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 34                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  # ====================
  # AFWIJZINGEN - BIBOB
  # ====================

  Scenario: Afwijzing - ernstig gevaar volgens Bibob-advies
    # Casus: Het Landelijk Bureau Bibob heeft geadviseerd dat er ernstig gevaar
    # bestaat dat de vergunning zal worden gebruikt voor witwassen of andere
    # criminele activiteiten.
    # Wet Bibob artikel 3: bij ernstig gevaar MOET de vergunning worden geweigerd
    # Verwachting: Vergunning wordt GEWEIGERD
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1980-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm |
      | 85234567   | Actief | BV         |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 44       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 100                               | horecabedrijf  |
    And de volgende GEMEENTE_ROTTERDAM bibob_adviezen gegevens:
      | kvk_nummer | mate_van_gevaar |
      | 85234567   | ernstig_gevaar  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar

  # ====================
  # AFWIJZINGEN - ONDERNEMING NIET ACTIEF
  # ====================

  Scenario: Afwijzing - onderneming is uitgeschreven uit handelsregister
    # Casus: De onderneming bestaat niet meer of is uitgeschreven.
    # Verwachting: Vergunning wordt GEWEIGERD
    Given een organisatie met KVK-nummer "85234567"
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1990-01-01    |
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status        | rechtsvorm  |
      | 85234567   | Uitgeschreven | Eenmanszaak |
    And de volgende GEMEENTE_ROTTERDAM inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM leidinggevenden gegevens:
      | kvk_nummer | bsn       | leeftijd | is_van_slecht_levensgedrag | is_onder_curatele | is_ingeschreven_svh_register | aantal_voldoet_alle_eisen |
      | 85234567   | 999999990 | 34       | false                      | false             | true                         | 1                         |
    And de volgende GEMEENTE_ROTTERDAM inrichtingen gegevens:
      | kvk_nummer | vloeroppervlakte_horecalokaliteit | type_bedrijf   |
      | 85234567   | 50                                | horecabedrijf  |
    And de volgende RECHTSPRAAK curatele gegevens:
      | bsn       | is_onder_curatele |
      | 999999990 | false             |
    When de alcoholwet/vergunning wordt uitgevoerd door GEMEENTE_ROTTERDAM
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_vergunning" onwaar
