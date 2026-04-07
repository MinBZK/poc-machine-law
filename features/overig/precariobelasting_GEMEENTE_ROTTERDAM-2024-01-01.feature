Feature: Bepalen precariobelasting voor terras op openbare grond Rotterdam
  Als horecaondernemer in Rotterdam
  Wil ik weten of en hoeveel precariobelasting ik verschuldigd ben
  Zodat ik mijn kosten voor een terras op gemeentegrond kan bepalen

  # Gebaseerd op de Verordening precariobelasting Rotterdam 2024
  # - Artikel 2: heffing voor voorwerpen op openbare gemeentegrond
  # - Artikel 3: belastingplichtige is de genotshebber
  # - Artikel 5: tarief EUR 36,10/m²/jaar boven vrijstellingsdrempel van 50 m²
  #
  # De precariobelasting vereist een actieve terrasvergunning en gegevens
  # uit het Handelsregister (KVK) en het BAG (Kadaster).

  Background:
    Given de datum is "2024-06-01"
    And een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | status | rechtsvorm | vestigingsadres       |
      | 85234567   | Actief | VOF        | Witte de Withstraat 1 |
    And de volgende KVK bedrijfsgegevens gegevens:
      | kvk_nummer | vestigingsadres       |
      | 85234567   | Witte de Withstraat 1 |
    And de volgende GEMEENTE_ROTTERDAM vestigingen gegevens:
      | kvk_nummer | heeft_terras |
      | 85234567   | true         |
    And de volgende GEMEENTE_ROTTERDAM bgt_terraslocaties gegevens:
      | adres                 | is_openbare_weg |
      | Witte de Withstraat 1 | true            |
    And de volgende GEMEENTE_ROTTERDAM precario_tarieven gegevens:
      | adres                 | gebruik | tarief_per_m2 |
      | Witte de Withstraat 1 | terras  | 25.00         |

  # ====================
  # BELASTINGPLICHTIG
  # ====================

  Scenario: Belastingplichtig - terras 80 m² (boven vrijstellingsdrempel)
    # Casus: Terras van 80 m², vrijstelling eerste 50 m², dus 30 m² belast.
    # Tarief: EUR 36,10/m²/jaar → 30 × 3610 = 108.300 eurocent
    # Verwachting: Belastingplichtig, belasting berekend over 30 m²
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | true                     | 80                   |
    Then is voldaan aan de voorwaarden
    And is de output "is_belastingplichtig" waar
    And heeft de output "heffingsmaatstaf_m2" waarde "30"
    And heeft de output "tarief_per_m2" waarde "3610"
    And heeft de output "belasting_per_jaar" waarde "108300"

  Scenario: Belastingplichtig - terras precies 50 m² (op vrijstellingsdrempel)
    # Casus: Terras precies 50 m², volledig vrijgesteld.
    # Heffingsmaatstaf = MAX(50 - 50, 0) = 0 → belasting = 0
    # Verwachting: Wel belastingplichtig, maar belasting is 0
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | true                     | 50                   |
    Then is voldaan aan de voorwaarden
    And is de output "is_belastingplichtig" waar
    And heeft de output "heffingsmaatstaf_m2" waarde "0"
    And heeft de output "belasting_per_jaar" waarde "0"

  Scenario: Belastingplichtig - klein terras 20 m² (onder vrijstellingsdrempel)
    # Casus: Terras van 20 m², ruim onder de vrijstelling van 50 m².
    # Heffingsmaatstaf = MAX(20 - 50, 0) = 0 → belasting = 0
    # Verwachting: Wel belastingplichtig, maar belasting is 0
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | true                     | 20                   |
    Then is voldaan aan de voorwaarden
    And is de output "is_belastingplichtig" waar
    And heeft de output "heffingsmaatstaf_m2" waarde "0"
    And heeft de output "belasting_per_jaar" waarde "0"

  # ====================
  # NIET BELASTINGPLICHTIG
  # ====================

  Scenario: Niet belastingplichtig - geen terras
    # Casus: Het bedrijf heeft geen terras op openbare gemeentegrond.
    # Verwachting: Niet belastingplichtig
    Given de volgende GEMEENTE_ROTTERDAM vestigingen gegevens:
      | kvk_nummer | heeft_terras |
      | 85234567   | false        |
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | true                     | 10                   |
    Then is niet voldaan aan de voorwaarden

  Scenario: Niet belastingplichtig - geen actieve terrasvergunning
    # Casus: Het bedrijf heeft een terras maar geen actieve terrasvergunning.
    # Verwachting: Niet belastingplichtig
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | false                    | 10                   |
    Then is niet voldaan aan de voorwaarden

  Scenario: Niet belastingplichtig - locatie niet op openbare weg
    # Casus: Het terras staat op eigen terrein, niet op gemeentegrond.
    # Verwachting: Niet belastingplichtig
    Given de volgende GEMEENTE_ROTTERDAM bgt_terraslocaties gegevens:
      | adres                 | is_openbare_weg |
      | Witte de Withstraat 1 | false           |
    When de verordening_precariobelasting wordt uitgevoerd door GEMEENTE_ROTTERDAM met
      | HEEFT_ACTIEVE_VERGUNNING | VERGUNDE_OPPERVLAKTE |
      | true                     | 10                   |
    Then is niet voldaan aan de voorwaarden
