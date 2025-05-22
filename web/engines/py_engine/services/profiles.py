from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from web.feature_flags import is_vertegenwoordiging_enabled

# Global service data that applies to all profiles
GLOBAL_SERVICES = {
    "CBS": {"levensverwachting": [{"jaar": 2025, "verwachting_65": 20.5}]},
    "KIESRAAD": {"verkiezingen": [{"type": "TWEEDE_KAMER", "verkiezingsdatum": "2025-05-05"}]},
    "JenV": {
        "jurisdicties": [
            {"gemeente": "Amsterdam", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "Amstelveen", "arrondissement": "AMSTERDAM", "rechtbank": "RECHTBANK_AMSTERDAM"},
            {"gemeente": "Haarlem", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "Alkmaar", "arrondissement": "NOORD-HOLLAND", "rechtbank": "RECHTBANK_NOORD_HOLLAND"},
            {"gemeente": "Rotterdam", "arrondissement": "ROTTERDAM", "rechtbank": "RECHTBANK_ROTTERDAM"},
            {"gemeente": "Utrecht", "arrondissement": "MIDDEN-NEDERLAND", "rechtbank": "RECHTBANK_MIDDEN_NEDERLAND"},
            {"gemeente": "Den Haag", "arrondissement": "DEN_HAAG", "rechtbank": "RECHTBANK_DEN_HAAG"},
            {"gemeente": "Groningen", "arrondissement": "NOORD-NEDERLAND", "rechtbank": "RECHTBANK_NOORD_NEDERLAND"},
            {"gemeente": "Maastricht", "arrondissement": "LIMBURG", "rechtbank": "RECHTBANK_LIMBURG"},
            {"gemeente": "Arnhem", "arrondissement": "GELDERLAND", "rechtbank": "RECHTBANK_GELDERLAND"},
        ]
    },
}
PROFILES = {
    # 1. Merijn - ZZP'er in de thuiszorg met jonge kinderen
    "100000001": {
        "name": "Merijn van der Meer",
        "description": "ZZP'er in de thuiszorg, alleenstaande ouder met twee jonge kinderen waarvan één met chronische aandoening",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "100000001",
                        "geboortedatum": "1989-05-15",  # 36 jaar in 2025
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 36,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Meeuwenlaan 28, 1021HS Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 3,  # Merijn + 2 kinderen
                    }
                ],
                "relaties": [{"bsn": "100000001", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "100000001",
                        "straat": "Meeuwenlaan",
                        "huisnummer": "28",
                        "postcode": "1021HS",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [
                    {
                        "bsn": "100000001",
                        "kinderen": [
                            {"geboortedatum": "2020-01-01"},  # 5 jaar in 2025
                            {"geboortedatum": "2022-01-01", "zorgbehoefte": True},
                            # 3 jaar in 2025, met chronische aandoening
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "100000001",
                        "loon_uit_dienstbetrekking": 600000,  # Verlaagd naar €6.000 (onder bijstandsnorm)
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 950000,  # Verlaagd naar €9.500 (onder bijstandsnorm)
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -85000,
                    }
                ],
                "box2": [{"bsn": "100000001", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "100000001",
                        "spaargeld": 580000,  # €5.800 spaargeld (onder de vermogensgrens van €7.500)
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "monthly_income": [{"bsn": "100000001", "bedrag": 129167}],
                # (€6.000 + €9.500) / 12 = €1.291,67 per maand
                "assets": [{"bsn": "100000001", "bedrag": 580000}],  # €5.800 spaargeld, onder vermogensgrens
                "business_income": [{"bsn": "100000001", "bedrag": 950000}],  # €9.500 inkomsten uit onderneming
                "buitenlands_inkomen": [{"bsn": "100000001", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "100000001", "persoonsgebonden_aftrek": 320000}],
            },
            "KVK": {
                "inschrijvingen": [
                    {
                        "bsn": "100000001",
                        "rechtsvorm": "EENMANSZAAK",
                        "status": "ACTIEF",
                        "activiteit": "Thuiszorg",
                        "is_active_entrepreneur": True,
                    }
                ],
                "is_entrepreneur": [{"bsn": "100000001", "waarde": True}],
            },
            "UWV": {
                "arbeidsverhoudingen": [
                    {"bsn": "100000001", "dienstverband_type": "GEEN", "verzekerd_ww": False, "verzekerd_wia": False}
                ]
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "100000001", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "100000001", "onderwijssoort": "GEEN"}],
                "studiefinanciering": [{"bsn": "100000001", "ontvangt_studiefinanciering": False}],
                "is_student": [{"bsn": "100000001", "waarde": False}],
                "receives_study_grant": [{"bsn": "100000001", "waarde": False}],
            },
            "DJI": {
                "detenties": [{"bsn": "100000001", "is_gedetineerd": False}],
                "is_detainee": [{"bsn": "100000001", "waarde": False}],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {"bsn": "100000001", "arbeidsvermogen": "VOLLEDIG", "re_integratie_traject": "Ondernemerscoaching"}
                ]
            },
            "SVB": {
                "retirement_age": [{"bsn": "100000001", "leeftijd": 68}]  # Hogere AOW-leeftijd in 2025
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "100000001",
                        "type": "PERMANENT",  # Valide type voor bijstand
                        "status": "VERLEEND",
                    }
                ],
                "residence_permit_type": [{"bsn": "100000001", "type": "PERMANENT"}],
            },
        },
    },
    # 2. Maria - Parttime werknemer met onregelmatige uren
    "100000002": {
        "name": "Maria Rodriguez",
        "description": "Alleenstaande moeder, parttime werkend in de horeca met onregelmatige uren, vraagt alleen huurtoeslag aan",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "100000002",
                        "geboortedatum": "1987-08-10",  # 38 jaar in 2025
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 38,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Javastraat 54, 1094HK Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 3,  # Maria + 2 kinderen
                    }
                ],
                "relaties": [{"bsn": "100000002", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "100000002",
                        "straat": "Javastraat",
                        "huisnummer": "54",
                        "postcode": "1094HK",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [
                    {
                        "bsn": "100000002",
                        "kinderen": [
                            {"geboortedatum": "2014-05-15"},  # 11 jaar in 2025
                            {"geboortedatum": "2017-03-22"},  # 8 jaar in 2025
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "100000002",
                        "loon_uit_dienstbetrekking": 950000,  # Verlaagd naar €9.500 (onder bijstandsnorm)
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 180000,  # Kleine bijverdiensten
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "100000002", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "100000002",
                        "spaargeld": 230000,  # €2.300 spaargeld (onder vermogensgrens)
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "100000002", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "100000002", "persoonsgebonden_aftrek": 120000}],
                "monthly_income": [{"bsn": "100000002", "bedrag": 79167}],  # €9.500 / 12 = €791,67 per maand
                "assets": [{"bsn": "100000002", "bedrag": 230000}],  # €2.300 spaargeld, onder vermogensgrens
                "business_income": [{"bsn": "100000002", "bedrag": 0}],  # Geen ZZP inkomsten
            },
            "UWV": {
                "arbeidsverhoudingen": [
                    {
                        "bsn": "100000002",
                        "dienstverband_type": "BEPAALDE_TIJD",
                        "dienstverband_uren": 16,  # Verlaagd naar 16 uur
                        "verzekerd_ww": True,
                        "verzekerd_wia": True,
                    }
                ]
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "100000002", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "100000002", "onderwijssoort": "GEEN"}],
                "studiefinanciering": [{"bsn": "100000002", "ontvangt_studiefinanciering": False}],
                "is_student": [{"bsn": "100000002", "waarde": False}],
                "receives_study_grant": [{"bsn": "100000002", "waarde": False}],
            },
            "DJI": {
                "detenties": [{"bsn": "100000002", "is_gedetineerd": False}],
                "is_detainee": [{"bsn": "100000002", "waarde": False}],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {"bsn": "100000002", "arbeidsvermogen": "VOLLEDIG", "re_integratie_traject": "Werkstage"}
                ]
            },
            "SVB": {
                "retirement_age": [{"bsn": "100000002", "leeftijd": 68}]  # Hogere AOW-leeftijd in 2025
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "100000002",
                        "type": "PERMANENT",  # Valide type voor bijstand
                        "status": "VERLEEND",
                    }
                ],
                "residence_permit_type": [{"bsn": "100000002", "type": "PERMANENT"}],
            },
            "KVK": {
                "is_entrepreneur": [{"bsn": "100000002", "waarde": False}],
                "is_active_entrepreneur": [{"bsn": "100000002", "waarde": False}],
            },
        },
    },
    # 3. Omar - Zelfstandige met fluctuerend inkomen in de bouw
    # 3. Omar - Zelfstandige met fluctuerend inkomen in de bouw
    "100000003": {
        "name": "Omar Yilmaz",
        "description": "ZZP'er in de bouwsector met sterk fluctuerend inkomen, moeite met administratie en lage tarieven",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "100000003",
                        "geboortedatum": "1983-11-22",  # 42 jaar in 2025
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 42,
                        "has_dutch_nationality": True,
                        "residence_address": "Kinkerstraat 112, 1053ED Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 3,  # Partner + kind + Omar
                    }
                ],
                "relaties": [
                    {
                        "bsn": "100000003",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "100000013",  # Fictieve partner BSN
                        "has_partner": True,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "100000003",
                        "straat": "Kinkerstraat",
                        "huisnummer": "112",
                        "postcode": "1053ED",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [
                    {
                        "bsn": "100000003",
                        "kinderen": [
                            {"geboortedatum": "2011-08-30"}  # 14 jaar in 2025
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "100000003",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 1250000,  # Verlaagd naar €12.500 (onder bijstandsnorm voor gezin)
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -95000,
                    }
                ],
                "box2": [{"bsn": "100000003", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "100000003",
                        "spaargeld": 120000,  # €1.200 beperkte buffer
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 850000,  # €8.500 schulden (belastingschulden)
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "100000003", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "100000003", "persoonsgebonden_aftrek": 450000}],
                "monthly_income": [{"bsn": "100000003", "bedrag": 104167}],  # €12.500 / 12 = €1.041,67 per maand
                "assets": [{"bsn": "100000003", "bedrag": 120000}],  # €1.200 spaargeld, onder de vermogensgrens
                "business_income": [{"bsn": "100000003", "bedrag": 1250000}],  # €12.500 inkomsten uit onderneming
                "partner_income": [{"bsn": "100000003", "bedrag": 350000}],  # €3.500 partner inkomen
                "partner_assets": [{"bsn": "100000003", "bedrag": 95000}],  # €950 partner vermogen
                "belastingschulden": [
                    {
                        "bsn": "100000003",
                        "totaalbedrag": 850000,  # €8.500 openstaande belastingschulden
                        "betalingsregeling": "LOPEND",
                    }
                ],
            },
            "KVK": {
                "inschrijvingen": [
                    {
                        "bsn": "100000003",
                        "rechtsvorm": "EENMANSZAAK",
                        "status": "ACTIEF",
                        "activiteit": "Bouwwerkzaamheden",
                        "is_active_entrepreneur": True,
                    }
                ],
                "is_entrepreneur": [{"bsn": "100000003", "waarde": True}],
                "is_active_entrepreneur": [{"bsn": "100000003", "waarde": True}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "100000003", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "100000003", "onderwijssoort": "GEEN"}],
                "studiefinanciering": [{"bsn": "100000003", "ontvangt_studiefinanciering": False}],
                "is_student": [{"bsn": "100000003", "waarde": False}],
                "receives_study_grant": [{"bsn": "100000003", "waarde": False}],
            },
            "DJI": {
                "detenties": [{"bsn": "100000003", "is_gedetineerd": False}],
                "is_detainee": [{"bsn": "100000003", "waarde": False}],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {"bsn": "100000003", "arbeidsvermogen": "VOLLEDIG", "re_integratie_traject": "Ondernemerscoaching"}
                ]
            },
            "SVB": {
                "retirement_age": [{"bsn": "100000003", "leeftijd": 68}]  # Hogere AOW-leeftijd in 2025
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "100000003",
                        "type": "PERMANENT",  # Valide type voor bijstand
                        "status": "VERLEEND",
                    }
                ],
                "residence_permit_type": [{"bsn": "100000003", "type": "PERMANENT"}],
            },
        },
    },
    # 4. Fatima - Bijstandsgerechtigde met gedeeltelijke arbeidsongeschiktheid
    "100000004": {
        "name": "Fatima el Hassan",
        "description": "Bijstandsgerechtigde met gedeeltelijke arbeidsongeschiktheid, ontvangt alle toeslagen maar komt moeilijk rond",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "100000004",
                        "geboortedatum": "1971-09-08",  # 54 jaar in 2025
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 54,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Van der Pekstraat 87, 1031CN Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 1,  # Alleenstaand
                    }
                ],
                "relaties": [{"bsn": "100000004", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "100000004",
                        "straat": "Van der Pekstraat",
                        "huisnummer": "87",
                        "postcode": "1031CN",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "100000004",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1089000,  # Bijstandsuitkering
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "100000004", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "100000004",
                        "spaargeld": 380000,  # €3.800 spaargeld (onder de vermogensgrens van €7.500)
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "100000004", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "100000004", "persoonsgebonden_aftrek": 0}],
                "monthly_income": [{"bsn": "100000004", "bedrag": 0}],  # Voor bijstandsberekening
                "assets": [{"bsn": "100000004", "bedrag": 380000}],  # Voor vermogenstoets bijstand (onder limiet)
                "business_income": [{"bsn": "100000004", "bedrag": 0}],  # Geen inkomsten uit onderneming
            },
            "UWV": {
                "arbeidsongeschiktheid": [
                    {
                        "bsn": "100000004",
                        "percentage": 40,  # 40% arbeidsongeschikt
                        "diagnose_categorie": "BEWEGINGSAPPARAAT",
                        "uitkering_type": "GEEN",  # Geen WIA/WAO door onvoldoende arbeidsverleden
                    }
                ],
                "arbeidsverhoudingen": [
                    {"bsn": "100000004", "dienstverband_type": "GEEN", "verzekerd_ww": False, "verzekerd_wia": False}
                ],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "100000004",
                        "arbeidsvermogen": "MEDISCH_VOLLEDIG",  # Gewijzigd naar volledige ontheffing voor bijstand
                        "ontheffing_reden": "Chronische ziekte",
                        "ontheffing_einddatum": "2026-09-01",
                        "re_integratie_traject": "Aangepast traject",  # Toegevoegd voor bijstand
                    }
                ]
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "100000004", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "100000004", "onderwijssoort": "GEEN"}],
                "studiefinanciering": [{"bsn": "100000004", "ontvangt_studiefinanciering": False}],
                "is_student": [{"bsn": "100000004", "waarde": False}],
                "receives_study_grant": [{"bsn": "100000004", "waarde": False}],
            },
            "DJI": {
                "detenties": [{"bsn": "100000004", "is_gedetineerd": False}],
                "is_detainee": [{"bsn": "100000004", "waarde": False}],
            },
            "SVB": {
                "retirement_age": [{"bsn": "100000004", "leeftijd": 68}]  # Hogere AOW-leeftijd in 2025
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "100000004",
                        "type": "PERMANENT",  # Valide type voor bijstand
                        "status": "VERLEEND",
                    }
                ],
                "residence_permit_type": [{"bsn": "100000004", "type": "PERMANENT"}],
            },
            "KVK": {
                "is_entrepreneur": [{"bsn": "100000004", "waarde": False}],
                "is_active_entrepreneur": [{"bsn": "100000004", "waarde": False}],
            },
        },
    },
    "999993653": {
        "name": "Jan Jansen",
        "description": "Jongere met part-time baan naast MBO opleiding, komt in aanmerking voor zorgtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993653",
                        "geboortedatum": "2005-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993653",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993653",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993653",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993653",
                        "loon_uit_dienstbetrekking": 1850000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -60000,
                    }
                ],
                "box2": [{"bsn": "999993653", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993653",
                        "spaargeld": 5000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993653", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993653", "persoonsgebonden_aftrek": 120000}],
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "999993653", "onderwijssoort": "MBO", "niveau": 4}],
                "studiefinanciering": [{"bsn": "999993653", "aantal_studerende_broers_zussen": 0}],
            },
            "DJI": {"detenties": [{"bsn": "999993653", "status": "VRIJ", "inrichting_type": "GEEN"}]},
            "SVB": {"verzekerde_tijdvakken": [{"bsn": "999993653", "woonperiodes": 35}]},
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993653",
                        "arbeidsvermogen": "VOLLEDIG",
                        "re_integratie_traject": "Werkstage",
                    }
                ]
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "999993653",
                        "type": "ONBEPAALDE_TIJD_REGULIER",
                        "status": "VERLEEND",
                        "ingangsdatum": "2015-01-01",
                        "einddatum": None,
                    }
                ]
            },
        },
    },
    "999993654": {
        "name": "Maria Pietersen",
        "description": "AOW-gerechtigde met volledige opbouw, gehuwd, partner nog geen AOW-leeftijd",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993654",
                        "geboortedatum": "1948-02-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993654",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999993655",
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993654",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "SVB": {"verzekerde_tijdvakken": [{"bsn": "999993654", "woonperiodes": 50}]},
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993654",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1380000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -75000,
                    }
                ],
                "box2": [{"bsn": "999993654", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993654",
                        "spaargeld": 8500000,
                        "beleggingen": 3700000,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993654", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993654", "persoonsgebonden_aftrek": 230000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993654",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
        },
    },
    "999993655": {
        "name": "Sarah de Wit",
        "description": "Dakloze met briefadres, recht op bijstand met woonkostentoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993655",
                        "geboortedatum": "1980-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993655",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993655",
                        "straat": "De Regenboog Groep",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "BRIEFADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993655",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993655", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993655",
                        "spaargeld": 250000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993655", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993655", "persoonsgebonden_aftrek": 0}],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993655",
                        "arbeidsvermogen": "VOLLEDIG",
                        "re_integratie_traject": "Werkstage",
                    }
                ]
            },
        },
    },
    "999993656": {
        "name": "Peter Bakker",
        "description": "ZZP'er met laag inkomen, recht op aanvullende bijstand en startkapitaal",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993656",
                        "geboortedatum": "1985-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993656",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993656",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993656",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 3850000,  # Verhoogd naar €38.500
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -110000,
                    }
                ],
                "box2": [{"bsn": "999993656", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993656",
                        "spaargeld": 1550000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993656", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993656", "persoonsgebonden_aftrek": 850000}],
            },
            "KVK": {
                "inschrijvingen": [
                    {
                        "bsn": "999993656",
                        "rechtsvorm": "EENMANSZAAK",
                        "status": "ACTIEF",
                        "activiteit": "Webdesign",
                    }
                ]
            },
        },
    },
    "999993657": {
        "name": "Emma Visser",
        "description": "Persoon met medische ontheffing, recht op bijstand zonder re-integratieverplichting",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993657",
                        "geboortedatum": "1975-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993657",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993657",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993657",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1089000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -45000,
                    }
                ],
                "box2": [{"bsn": "999993657", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993657",
                        "spaargeld": 3250000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993657", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993657", "persoonsgebonden_aftrek": 180000}],
            },
            "GEMEENTE_AMSTERDAM": {
                "werk_en_re_integratie": [
                    {
                        "bsn": "999993657",
                        "arbeidsvermogen": "MEDISCH_VOLLEDIG",
                        "ontheffing_reden": "Chronische ziekte",
                        "ontheffing_einddatum": "2026-01-01",
                    }
                ]
            },
        },
    },
    "999993658": {
        "name": "Thomas Mulder",
        "description": "Student met laag inkomen en studiefinanciering, recht op zorgtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993658",
                        "geboortedatum": "2004-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993658",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993658",
                        "straat": "Science Park",
                        "huisnummer": "123",
                        "postcode": "1098XG",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {"verzekeringen": [{"bsn": "999993658", "polis_status": "ACTIEF"}]},
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993658",
                        "loon_uit_dienstbetrekking": 825000,
                        "uitkeringen_en_pensioenen": 1025000,  # Studiefinanciering
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 230000,  # Bijbaantjes
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993658", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993658",
                        "spaargeld": 1200000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 1800000,  # Studieschuld
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993658", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993658", "persoonsgebonden_aftrek": 75000}],
            },
            "DUO": {
                "inschrijvingen": [{"bsn": "999993658", "onderwijstype": "WO"}],
                "studiefinanciering": [{"bsn": "999993658", "aantal_studerend_gezin": 0}],
            },
        },
    },
    "999993659": {
        "name": "Anna Schmidt",
        "description": "Duitse student zonder stemrecht voor de Tweede Kamer",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993659",
                        "geboortedatum": "1990-01-01",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "DUITS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993659",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993659",
                        "straat": "Kalverstraat",
                        "huisnummer": "1",
                        "postcode": "1012NX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993659",
                        "loon_uit_dienstbetrekking": 1750000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 350000,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993659", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993659",
                        "spaargeld": 950000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993659", "bedrag": 450000, "land": "DUITSLAND"}],
                "aftrekposten": [{"bsn": "999993659", "persoonsgebonden_aftrek": 65000}],
            },
            "DUO": {"inschrijvingen": [{"bsn": "999993659", "onderwijstype": "WO"}]},
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "999993659",
                        "type": "STUDIE",
                        "status": "VERLEEND",
                        "ingangsdatum": "2022-09-01",
                        "einddatum": "2025-08-31",
                    }
                ]
            },
        },
    },
    "999993660": {
        "name": "Lisa de Jong",
        "description": "Werkende ouder met jong kind, komt in aanmerking voor inkomensafhankelijke combinatiekorting",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993660",
                        "geboortedatum": "1998-05-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993660",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993660",
                        "straat": "Prinsengracht",
                        "huisnummer": "42",
                        "postcode": "1015DX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [{"bsn": "999993660", "kinderen": [{"geboortedatum": "2020-01-01"}]}],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993660",
                        "loon_uit_dienstbetrekking": 3000000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -90000,
                    }
                ],
                "box2": [{"bsn": "999993660", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993660",
                        "spaargeld": 2000000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "aftrekposten": [
                    {
                        "bsn": "999993660",
                        "persoonsgebonden_aftrek": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993660", "bedrag": 0, "land": "GEEN"}],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "999993660",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
        },
    },
    "777777777": {
        "name": "Fatima Al-Zahra",
        "description": "Alleenstaande met laag inkomen en hoge huur, komt in aanmerking voor huurtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "777777777",
                        "geboortedatum": "1991-04-15",
                        "verblijfsadres": "Utrecht",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "MAROKKAANS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "777777777",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "777777777",
                        "straat": "Rooseveltlaan",
                        "huisnummer": "42",
                        "postcode": "3527AK",
                        "woonplaats": "Utrecht",
                        "type": "WOONADRES",
                    }
                ],
            },
            "RVZ": {
                "verzekeringen": [
                    {
                        "bsn": "777777777",
                        "polis_status": "ACTIEF",
                        "verdrag_status": "GEEN",
                        "zorg_type": "BASIS",
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "777777777",
                        "loon_uit_dienstbetrekking": 1750000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 25000,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "777777777", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "777777777",
                        "spaargeld": 1200000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "777777777", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "777777777", "persoonsgebonden_aftrek": 85000}],
            },
            "IND": {
                "verblijfsvergunningen": [
                    {
                        "bsn": "777777777",
                        "type": "ONBEPAALDE_TIJD_REGULIER",
                        "status": "VERLEEND",
                        "ingangsdatum": "2010-05-12",
                        "einddatum": None,
                    }
                ]
            },
        },
    },
    "888888888": {
        "name": "Sarah de Boer",
        "description": "Alleenstaande ouder met kinderopvang, komt in aanmerking voor kinderopvangtoeslag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "888888888",
                        "geboortedatum": "1990-05-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "888888888",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                        "children": [{"bsn": "111111111"}, {"bsn": "222222222"}],
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "888888888",
                        "straat": "Keizersgracht",
                        "huisnummer": "123",
                        "postcode": "1015CJ",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "children": [
                    {"kind_bsn": "111111111", "geboortedatum": "2020-03-01", "naam": "Sem de Jong"},
                    {"kind_bsn": "222222222", "geboortedatum": "2022-07-15", "naam": "Emma de Jong"},
                ],
            },
            "UWV": {
                "dienstverbanden": [
                    {
                        "bsn": "888888888",
                        "start_date": "2024-01-15",
                        "end_date": "2024-01-30",
                        "uren_per_week": 32,
                        "worked_hours": 1664,  # 32 hours × 52 weeks
                    }
                ],
                "wet_structuur_uitvoeringsorganisatie_werk_en_inkomen": [{"BSN": "888888888", "insured_years": 5}],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "888888888",
                        "loon_uit_dienstbetrekking": 3600000,  # €36.000
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "888888888", "dividend": 0, "vervreemding_aandelen": 0}],
                "box3": [
                    {
                        "bsn": "888888888",
                        "spaargeld": 800000,  # €8.000
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
            },
        },
    },
    # Wilsonbekwame persoon en vertegenwoordiger
    "999993800": {
        "name": "Wil Sonbekwaam",
        "description": "Wilsonbekwame persoon met wettelijke vertegenwoordiger",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993800",
                        "geboortedatum": "1960-05-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 65,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Amsteldijk 128, 1078RS Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 1,
                    }
                ],
                "relaties": [{"bsn": "999993800", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "999993800",
                        "straat": "Amsteldijk",
                        "huisnummer": "128",
                        "postcode": "1078RS",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "wilsbekwaamheid": [
                    {
                        "bsn": "999993800",
                        "status": "WILSONBEKWAAM",
                        "sinds": "2023-04-15",
                    }
                ],
                "vertegenwoordiging": [
                    {
                        "bsn": "999993800",
                        "type": "CURATELE",
                        "vertegenwoordigers": [
                            {
                                "bsn": "999993801",
                                "naam": "Jan Vertegenwoordiger",
                                "sinds": "2023-05-01",
                            }
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993800",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1380000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993800", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993800",
                        "spaargeld": 4500000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993800", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993800", "persoonsgebonden_aftrek": 120000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993800", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
    "999993801": {
        "name": "Jan Vertegenwoordiger",
        "description": "Wettelijke vertegenwoordiger van meerdere personen",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993801",
                        "geboortedatum": "1965-03-20",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 60,
                        "has_dutch_nationality": True,
                        "has_partner": True,
                        "residence_address": "Singel 42, 1015AB Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 2,
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993801",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999993802",
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993801",
                        "straat": "Singel",
                        "huisnummer": "42",
                        "postcode": "1015AB",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "vertegenwoordiging": [
                    {
                        "bsn": "999993801",
                        "vertegenwoordigt_voor": [
                            {
                                "bsn": "999993800",
                                "naam": "Wil Sonbekwaam",
                                "type": "CURATELE",
                                "sinds": "2023-05-01",
                            },
                            {
                                "bsn": "999993805",
                                "naam": "Sara Dementie",
                                "type": "MENTORSCHAP",
                                "sinds": "2022-11-15",
                            },
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993801",
                        "loon_uit_dienstbetrekking": 3850000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -95000,
                    }
                ],
                "box2": [{"bsn": "999993801", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993801",
                        "spaargeld": 3250000,
                        "beleggingen": 1500000,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993801", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993801", "persoonsgebonden_aftrek": 210000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993801", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
    # Ouder met minderjarig kind
    "999993901": {
        "name": "Peter Ouderman",
        "description": "Ouder met minderjarig kind",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993901",
                        "geboortedatum": "1980-05-15",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 45,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Prinsengracht 42, 1015DX Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 2,
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993901",
                        "partnerschap_type": "GEEN",
                        "partner_bsn": None,
                        "children": [{"bsn": "999993902", "geboortedatum": "2015-03-20", "naam": "Kind Minderjarig"}],
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993901",
                        "straat": "Prinsengracht",
                        "huisnummer": "42",
                        "postcode": "1015DX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "vertegenwoordiging": [
                    {
                        "bsn": "999993901",
                        "vertegenwoordigt_voor": [
                            {
                                "bsn": "999993902",
                                "naam": "Kind Minderjarig",
                                "type": "OUDERLIJK_GEZAG",
                                "sinds": "2015-03-20",
                            }
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993901",
                        "loon_uit_dienstbetrekking": 4250000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -120000,
                    }
                ],
                "box2": [{"bsn": "999993901", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993901",
                        "spaargeld": 2800000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993901", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993901", "persoonsgebonden_aftrek": 180000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993901", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
    "999993902": {
        "name": "Kind Minderjarig",
        "description": "Minderjarig kind met twee ouders als wettelijke vertegenwoordigers",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993902",
                        "geboortedatum": "2015-03-20",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 10,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Prinsengracht 42, 1015DX Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 3,
                    }
                ],
                "relaties": [{"bsn": "999993902", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "999993902",
                        "straat": "Prinsengracht",
                        "huisnummer": "42",
                        "postcode": "1015DX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "vertegenwoordiging": [
                    {
                        "bsn": "999993902",
                        "type": "OUDERLIJK_GEZAG",
                        "vertegenwoordigers": [
                            {
                                "bsn": "999993901",
                                "naam": "Peter Ouderman",
                                "sinds": "2015-03-20",
                            },
                            {
                                "bsn": "999993903",
                                "naam": "Maria Ouderman",
                                "sinds": "2015-03-20",
                            },
                        ],
                    }
                ],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993902", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
    "999993903": {
        "name": "Maria Ouderman",
        "description": "Moeder met ouderlijk gezag",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993903",
                        "geboortedatum": "1978-10-28",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 46,
                        "has_dutch_nationality": True,
                        "has_partner": True,
                        "residence_address": "Prinsengracht 42, 1015DX Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 3,
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993903",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999993901",
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993903",
                        "straat": "Prinsengracht",
                        "huisnummer": "42",
                        "postcode": "1015DX",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "vertegenwoordiging": [
                    {
                        "bsn": "999993903",
                        "vertegenwoordigt_voor": [
                            {
                                "bsn": "999993902",
                                "naam": "Kind Minderjarig",
                                "type": "OUDERLIJK_GEZAG",
                                "sinds": "2015-03-20",
                            }
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993903",
                        "loon_uit_dienstbetrekking": 4560000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": -120000,
                    }
                ],
                "box2": [{"bsn": "999993903", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993903",
                        "spaargeld": 1950000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993903", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993903", "persoonsgebonden_aftrek": 150000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993903", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
    "999993805": {
        "name": "Sara Dementie",
        "description": "Persoon met mentorschap wegens dementie",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993805",
                        "geboortedatum": "1940-05-16",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                        "age": 84,
                        "has_dutch_nationality": True,
                        "has_partner": False,
                        "residence_address": "Zorgcentrum De Linde, Lindestraat 10, 1015RS Amsterdam",
                        "has_fixed_address": True,
                        "household_size": 1,
                    }
                ],
                "relaties": [{"bsn": "999993805", "partnerschap_type": "GEEN", "partner_bsn": None}],
                "verblijfplaats": [
                    {
                        "bsn": "999993805",
                        "straat": "Lindestraat",
                        "huisnummer": "10",
                        "postcode": "1015RS",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
            },
            "JenV": {
                "wilsbekwaamheid": [
                    {
                        "bsn": "999993805",
                        "status": "WILSONBEKWAAM",
                        "sinds": "2022-10-28",
                    }
                ],
                "vertegenwoordiging": [
                    {
                        "bsn": "999993805",
                        "type": "MENTORSCHAP",
                        "vertegenwoordigers": [
                            {
                                "bsn": "999993801",
                                "naam": "Jan Vertegenwoordiger",
                                "sinds": "2022-11-15",
                            }
                        ],
                    }
                ],
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993805",
                        "loon_uit_dienstbetrekking": 0,
                        "uitkeringen_en_pensioenen": 1950000,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [{"bsn": "999993805", "reguliere_voordelen": 0, "vervreemdingsvoordelen": 0}],
                "box3": [
                    {
                        "bsn": "999993805",
                        "spaargeld": 12500000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993805", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993805", "persoonsgebonden_aftrek": 450000}],
            },
            "RVZ": {
                "verzekeringen": [
                    {"bsn": "999993805", "polis_status": "ACTIEF", "verdrag_status": "GEEN", "zorg_type": "BASIS"}
                ]
            },
        },
    },
}


def get_profile_data(bsn: str) -> dict[str, Any] | None:
    """Get profile data for a specific BSN"""
    return PROFILES.get(bsn)


def get_profile_properties(profile: dict) -> list[str]:
    """Extract key properties from a profile with emoji representations"""
    properties = []

    # Check if sources and RvIG data exist
    if not profile.get("sources") or not profile["sources"].get("RvIG"):
        return properties

    rvig_data = profile["sources"]["RvIG"]

    # Extract person data
    person_data = next(iter(rvig_data.get("personen", [])), {})
    if not person_data:
        return properties

    # Add nationality
    nationality = person_data.get("nationaliteit")
    if nationality:
        if nationality == "NEDERLANDS":
            properties.append("🇳🇱 Nederlands")
        elif nationality == "DUITS":
            properties.append("🇩🇪 Duits")
        elif nationality == "MAROKKAANS":
            properties.append("🇲🇦 Marokkaans")
        else:
            properties.append(f"🌍 {nationality}")

    # Add age
    if "geboortedatum" in person_data:
        birth_date_str = person_data["geboortedatum"]
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        current_date = datetime.now()
        age = relativedelta(current_date, birth_date).years
        properties.append(f"🗓️ {age} jaar")

    # Add children
    children_data = rvig_data.get("CHILDREN_DATA", [])
    for child_entry in children_data:
        if "kinderen" in child_entry:
            num_children = len(child_entry["kinderen"])
            if num_children == 1:
                properties.append("👶 1 kind")
            elif num_children > 1:
                properties.append(f"👨‍👩‍👧‍👦 {num_children} kinderen")

    # Add housing status
    address_data = next(iter(rvig_data.get("verblijfplaats", [])), {})
    if address_data:
        address_type = address_data.get("type")
        if address_type == "WOONADRES":
            properties.append("🏠 Vast woonadres")
        elif address_type == "BRIEFADRES":
            properties.append("📫 Briefadres")

    # Add work status
    is_entrepreneur = False
    if "KVK" in profile["sources"]:
        kvk_data = profile["sources"]["KVK"]
        if any(entry.get("waarde") for entry in kvk_data.get("is_entrepreneur", [])):
            is_entrepreneur = True
            properties.append("💼 ZZP'er")

    if "UWV" in profile["sources"]:
        uwv_data = profile["sources"]["UWV"]
        if "arbeidsverhoudingen" in uwv_data:
            for relation in uwv_data["arbeidsverhoudingen"]:
                if relation.get("dienstverband_type") != "GEEN" and not is_entrepreneur:
                    properties.append("👔 In loondienst")

    # Add student status
    if "DUO" in profile["sources"]:
        duo_data = profile["sources"]["DUO"]
        if "inschrijvingen" in duo_data:
            for enrollment in duo_data["inschrijvingen"]:
                if enrollment.get("onderwijssoort") != "GEEN":
                    properties.append("🎓 Student")

    # Add disability status
    if "UWV" in profile["sources"] and "arbeidsongeschiktheid" in profile["sources"]["UWV"]:
        for disability in profile["sources"]["UWV"]["arbeidsongeschiktheid"]:
            percentage = disability.get("percentage")
            if percentage:
                properties.append(f"♿ {percentage}% arbeidsongeschikt")

    if is_vertegenwoordiging_enabled():
        # Add wilsonbekwaamheid (incapacity) status
        if "JenV" in profile["sources"] and "wilsbekwaamheid" in profile["sources"]["JenV"]:
            for wilsbekwaamheid in profile["sources"]["JenV"]["wilsbekwaamheid"]:
                status = wilsbekwaamheid.get("status")
                if status == "WILSONBEKWAAM":
                    properties.append("⚠️ Wilsonbekwaam")

        # Add vertegenwoordiging (representation) status
        if "JenV" in profile["sources"] and "vertegenwoordiging" in profile["sources"]["JenV"]:
            # Check if person is being represented
            if any(entry.get("vertegenwoordigers") for entry in profile["sources"]["JenV"]["vertegenwoordiging"]):
                for entry in profile["sources"]["JenV"]["vertegenwoordiging"]:
                    rep_type = entry.get("type")
                    if rep_type == "CURATELE":
                        properties.append("👨‍⚖️ Onder curatele")
                    elif rep_type == "MENTORSCHAP":
                        properties.append("🧠 Onder mentorschap")
                    elif rep_type == "OUDERLIJK_GEZAG":
                        properties.append("👪 Onder ouderlijk gezag")
                    else:
                        properties.append("🔄 Heeft vertegenwoordiger")

            # Check if person is a representative for others
            if any(entry.get("vertegenwoordigt_voor") for entry in profile["sources"]["JenV"]["vertegenwoordiging"]):
                for entry in profile["sources"]["JenV"]["vertegenwoordiging"]:
                    if "vertegenwoordigt_voor" in entry:
                        num_represented = len(entry["vertegenwoordigt_voor"])
                        if num_represented == 1:
                            properties.append("⚖️ Vertegenwoordigt 1 persoon")
                        elif num_represented > 1:
                            properties.append(f"⚖️ Vertegenwoordigt {num_represented} personen")

    return properties


def get_all_profiles() -> dict[str, dict[str, Any]]:
    """Get all available profiles with properties"""
    profiles = PROFILES.copy()

    # Add properties to each profile
    for bsn, profile in profiles.items():
        profile["properties"] = get_profile_properties(profile)

    return profiles
