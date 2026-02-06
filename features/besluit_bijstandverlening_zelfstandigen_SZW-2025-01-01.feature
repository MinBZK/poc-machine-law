Feature: Bepalen recht op bijstand voor zelfstandigen (Bbz 2004)
  Als zelfstandige ondernemer
  Wil ik weten of ik recht heb op bijstand volgens de Bbz 2004
  Zodat ik weet welke financiële ondersteuning ik kan krijgen

  Background:
    Given de datum is "2025-03-01"
    And een persoon met BSN "999993653"
    And de volgende CBS levensverwachting gegevens:
      | jaar | verwachting_65 |
      | 2025 | 20.5           |
    And de volgende IND verblijfsvergunningen gegevens:
      | bsn       | type                     | status   | ingangsdatum | einddatum |
      | 999993653 | ONBEPAALDE_TIJD_REGULIER | VERLEEND | 2015-01-01   | null      |

  # ============================================================================
  # GEVESTIGDE ZELFSTANDIGEN (Artikelen 18-22)
  # ============================================================================

  Scenario: Gevestigde zelfstandige met levensvatbaar bedrijf krijgt bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1985-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000000   | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Thuiszorg  |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | GEVESTIGD         | true                  | 5                     | 40            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is voldaan aan de voorwaarden
    And heeft de output "categorie_zelfstandige" waarde "GEVESTIGD"
    And heeft de output "max_duur_maanden" waarde "12"
    And is het bedrijfskapitaal_max "253420.00" euro
    And heeft de output "bedrijfskapitaal_type" waarde "LENING_RENTE"

  Scenario: Gevestigde zelfstandige met te hoog vermogen krijgt geen bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1985-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld  | beleggingen | onroerend_goed | schulden |
      | 999993653 | 250000000  | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Adviesbureau |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | GEVESTIGD         | true                  | 10                    | 50            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  Scenario: Gevestigde zelfstandige met niet-levensvatbaar bedrijf krijgt geen bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1985-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 1000000   | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Webshop    |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | GEVESTIGD         | false                 | 3                     | 35            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  # ============================================================================
  # BEGINNENDE ZELFSTANDIGEN (Artikelen 23-24)
  # ============================================================================

  Scenario: Beginnende zelfstandige na WW-uitkering krijgt 36 maanden bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | nationaliteit | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLANDS    | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 500000    | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit    |
      | 999993653 | EENMANSZAAK | ACTIEF | Grafisch ontwerp |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 999993653 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon |
      | 999993653 | 40                      | 0                     | 30                | 5                     | 3600000  |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 999993653 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 999993653 | false               |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 999993653 | false          |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | BEGINNEND         | true                  | 0                     | 30            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is voldaan aan de voorwaarden
    And heeft de output "categorie_zelfstandige" waarde "BEGINNEND"
    And heeft de output "max_duur_maanden" waarde "36"
    And is het bedrijfskapitaal_max "46656.00" euro
    And heeft de output "bedrijfskapitaal_type" waarde "LENING_RENTE"

  Scenario: Beginnende zelfstandige zonder WW-uitkering krijgt geen bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres | nationaliteit | land_verblijf |
      | 999993653 | 1990-01-01    | Amsterdam      | NEDERLANDS    | NEDERLAND     |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 500000    | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Fotografie |
    And de volgende SVB algemene_ouderdomswet_gegevens gegevens:
      | bsn       | pensioenleeftijd |
      | 999993653 | 67               |
    And de volgende UWV uwv_werkgegevens gegevens:
      | bsn       | gemiddeld_uren_per_week | huidige_uren_per_week | gewerkte_weken_36 | arbeidsverleden_jaren | jaarloon |
      | 999993653 | 0                       | 0                     | 0                 | 0                     | 0        |
    And de volgende UWV ziektewet gegevens:
      | bsn       | heeft_ziektewet_uitkering |
      | 999993653 | false                     |
    And de volgende UWV WIA gegevens:
      | bsn       | heeft_wia_uitkering |
      | 999993653 | false               |
    And de volgende DJI detentie gegevens:
      | bsn       | is_gedetineerd |
      | 999993653 | false          |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | BEGINNEND         | true                  | 0                     | 25            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  # ============================================================================
  # OUDERE ZELFSTANDIGEN (Artikelen 25-26)
  # ============================================================================

  Scenario: Oudere zelfstandige (geboren voor 1960) met niet-levensvatbaar bedrijf krijgt onbeperkte bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1958-06-15    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 10000000  | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit  |
      | 999993653 | EENMANSZAAK | ACTIEF | Timmerbedrijf |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | OUDER             | false                 | 25                    | 30            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is voldaan aan de voorwaarden
    And heeft de output "categorie_zelfstandige" waarde "OUDER"
    And heeft de output "max_duur_maanden" waarde "0"
    And is het bedrijfskapitaal_max "12671.00" euro
    And heeft de output "bedrijfskapitaal_type" waarde "OM_NIET"

  Scenario: Oudere zelfstandige met te hoog vermogen krijgt geen bijstand
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1958-06-15    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld  | beleggingen | onroerend_goed | schulden |
      | 999993653 | 180000000  | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Schildersbedrijf |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | OUDER             | false                 | 30                    | 25            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  Scenario: Oudere zelfstandige geboren na 1960 komt niet in aanmerking als oudere
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1965-03-20    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000000   | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Loodgieter |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | OUDER             | false                 | 20                    | 30            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  Scenario: Oudere zelfstandige met minder dan 10 jaar ondernemerschap komt niet in aanmerking
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1958-06-15    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 5000000   | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Bakkerij   |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | OUDER             | false                 | 8                     | 35            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  # ============================================================================
  # BEEINDIGENDE ZELFSTANDIGEN (Artikel 27)
  # ============================================================================

  Scenario: Beeindigende zelfstandige krijgt uitloopbijstand zonder bedrijfskapitaal
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1980-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 2000000   | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Restaurant |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | BEEINDIGEND       | false                 | 7                     | 25            | 2025-12-01        |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is voldaan aan de voorwaarden
    And heeft de output "categorie_zelfstandige" waarde "BEEINDIGEND"
    And heeft de output "max_duur_maanden" waarde "12"
    And is het bedrijfskapitaal_max "0.00" euro
    And heeft de output "bedrijfskapitaal_type" waarde "GEEN"

  # ============================================================================
  # URENCRITERIUM (Artikel 1 lid 1 onder b)
  # ============================================================================

  Scenario: Persoon voldoet niet aan urencriterium (minder dan 24 uur per week)
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1985-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 500000    | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status | activiteit |
      | 999993653 | EENMANSZAAK | ACTIEF | Consultant |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | GEVESTIGD         | true                  | 5                     | 20            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden

  # ============================================================================
  # NIET-ONDERNEMER
  # ============================================================================

  Scenario: Persoon zonder actieve onderneming krijgt geen Bbz
    Given de volgende RvIG personen gegevens:
      | bsn       | geboortedatum | verblijfsadres |
      | 999993653 | 1985-01-01    | Amsterdam      |
    And de volgende RvIG relaties gegevens:
      | bsn       | partnerschap_type | partner_bsn |
      | 999993653 | GEEN              | null        |
    And de volgende BELASTINGDIENST box3 gegevens:
      | bsn       | spaargeld | beleggingen | onroerend_goed | schulden |
      | 999993653 | 500000    | 0           | 0              | 0        |
    And de volgende KVK inschrijvingen gegevens:
      | bsn       | rechtsvorm  | status    | activiteit |
      | 999993653 | EENMANSZAAK | OPGEHEVEN | Winkel     |
    And de volgende SZW bbz_aanvraag gegevens:
      | bsn       | type_zelfstandige | bedrijf_levensvatbaar | jaren_ondernemerschap | uren_per_week | beeindigingsdatum |
      | 999993653 | GEVESTIGD         | true                  | 3                     | 40            | null              |
    When de besluit_bijstandverlening_zelfstandigen wordt uitgevoerd door SZW
    Then is niet voldaan aan de voorwaarden
