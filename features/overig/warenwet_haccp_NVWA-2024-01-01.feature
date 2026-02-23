Feature: Bepalen HACCP-voedselveiligheidsverplichting
  Als horecaondernemer
  Wil ik weten of de HACCP-verplichting op mijn bedrijf van toepassing is
  Zodat ik kan voldoen aan de voedselveiligheidseisen van de Warenwet

  # Gebaseerd op de Warenwet (BWBR0001969) en het Warenwetbesluit hygiëne van levensmiddelen (BWBR0018823):
  # - Artikel 2 Warenwet: verbod op onveilig voedsel
  # - Artikel 4 Warenwet: hygiëne-eisen
  # - Artikel 2-4 Warenwetbesluit: HACCP-verplichting voor levensmiddelenbedrijven
  # - Verordening (EG) 852/2004 artikel 5: HACCP-procedures
  # - Verordening (EG) 852/2004 artikel 6: registratieplicht
  #
  # De bepaling of een bedrijf een levensmiddelenbedrijf is, gebeurt op basis van:
  # 1. De SBI-code uit het handelsregister (KvK)
  # 2. De opgave van de ondernemer (BEREIDT_OF_SERVEERT_VOEDSEL)

  Background:
    Given de datum is "2024-06-01"

  # ====================
  # VERPLICHTING VAN TOEPASSING - SBI-CODE
  # ====================

  Scenario: Horecabedrijf (SBI 56102) met hygiënecode - voldoet aan verplichting
    # Casus: Een koffiezaak met SBI-code 56102 (Cafés) is geregistreerd bij de NVWA
    # en werkt met een goedgekeurde hygiënecode.
    # De SBI-code alleen is voldoende om als levensmiddelenbedrijf te kwalificeren.
    # Verwachting: Verplichting geldt, bedrijf voldoet.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56102    |
    And de volgende NVWA nvwa_registratie gegevens:
      | kvk_nummer | is_geregistreerd_nvwa | heeft_haccp_systeem | type_haccp_systeem |
      | 85234567   | true                  | true                | hygienecode        |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | true                        |
    Then is voldaan aan de voorwaarden
    And is de output "is_levensmiddelenbedrijf" waar
    And is de output "heeft_haccp_verplichting" waar
    And is de output "is_geregistreerd" waar
    And is de output "heeft_haccp_systeem" waar
    And is de output "voldoet_aan_verplichting" waar
    And heeft de output "type_haccp_systeem" waarde "hygienecode"
    And heeft de output "toezichthouder" waarde "NVWA"

  Scenario: Restaurant (SBI 56101) zonder HACCP-systeem - voldoet niet
    # Casus: Een restaurant is wel geregistreerd bij de NVWA maar heeft nog geen
    # HACCP-systeem geïmplementeerd. De SBI-code 56101 (Restaurants) kwalificeert
    # automatisch als levensmiddelenbedrijf.
    # Verwachting: Verplichting geldt, maar bedrijf voldoet NIET.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 56101    |
    And de volgende NVWA nvwa_registratie gegevens:
      | kvk_nummer | is_geregistreerd_nvwa | heeft_haccp_systeem |
      | 85234567   | true                  | false               |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | true                        |
    Then is voldaan aan de voorwaarden
    And is de output "is_levensmiddelenbedrijf" waar
    And is de output "heeft_haccp_verplichting" waar
    And is de output "heeft_haccp_systeem" onwaar
    And is de output "voldoet_aan_verplichting" onwaar

  Scenario: Supermarkt (SBI 4711) met eigen HACCP-plan - voldoet
    # Casus: Een supermarkt met SBI-code 4711 heeft een eigen volledig HACCP-plan
    # en is geregistreerd bij de NVWA.
    # Verwachting: Verplichting geldt, bedrijf voldoet.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 4711     |
    And de volgende NVWA nvwa_registratie gegevens:
      | kvk_nummer | is_geregistreerd_nvwa | heeft_haccp_systeem | type_haccp_systeem |
      | 85234567   | true                  | true                | eigen_haccp_plan   |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | true                        |
    Then is voldaan aan de voorwaarden
    And is de output "is_levensmiddelenbedrijf" waar
    And is de output "voldoet_aan_verplichting" waar
    And heeft de output "type_haccp_systeem" waarde "eigen_haccp_plan"

  # ====================
  # VERPLICHTING VAN TOEPASSING - OPGAVE ONDERNEMER
  # ====================

  Scenario: Bedrijf met niet-voedings SBI maar serveert wel voedsel - verplichting geldt
    # Casus: Een evenementenbureau (SBI niet in levensmiddelen-lijst) dat ook
    # catering verzorgt. De SBI-code dekt de voedselactiviteit niet, maar de
    # ondernemer geeft aan voedsel te bereiden/serveren.
    # Verwachting: Verplichting geldt op basis van opgave ondernemer.
    Given een organisatie met KVK-nummer "85234567"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 85234567   | 8230     |
    And de volgende NVWA nvwa_registratie gegevens:
      | kvk_nummer | is_geregistreerd_nvwa | heeft_haccp_systeem |
      | 85234567   | false                 | false               |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | true                        |
    Then is voldaan aan de voorwaarden
    And is de output "is_levensmiddelenbedrijf" waar
    And is de output "heeft_haccp_verplichting" waar
    And is de output "is_geregistreerd" onwaar
    And is de output "voldoet_aan_verplichting" onwaar

  # ====================
  # VERPLICHTING NIET VAN TOEPASSING
  # ====================

  Scenario: Kledingwinkel - geen levensmiddelenbedrijf
    # Casus: Een kledingwinkel (SBI 4771) bereidt of serveert geen voedsel.
    # Noch de SBI-code noch de opgave wijst op levensmiddelenactiviteiten.
    # Verwachting: Requirements niet voldaan, verplichting niet van toepassing.
    Given een organisatie met KVK-nummer "99999999"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 99999999   | 4771     |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | false                       |
    Then is niet voldaan aan de voorwaarden

  Scenario: IT-bedrijf - geen levensmiddelenbedrijf
    # Casus: Een softwarebedrijf (SBI 6201) heeft geen enkele relatie met voedsel.
    # Verwachting: Requirements niet voldaan.
    Given een organisatie met KVK-nummer "99999999"
    And de volgende KVK organisaties gegevens:
      | kvk_nummer | sbi_code |
      | 99999999   | 6201     |
    When de warenwet/haccp wordt uitgevoerd door NVWA met
      | BEREIDT_OF_SERVEERT_VOEDSEL |
      | false                       |
    Then is niet voldaan aan de voorwaarden
