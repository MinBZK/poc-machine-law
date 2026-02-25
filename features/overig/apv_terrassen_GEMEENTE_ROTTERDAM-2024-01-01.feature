Feature: Bepalen recht op Terrasvergunning horeca Rotterdam
  Als horecaondernemer in Rotterdam
  Wil ik weten of ik een terrasvergunning kan krijgen
  Zodat ik een terras mag exploiteren bij mijn horecabedrijf

  # Gebaseerd op de APV Rotterdam 2012, met name:
  # - Artikel 2:30b: Terrasvergunning
  # - Artikel 2:10: Voorwerpen op of aan de weg
  # - Artikel 2:29: Sluitingstijden
  # - Terrassenbeleid Rotterdam 2023
  # - Verordening precariobelasting Rotterdam 2024
  #
  # De terrasvergunning vereist een geldige exploitatievergunning (artikel 2:28).
  # De exploitatievergunning wordt volledig geëvalueerd via service_reference,
  # daarom bevat de Background alle benodigde data voor beide wetten.

  Background:
    Given de datum is "2024-06-01"
    And een organisatie met KVK-nummer "85234567"
    # === Exploitatievergunning dependency chain ===
    # Alle data die nodig is voor een geldige exploitatievergunning,
    # omdat de terrassenvergunning de exploitatievergunning volledig evalueert.
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm | vestigingsadres       |
      | 85234567   | Actief | VOF        | Witte de Withstraat 1 |
    And de volgende GEMEENTE_ROTTERDAM exploitatie_inschrijvingen gegevens:
      | kvk_nummer | bsn_eigenaar |
      | 85234567   | 999999990    |
    And de volgende GEMEENTE_ROTTERDAM personen_vog gegevens:
      | bsn       | heeft_geldige_vog |
      | 999999990 | true              |
    And de volgende GEMEENTE_ROTTERDAM vestigingen gegevens:
      | kvk_nummer | schenkt_alcohol |
      | 85234567   | true            |
    And de volgende GEMEENTE_ROTTERDAM beheerders gegevens:
      | kvk_nummer | schenkt_alcohol | alle_hebben_vog | alle_voldoen_leeftijd | geen_onder_curatele | heeft_svh_diploma |
      | 85234567   | true            | true            | true                  | true                | true              |
    And de volgende GEMEENTE_ROTTERDAM horecagebiedsplannen gegevens:
      | adres                 | categorie_toegestaan |
      | Witte de Withstraat 1 | true                 |
    And de volgende GEMEENTE_ROTTERDAM vergunningen_historie gegevens:
      | bsn       | ingetrokken_slecht_levensgedrag |
      | 999999990 | false                          |
    And de volgende GEMEENTE_ROTTERDAM omgevingsplan_toetsingen gegevens:
      | adres                 | horeca_toegestaan |
      | Witte de Withstraat 1 | true              |
    And de volgende RvIG personen gegevens:
      | bsn       | geboortedatum |
      | 999999990 | 1990-01-01    |
    And de volgende RECHTSPRAAK curatele_registraties gegevens:
      | bsn_curandus | status    | datum_ingang | datum_einde |
      | 999999990    | BEËINDIGD | 2020-01-01   | 2021-01-01  |
    And de volgende KADASTER bag_verblijfsobjecten gegevens:
      | adres                 | gebruiksdoel       |
      | Witte de Withstraat 1 | bijeenkomstfunctie |
    # === Terras-specifieke bronnen ===
    And de volgende GEMEENTE_ROTTERDAM vergunningen gegevens:
      | kvk_nummer | heeft_exploitatievergunning | heeft_alcoholvergunning | categorie   |
      | 85234567   | true                        | true                    | middelzwaar |
    And de volgende GEMEENTE_ROTTERDAM bgt_terraslocaties gegevens:
      | adres                 | locatie | beschikbare_oppervlakte | functie_oppervlak | is_openbare_weg |
      | Witte de Withstraat 1 | voor    | 15                      | voetpad           | true            |
    And de volgende GEMEENTE_ROTTERDAM terrassenbeleid gegevens:
      | adres                 | seizoen  | max_sluitingstijd_doordeweeks | max_sluitingstijd_weekend |
      | Witte de Withstraat 1 | jaarrond | 24                            | 24                        |
    And de volgende GEMEENTE_ROTTERDAM precario_tarieven gegevens:
      | adres                 | gebruik | tarief_per_m2 |
      | Witte de Withstraat 1 | terras  | 25.00         |

  # ====================
  # SUCCESVOLLE AANVRAGEN
  # ====================

  Scenario: Succesvolle aanvraag - standaard terras voor het pand
    # Casus: Horecabedrijf met exploitatievergunning vraagt terras aan. 10 m² gevraagd
    # (15 m² beschikbaar via BGT), voetpad, 2.5m obstakelvrij, sluitingstijden binnen limiet.
    # Verwachting: Terrasvergunning wordt verleend (artikel 2:30b)
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 2.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" waar
    And heeft de output "vergunde_oppervlakte" waarde "10"
    And heeft de output "vergunde_sluitingstijd_doordeweeks" waarde "23"
    And heeft de output "vergunde_sluitingstijd_weekend" waarde "24"
    And is de output "precariobelasting_verschuldigd" waar
    And heeft de output "precariobelasting_per_jaar" waarde "250"

  Scenario: Succesvolle aanvraag - grenswaarde obstakelvrije ruimte (precies 1.8m)
    # Casus: Obstakelvrije ruimte is precies het minimum van 1.8 meter (GREATER_OR_EQUAL).
    # Verwachting: Terrasvergunning wordt verleend (grenswaarde is voldoende)
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 1.8                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" waar

  # ====================
  # AFWIJZINGEN
  # ====================

  Scenario: Afwijzing - geen geldige exploitatievergunning (artikel 2:28)
    # Casus: Het horecabedrijf heeft geen geldige exploitatievergunning.
    # Verwachting: Terrasvergunning wordt GEWEIGERD
    Given de volgende GEMEENTE_ROTTERDAM vergunningen gegevens:
      | kvk_nummer | heeft_exploitatievergunning | heeft_alcoholvergunning | categorie   |
      | 85234567   | false                       | true                    | middelzwaar |
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 2.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" onwaar

  Scenario: Afwijzing - onvoldoende obstakelvrije ruimte (1.5m < 1.8m minimum)
    # Casus: Obstakelvrije ruimte is 1.5 meter, onder het minimum van 1.8 meter.
    # Artikel 2:30b lid 3: minimaal 1.8 meter obstakelvrije ruimte voor voetgangers.
    # Verwachting: Terrasvergunning wordt GEWEIGERD
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 1.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" onwaar

  Scenario: Afwijzing - gevraagde oppervlakte groter dan beschikbare ruimte
    # Casus: 20 m² gevraagd terwijl slechts 15 m² beschikbaar is via BGT.
    # Verwachting: Terrasvergunning wordt GEWEIGERD
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 20                 | 2.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" onwaar

  Scenario: Afwijzing - verkeerde BGT-functie oppervlak (rijbaan i.p.v. voetpad)
    # Casus: Het oppervlak heeft BGT-functie "rijbaan", wat niet in de lijst van
    # toegestane functies staat (voetpad, voetgangersgebied, woonerf, inrit).
    # Verwachting: Terrasvergunning wordt GEWEIGERD
    Given de volgende GEMEENTE_ROTTERDAM bgt_terraslocaties gegevens:
      | adres                 | locatie | beschikbare_oppervlakte | functie_oppervlak | is_openbare_weg |
      | Witte de Withstraat 1 | voor    | 15                      | rijbaan           | true            |
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 2.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" onwaar

  Scenario: Afwijzing - gewenste sluitingstijd weekend later dan toegestaan
    # Casus: Gewenste sluitingstijd weekend is 24 (middernacht) terwijl maximaal 23:00
    # is toegestaan in dit gebied. Artikel 2:29: sluitingstijden terrassen.
    # Verwachting: Terrasvergunning wordt GEWEIGERD
    Given de volgende GEMEENTE_ROTTERDAM terrassenbeleid gegevens:
      | adres                 | seizoen  | max_sluitingstijd_doordeweeks | max_sluitingstijd_weekend |
      | Witte de Withstraat 1 | jaarrond | 24                            | 23                        |
    When de algemene_plaatselijke_verordening/terrassen wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | TERRAS_LOCATIE | TERRAS_OPPERVLAKTE | OBSTAKELVRIJE_RUIMTE | SEIZOEN  | GEWENSTE_OPENINGSTIJD | GEWENSTE_SLUITINGSTIJD_DOORDEWEEKS | GEWENSTE_SLUITINGSTIJD_WEEKEND |
      | voor          | 10                 | 2.5                  | jaarrond | 8                     | 23                                 | 24                             |
    Then is niet voldaan aan de voorwaarden
    And is de output "heeft_recht_op_terrasvergunning" onwaar
