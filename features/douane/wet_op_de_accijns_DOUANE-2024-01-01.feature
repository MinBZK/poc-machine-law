@skip-go
Feature: Bepalen accijnsplicht en tarief alcoholhoudende dranken
  Als ondernemer die handelt in alcoholhoudende dranken
  Wil ik weten of accijns verschuldigd is, welk tarief van toepassing is en of ik een AGP-vergunning nodig heb
  Zodat ik kan voldoen aan mijn fiscale verplichtingen op grond van de Wet op de accijns

  # Gebaseerd op de Wet op de accijns (BWBR0005251), met name:
  # - Artikel 1: Accijns wordt geheven van bier, wijn, tussenproducten, overige alcoholhoudende producten
  # - Artikel 2: Uitslag tot verbruik als belastbaar feit
  # - Artikel 5: Verbod productie/opslag buiten accijnsgoederenplaats
  # - Artikel 7: Biertarief (8,12 euro/hl/%vol, minimum 26,13 euro/hl; kleine brouwerij: 7,51 euro/hl/%vol)
  # - Artikel 10: Wijntarief (47,95 euro/hl t/m 8,5%vol; 95,69 euro/hl boven 8,5%vol)
  # - Artikel 11d: Tussenproducten (114,85 euro/hl t/m 15%vol; 161,80 euro/hl boven 15%vol)
  # - Artikel 13: Overige alcohol (18,27 euro/hl/%vol)
  # - Artikel 40: Vergunning accijnsgoederenplaats vereist voor productie en opslag

  Background:
    Given de datum is "2024-06-01"

  # ====================
  # BIER - NORMAAL TARIEF (ARTIKEL 7 LID 1)
  # ====================

  Scenario: Horecabedrijf importeert Belgisch speciaalbier (6% vol) - normaal biertarief
    # Casus: Claudia's horecabedrijf importeert 5 hectoliter Belgisch tripelbier
    # met 6% alcohol. Als handelaar is geen AGP-vergunning nodig.
    # Artikel 7 lid 1: 8,12 x 6 = 48,72 euro/hl (boven minimum van 26,13)
    # Verschuldigde accijns: 48,72 x 5 = 243,60 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 6                 | 5                      | false               | handel     |
    Then is voldaan aan de voorwaarden
    And is de output "is_accijnsgoed" waar
    And heeft de output "accijnscategorie" waarde "bier"
    And heeft de output "tarief_per_hectoliter" waarde "48.72"
    And heeft de output "verschuldigde_accijns" waarde "243.6"
    And is de output "agp_vergunning_vereist" onwaar
    And is de output "voldoet_aan_vergunningsplicht" waar

  Scenario: Zwaar Belgisch bier (12% vol) - biertarief boven minimum
    # Casus: Import van 5 hectoliter quadrupel met 12% alcohol.
    # Artikel 7 lid 1: 8,12 x 12 = 97,44 euro/hl (ruim boven minimum van 26,13)
    # Verschuldigde accijns: 97,44 x 5 = 487,20 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 12                | 5                      | false               | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "97.44"
    And heeft de output "verschuldigde_accijns" waarde "487.2"

  Scenario: Licht bier (2% vol) - biertarief valt terug op minimum (artikel 7 lid 1)
    # Casus: Import van 20 hectoliter licht bier met 2% alcohol.
    # Artikel 7 lid 1: 8,12 x 2 = 16,24 euro/hl, maar MINIMUM is 26,13 euro/hl
    # Het minimum geldt dus. Verschuldigde accijns: 26,13 x 20 = 522,60 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 2                 | 20                     | false               | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "26.13"
    And heeft de output "verschuldigde_accijns" waarde "522.6"

  # ====================
  # BIER - VERLAAGD TARIEF KLEINE BROUWERIJ (ARTIKEL 7 LID 2)
  # ====================

  Scenario: Kleine brouwerij produceert bier (6% vol) - verlaagd tarief
    # Casus: Een ambachtelijke brouwerij met jaarproductie onder 200.000 hl
    # produceert 50 hectoliter bier met 6% alcohol. AGP-vergunning vereist voor productie.
    # Artikel 7 lid 2: 7,51 x 6 = 45,06 euro/hl (boven minimum van 26,13)
    # Verschuldigde accijns: 45,06 x 50 = 2253,00 euro
    Given een organisatie met KVK-nummer "12345678"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 12345678   | 1105     |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 12345678   | true                 |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 6                 | 50                     | true                | productie  |
    Then is voldaan aan de voorwaarden
    And heeft de output "accijnscategorie" waarde "bier"
    And heeft de output "tarief_per_hectoliter" waarde "45.06"
    And heeft de output "verschuldigde_accijns" waarde "2253.0"
    And is de output "agp_vergunning_vereist" waar
    And is de output "heeft_agp_vergunning" waar
    And is de output "voldoet_aan_vergunningsplicht" waar

  Scenario: Kleine brouwerij - licht bier (2% vol) - minimum tarief geldt ook bij verlaagd tarief
    # Casus: Kleine brouwerij, 2% bier. 7,51 x 2 = 15,02 < minimum 26,13
    # Minimum van 26,13 euro/hl geldt.
    Given een organisatie met KVK-nummer "12345678"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 12345678   | 1105     |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 12345678   | true                 |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 2                 | 10                     | true                | productie  |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "26.13"
    And heeft de output "verschuldigde_accijns" waarde "261.3"

  # ====================
  # WIJN - NIET-MOUSSEREND (ARTIKEL 10)
  # ====================

  Scenario: Niet-mousserende wijn met laag alcoholgehalte (7% vol) - laag tarief
    # Casus: Import van 15 hectoliter lichte wijn (7% vol).
    # Artikel 10: alcoholgehalte t/m 8,5% -> tarief 47,95 euro/hl
    # Verschuldigde accijns: 47,95 x 15 = 719,25 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT          | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | wijn_niet_mousserend  | 7                 | 15                     | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "accijnscategorie" waarde "wijn"
    And heeft de output "tarief_per_hectoliter" waarde "47.95"
    And heeft de output "verschuldigde_accijns" waarde "719.25"

  Scenario: Niet-mousserende wijn precies op grenswaarde (8,5% vol) - laag tarief
    # Casus: Wijn met precies 8,5% alcohol valt nog in het lage tarief.
    # Artikel 10: "niet meer dan 8,5 volumeprocent" -> 47,95 euro/hl
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT          | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | wijn_niet_mousserend  | 8.5               | 10                     | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "47.95"
    And heeft de output "verschuldigde_accijns" waarde "479.5"

  Scenario: Niet-mousserende wijn boven grenswaarde (13% vol) - hoog tarief
    # Casus: Franse rode wijn met 13% alcohol.
    # Artikel 10: alcoholgehalte boven 8,5% -> tarief 95,69 euro/hl
    # Verschuldigde accijns: 95,69 x 8 = 765,52 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT          | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | wijn_niet_mousserend  | 13                | 8                      | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "95.69"
    And heeft de output "verschuldigde_accijns" waarde "765.52"

  # ====================
  # WIJN - MOUSSEREND (ARTIKEL 10)
  # ====================

  Scenario: Mousserende wijn / champagne (12% vol) - hoog tarief
    # Casus: Import van 3 hectoliter champagne met 12% alcohol.
    # Artikel 10: mousserende wijn boven 8,5% -> 95,69 euro/hl
    # Verschuldigde accijns: 95,69 x 3 = 287,07 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | wijn_mousserend | 12                | 3                      | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "accijnscategorie" waarde "wijn"
    And heeft de output "tarief_per_hectoliter" waarde "95.69"
    And heeft de output "verschuldigde_accijns" waarde "287.07"

  # ====================
  # TUSSENPRODUCTEN (ARTIKEL 11D)
  # ====================

  Scenario: Port (18% vol) - tussenproduct hoog tarief
    # Casus: Import van 5 hectoliter port met 18% alcohol.
    # Artikel 11d: tussenproduct boven 15% -> 161,80 euro/hl
    # Verschuldigde accijns: 161,80 x 5 = 809,00 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT                    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | tussenproduct_niet_mousserend   | 18                | 5                      | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "accijnscategorie" waarde "tussenproducten"
    And heeft de output "tarief_per_hectoliter" waarde "161.8"
    And heeft de output "verschuldigde_accijns" waarde "809.0"

  Scenario: Sherry (14% vol) - tussenproduct laag tarief
    # Casus: Import van 10 hectoliter sherry met 14% alcohol.
    # Artikel 11d: tussenproduct t/m 15% -> 114,85 euro/hl
    # Verschuldigde accijns: 114,85 x 10 = 1148,50 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT                    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | tussenproduct_niet_mousserend   | 14                | 10                     | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "114.85"
    And heeft de output "verschuldigde_accijns" waarde "1148.5"

  # ====================
  # OVERIGE ALCOHOLHOUDENDE PRODUCTEN / GEDISTILLEERD (ARTIKEL 13)
  # ====================

  Scenario: Whisky (40% vol) - overige alcoholhoudende producten
    # Casus: Import van 2 hectoliter Schotse whisky met 40% alcohol.
    # Artikel 13: 18,27 x 40 = 730,80 euro/hl
    # Verschuldigde accijns: 730,80 x 2 = 1461,60 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | overige_alcohol | 40                | 2                      | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "accijnscategorie" waarde "overige_alcoholhoudende_producten"
    And heeft de output "tarief_per_hectoliter" waarde "730.8"
    And heeft de output "verschuldigde_accijns" waarde "1461.6"

  Scenario: Jenever (30% vol) - overige alcoholhoudende producten
    # Casus: Nederlandse jenever met 30% alcohol, 4 hectoliter.
    # Artikel 13: 18,27 x 30 = 548,10 euro/hl
    # Verschuldigde accijns: 548,10 x 4 = 2192,40 euro
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | overige_alcohol | 30                | 4                      | handel     |
    Then is voldaan aan de voorwaarden
    And heeft de output "tarief_per_hectoliter" waarde "548.1"
    And heeft de output "verschuldigde_accijns" waarde "2192.4"

  # ====================
  # AGP-VERGUNNINGSPLICHT (ARTIKEL 5 JO. ARTIKEL 40)
  # ====================

  Scenario: Productie zonder AGP-vergunning - voldoet NIET aan vergunningsplicht
    # Casus: Een ondernemer produceert bier zonder AGP-vergunning.
    # Artikel 5 lid 1 onder a: het is verboden accijnsgoederen te produceren buiten een AGP.
    # Artikel 40: voor het hebben van een AGP is een vergunning vereist.
    # Verwachting: accijns wordt berekend maar vergunningsplicht is niet vervuld.
    Given een organisatie met KVK-nummer "99887766"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 99887766   | 1105     |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 99887766   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | IS_KLEINE_BROUWERIJ | ACTIVITEIT |
      | bier         | 5                 | 10                     | true                | productie  |
    Then is voldaan aan de voorwaarden
    And is de output "agp_vergunning_vereist" waar
    And is de output "heeft_agp_vergunning" onwaar
    And is de output "voldoet_aan_vergunningsplicht" onwaar

  Scenario: Opslag zonder AGP-vergunning - voldoet NIET aan vergunningsplicht
    # Casus: Een ondernemer slaat wijn op onder accijnsschorsing zonder vergunning.
    # Artikel 5 lid 1: verbod op opslag buiten AGP.
    Given een organisatie met KVK-nummer "99887766"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 99887766   | 4634     |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 99887766   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT          | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | wijn_niet_mousserend  | 13                | 100                    | opslag     |
    Then is voldaan aan de voorwaarden
    And is de output "agp_vergunning_vereist" waar
    And is de output "voldoet_aan_vergunningsplicht" onwaar

  Scenario: Invoer als handelaar - geen AGP-vergunning nodig
    # Casus: Een handelaar importeert whisky. Bij invoer wordt accijns geheven
    # maar een AGP-vergunning is niet nodig als je niet zelf produceert of opslaat.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende DOUANE agp_vergunningen gegevens:
      | kvk_nummer | heeft_agp_vergunning |
      | 85234567   | false                |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT    | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | overige_alcohol | 40                | 1                      | invoer     |
    Then is voldaan aan de voorwaarden
    And is de output "agp_vergunning_vereist" onwaar
    And is de output "voldoet_aan_vergunningsplicht" waar

  # ====================
  # NIET-ACCIJNSGOED / REQUIREMENTS NIET VOLDAAN
  # ====================

  Scenario: Product met 0% alcohol - geen accijnsgoed
    # Casus: Alcoholvrij bier (0% vol) is geen accijnsgoed.
    # Requirements niet voldaan: alcoholpercentage moet groter zijn dan 0.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    When de wet_op_de_accijns/accijnsplicht_alcohol wordt uitgevoerd door DOUANE met
      | TYPE_PRODUCT | ALCOHOLPERCENTAGE | HOEVEELHEID_HECTOLITER | ACTIVITEIT |
      | bier         | 0                 | 10                     | handel     |
    Then is niet voldaan aan de voorwaarden
