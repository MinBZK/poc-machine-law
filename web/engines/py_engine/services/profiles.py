from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta

# Global service data that applies to all profiles
GLOBAL_SERVICES = {
    "CBS": {"levensverwachting": [{"jaar": 2025, "verwachting_65": 20.5}]},
    "KIESRAAD": {"verkiezingen": [{"type": "TWEEDE_KAMER", "verkiezingsdatum": "2025-10-29"}]},
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
    # Merijn - ZZP'er in de thuiszorg met jonge kinderen
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
    # Linda - Parttime werkende moeder met twee jonge kinderen
    "999991905": {
        "name": "Linda Vieltlep",
        "description": "Moeder van twee jonge kinderen, werkt parttime",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999991905",
                        "geboortedatum": "1988-10-16",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999991905",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999993872",
                        "children": [
                            {
                                "bsn": "999991723",
                                "geboortedatum": "2020-06-10",
                                "naam": "Kind 1",
                            },
                            {
                                "bsn": "999992740",
                                "geboortedatum": "2022-08-15",
                                "naam": "Kind 2",
                            },
                        ],
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999991905",
                        "straat": "Glitterstraat",
                        "huisnummer": "1",
                        "postcode": "1103SK",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [
                    {"kind_bsn": "999991723", "geboortedatum": "2020-06-10", "naam": "Kind 1"},
                    {"kind_bsn": "999992740", "geboortedatum": "2022-08-15", "naam": "Kind 2"}
                ]
            },
            "UWV": {
                "dienstverbanden": [
                    {
                        "bsn": "999991905",
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                        "uren_per_week": 24,
                        "worked_hours": 1248,
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999991905",
                        "loon_uit_dienstbetrekking": 2000000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 0,
                    }
                ],
                "box2": [
                    {"bsn": "999991905", "dividend": 0, "vervreemding_aandelen": 0}
                ],
                "box3": [
                    {
                        "bsn": "999991905",
                        "spaargeld": 1000000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999991905", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999991905", "persoonsgebonden_aftrek": 0}],
                "monthly_income": [{"bsn": "999991905", "bedrag": 166700}],
                "assets": [{"bsn": "999991905", "bedrag": 1000000}],
                "business_income": [{"bsn": "999991905", "bedrag": 0}],
                "partner_income": [{"bsn": "999991905", "bedrag": 4500000}],
                "partner_assets": [{"bsn": "999991905", "bedrag": 3000000}],
            },
        },
    },
    # Maria - Parttime werknemer met onregelmatige uren
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
    # Omar - Zelfstandige met fluctuerend inkomen in de bouw
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
    # Fatima - Bijstandsgerechtigde met gedeeltelijke arbeidsongeschiktheid
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
    "999993872": {
        "name": "Peter-Jan van der Meijden",
        "description": "Vader van twee jonge kinderen, eigen woning",
        "sources": {
            **GLOBAL_SERVICES,
            "RvIG": {
                "personen": [
                    {
                        "bsn": "999993872",
                        "geboortedatum": "1986-04-17",
                        "verblijfsadres": "Amsterdam",
                        "land_verblijf": "NEDERLAND",
                        "nationaliteit": "NEDERLANDS",
                    }
                ],
                "relaties": [
                    {
                        "bsn": "999993872",
                        "partnerschap_type": "HUWELIJK",
                        "partner_bsn": "999991905",
                        "children": [
                            {
                                "bsn": "999991723",
                                "geboortedatum": "2020-06-10",
                                "naam": "Kind 1",
                            },
                            {
                                "bsn": "999992740",
                                "geboortedatum": "2022-08-15",
                                "naam": "Kind 2",
                            },
                        ],
                    }
                ],
                "verblijfplaats": [
                    {
                        "bsn": "999993872",
                        "straat": "Glitterstraat",
                        "huisnummer": "1",
                        "postcode": "1103SK",
                        "woonplaats": "Amsterdam",
                        "type": "WOONADRES",
                    }
                ],
                "CHILDREN_DATA": [
                    {"kind_bsn": "999991723", "geboortedatum": "2020-06-10", "naam": "Kind 1"},
                    {"kind_bsn": "999992740", "geboortedatum": "2022-08-15", "naam": "Kind 2"}
                ]
            },
            "UWV": {
                "dienstverbanden": [
                    {
                        "bsn": "999993872",
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                        "uren_per_week": 40,
                        "worked_hours": 2080,
                    }
                ]
            },
            "BELASTINGDIENST": {
                "box1": [
                    {
                        "bsn": "999993872",
                        "loon_uit_dienstbetrekking": 4500000,
                        "uitkeringen_en_pensioenen": 0,
                        "winst_uit_onderneming": 0,
                        "resultaat_overige_werkzaamheden": 0,
                        "eigen_woning": 192500,
                    }
                ],
                "box2": [
                    {"bsn": "999993872", "dividend": 0, "vervreemding_aandelen": 0}
                ],
                "box3": [
                    {
                        "bsn": "999993872",
                        "spaargeld": 3000000,
                        "beleggingen": 0,
                        "onroerend_goed": 0,
                        "schulden": 0,
                    }
                ],
                "buitenlands_inkomen": [{"bsn": "999993872", "bedrag": 0, "land": "GEEN"}],
                "aftrekposten": [{"bsn": "999993872", "persoonsgebonden_aftrek": 0}],
                "monthly_income": [{"bsn": "999993872", "bedrag": 375000}],
                "assets": [{"bsn": "999993872", "bedrag": 3000000}],
                "business_income": [{"bsn": "999993872", "bedrag": 0}],
                "partner_income": [{"bsn": "999993872", "bedrag": 2000000}],
                "partner_assets": [{"bsn": "999993872", "bedrag": 1000000}],
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

    return properties


# Business profiles for KVK-based personas
BUSINESS_PROFILES = {
    # CSRD Personas
    "72841234": {
        "name": "GreenTech Solutions BV",
        "description": "Middelgroot technologiebedrijf dat net onder CSRD valt - CEO met beperkte CSRD kennis",
        "persona_id": "csrd_beginner_ceo",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "72841234",
                        "aantal_werknemers": 280,
                        "omzet": 45000000,  # €45M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "GreenTech Solutions BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Software ontwikkeling duurzame technologie",
                        "csrd_status": "EERSTE_JAAR",
                    }
                ]
            },
            "RVO": {
                "csrd_data": [
                    {
                        "kvk_nummer": "72841234",
                        "rapportage_jaar": 2025,
                        "materiality_assessment": "NIET_UITGEVOERD",
                        "externe_verificatie": "NIET_GEREGELD",
                        "esrs_implementatie": "BEGINFASE",
                    }
                ]
            },
        },
    },
    "82475619": {
        "name": "EcoConsult International",
        "description": "CSRD-adviesbureau met expertise in duurzaamheidsrapportage",
        "persona_id": "csrd_expert_consultant",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "82475619",
                        "aantal_werknemers": 45,
                        "omzet": 8500000,  # €8.5M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "EcoConsult International BV",
                        "rechtsvorm": "BV",
                        "activiteit": "CSRD en ESG adviesservices",
                        "csrd_status": "EXPERT_DIENSTVERLENER",
                    }
                ]
            },
        },
    },
    "91863520": {
        "name": "Global Manufacturing Corp",
        "description": "Grote multinational met ervaren sustainability team",
        "persona_id": "csrd_sustainability_director",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "91863520",
                        "aantal_werknemers": 15000,
                        "omzet": 2500000000,  # €2.5B
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Global Manufacturing Corp NV",
                        "rechtsvorm": "NV",
                        "activiteit": "Industriële productie",
                        "csrd_status": "ERVAREN_IMPLEMENTATIE",
                        "beursgenoteerd": True,
                    }
                ]
            },
            "RVO": {
                "csrd_data": [
                    {
                        "kvk_nummer": "91863520",
                        "rapportage_jaar": 2025,
                        "materiality_assessment": "UITGEVOERD",
                        "externe_verificatie": "GEREGELD",
                        "esrs_implementatie": "GEVORDERD",
                        "sustainability_team_grootte": 12,
                    }
                ]
            },
        },
    },
    # Horeca Personas
    "68297415": {
        "name": "Café de Hoek",
        "description": "Eerste café opening in Rotterdam Centrum",
        "persona_id": "horeca_starter_cafe",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "68297415",
                        "aantal_werknemers": 3,
                        "omzet": 150000,  # €150K verwacht
                        "status": "NIEUW",
                        "bedrijfsnaam": "Café de Hoek",
                        "rechtsvorm": "EENMANSZAAK",
                        "activiteit": "Café exploitatie",
                        "locatie": "Rotterdam Centrum",
                    }
                ]
            },
            "GEMEENTE_ROTTERDAM": {
                "vergunningen": [
                    {
                        "kvk_nummer": "68297415",
                        "horeca_vergunning": "AANGEVRAAGD",
                        "alcohol_vergunning": "NIET_AANGEVRAAGD",
                        "terras_vergunning": "NIET_NODIG",
                        "status": "IN_BEHANDELING",
                    }
                ]
            },
        },
    },
    "54732681": {
        "name": "Rotterdam Restaurants Groep",
        "description": "Keten met 15 restaurants verspreid over Rotterdam",
        "persona_id": "horeca_chain_manager",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "54732681",
                        "aantal_werknemers": 180,
                        "omzet": 12000000,  # €12M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Rotterdam Restaurants Groep BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Restaurantexploitatie",
                        "aantal_vestigingen": 15,
                    }
                ]
            },
            "GEMEENTE_ROTTERDAM": {
                "vergunningen": [
                    {
                        "kvk_nummer": "54732681",
                        "horeca_vergunning": "ACTIEF",
                        "aantal_locaties": 15,
                        "compliance_score": "GOED",
                    }
                ]
            },
        },
    },
    # WPM Personas
    "58372941": {
        "name": "TechCorp Nederland",
        "description": "Technologiebedrijf met 2000+ werknemers voor WPM implementatie",
        "persona_id": "wpm_hr_director",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "58372941",
                        "aantal_werknemers": 2200,
                        "omzet": 350000000,  # €350M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "TechCorp Nederland BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Software ontwikkeling",
                    }
                ]
            },
            "RVO": {
                "wpm_gegevens": [
                    {
                        "kvk_nummer": "58372941",
                        "aantal_werknemers": 2200,
                        "verstrekt_mobiliteitsvergoeding": True,
                    }
                ],
                "wpm_data": [
                    {
                        "kvk_nummer": "58372941",
                        "woon_werk_auto_benzine": 450000,  # km per jaar
                        "woon_werk_auto_diesel": 320000,
                        "woon_werk_auto_elektrisch": 180000,
                        "woon_werk_ov": 850000,  # OV kilometers
                        "woon_werk_fiets": 120000,
                        "zakelijk_auto_benzine": 280000,
                        "zakelijk_auto_diesel": 195000,
                        "zakelijk_vliegtuig_binnenland": 25000,
                        "zakelijk_vliegtuig_europa": 180000,
                        "zakelijk_vliegtuig_intercontinentaal": 320000,
                    }
                ],
            },
        },
    },
    "81563429": {
        "name": "WPM Consultancy Partners",
        "description": "Gespecialiseerd adviesbureau voor WPM implementatie",
        "persona_id": "wpm_external_consultant",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "81563429",
                        "aantal_werknemers": 25,
                        "omzet": 4200000,  # €4.2M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "WPM Consultancy Partners BV",
                        "rechtsvorm": "BV",
                        "activiteit": "WPM implementatie advies",
                        "specialisatie": "WERKNEMERS_PERSONEN_MOBILITEIT",
                    }
                ]
            },
        },
    },
    "74185296": {
        "name": "InnovateNow Startup",
        "description": "50-persoons tech startup met remote/hybrid model",
        "persona_id": "wpm_startup_founder",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "74185296",
                        "aantal_werknemers": 52,
                        "omzet": 3800000,  # €3.8M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "InnovateNow Startup BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Software as a Service",
                        "werk_model": "HYBRID_REMOTE",
                    }
                ]
            },
            "RVO": {
                "wpm_gegevens": [
                    {
                        "kvk_nummer": "74185296",
                        "aantal_werknemers": 52,
                        "verstrekt_mobiliteitsvergoeding": False,
                    }
                ],
                "wpm_data": [
                    {
                        "kvk_nummer": "74185296",
                        "woon_werk_auto_benzine": 15000,  # Laag door remote werk
                        "woon_werk_auto_diesel": 8000,
                        "woon_werk_ov": 25000,
                        "co_working_spaces": 180000,  # km naar co-working spaces
                        "client_visits": 85000,
                        "team_meetups": 32000,
                    }
                ],
            },
        },
    },
    # Additional CSRD personas
    "45681297": {
        "name": "DataTech Analytics",
        "description": "Tech bedrijf met focus op CSRD data-analyse",
        "persona_id": "csrd_data_analyst",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "45681297",
                        "aantal_werknemers": 120,
                        "omzet": 18500000,  # €18.5M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "DataTech Analytics BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Data-analyse en ESG rapportage",
                        "csrd_status": "IMPLEMENTATIE_FASE",
                    }
                ]
            },
        },
    },
    "59374892": {
        "name": "LegalCorp Adviseurs",
        "description": "Juridisch adviesbureau gespecialiseerd in corporate compliance",
        "persona_id": "csrd_legal_counsel",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "59374892",
                        "aantal_werknemers": 85,
                        "omzet": 15200000,  # €15.2M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "LegalCorp Adviseurs BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Juridische CSRD compliance diensten",
                        "specialisatie": "CORPORATE_COMPLIANCE",
                    }
                ]
            },
        },
    },
    # Additional Horeca personas
    "73519847": {
        "name": "Club Nachtleven Rotterdam",
        "description": "Nachtclub in Rotterdam met complexe vergunningen",
        "persona_id": "horeca_night_club_owner",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "73519847",
                        "aantal_werknemers": 45,
                        "omzet": 2800000,  # €2.8M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Club Nachtleven Rotterdam BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Nachtclub exploitatie",
                        "locatie": "Rotterdam Centrum",
                        "openingstijden": "NACHT",
                    }
                ]
            },
            "GEMEENTE_ROTTERDAM": {
                "vergunningen": [
                    {
                        "kvk_nummer": "73519847",
                        "horeca_vergunning": "ACTIEF",
                        "alcohol_vergunning": "ACTIEF",
                        "evenementen_vergunning": "ACTIEF",
                        "geluidsvergunning": "ACTIEF",
                        "veiligheid_score": "GOED",
                    }
                ]
            },
        },
    },
    "86297531": {
        "name": "FastFood Franchise Rotterdam",
        "description": "Fastfood franchiseketen met 3 locaties",
        "persona_id": "horeca_franchise_owner",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "86297531",
                        "aantal_werknemers": 35,
                        "omzet": 1850000,  # €1.85M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "FastFood Franchise Rotterdam BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Fastfood franchise exploitatie",
                        "aantal_vestigingen": 3,
                        "franchise_type": "FASTFOOD",
                    }
                ]
            },
        },
    },
    "52893741": {
        "name": "Craft Brewery Rotterdam",
        "description": "Craft brewery met taproom en productie",
        "persona_id": "horeca_craft_brewery_owner",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "52893741",
                        "aantal_werknemers": 12,
                        "omzet": 750000,  # €750K
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Craft Brewery Rotterdam BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Bierbrouwerij met taproom",
                        "speciale_vergunningen": "ALCOHOL_PRODUCTIE",
                    }
                ]
            },
        },
    },
    # Additional WPM personas
    "67428591": {
        "name": "FleetManagement Services",
        "description": "Bedrijf gespecialiseerd in wagenparkbeheer",
        "persona_id": "wpm_fleet_manager",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "67428591",
                        "aantal_werknemers": 85,
                        "omzet": 12500000,  # €12.5M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "FleetManagement Services BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Wagenparkbeheer en mobiliteitsadvies",
                        "voertuigen_onder_beheer": 300,
                    }
                ]
            },
            "RVO": {
                "wpm_gegevens": [
                    {
                        "kvk_nummer": "67428591",
                        "aantal_werknemers": 85,
                        "verstrekt_mobiliteitsvergoeding": True,
                    }
                ],
                "wpm_data": [
                    {
                        "kvk_nummer": "67428591",
                        "fleet_benzine": 850000,  # km per jaar
                        "fleet_diesel": 1200000,
                        "fleet_elektrisch": 320000,
                        "fuel_efficiency_tracking": True,
                        "emissions_monitoring": "ACTIEF",
                    }
                ],
            },
        },
    },
    "85296741": {
        "name": "BusinessTravel Solutions",
        "description": "Zakelijke reizen en travel management",
        "persona_id": "wpm_travel_manager",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "85296741",
                        "aantal_werknemers": 28,
                        "omzet": 5200000,  # €5.2M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "BusinessTravel Solutions BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Business travel management",
                        "specialisatie": "CORPORATE_TRAVEL",
                    }
                ]
            },
        },
    },
    # Missing CSRD personas
    "94728163": {
        "name": "FinanceCorp Holdings",
        "description": "CFO van middelgroot bedrijf bezorgd over CSRD kosten",
        "persona_id": "csrd_cfo",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "94728163",
                        "aantal_werknemers": 195,
                        "omzet": 32000000,  # €32M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "FinanceCorp Holdings BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Financiële dienstverlening",
                        "csrd_status": "KOSTEN_EVALUATIE",
                    }
                ]
            },
        },
    },
    "36851947": {
        "name": "StartupTech Innovation",
        "description": "Junior coordinator bij tech startup voor CSRD project",
        "persona_id": "csrd_junior_coordinator",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "36851947",
                        "aantal_werknemers": 65,
                        "omzet": 8500000,  # €8.5M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "StartupTech Innovation BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Technology innovation",
                        "csrd_status": "EERSTE_IMPLEMENTATIE",
                    }
                ]
            },
        },
    },
    "75293846": {
        "name": "PublicCorp Communications",
        "description": "Beursgenoteerd bedrijf met focus op investor relations",
        "persona_id": "csrd_investor_relations",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "75293846",
                        "aantal_werknemers": 850,
                        "omzet": 125000000,  # €125M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "PublicCorp Communications NV",
                        "rechtsvorm": "NV",
                        "activiteit": "Media en communicatie",
                        "beursgenoteerd": True,
                        "csrd_status": "INVESTOR_FOCUS",
                    }
                ]
            },
        },
    },
    "48572931": {
        "name": "Manufacturing Operations BV",
        "description": "Productiebedrijf met operations manager voor CSRD data",
        "persona_id": "csrd_operations_manager",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "48572931",
                        "aantal_werknemers": 320,
                        "omzet": 58000000,  # €58M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Manufacturing Operations BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Industriële productie",
                        "csrd_status": "OPERATIONELE_DATA",
                    }
                ]
            },
        },
    },
    "62847395": {
        "name": "Executive Holdings Group",
        "description": "Holding met niet-uitvoerende bestuurders",
        "persona_id": "csrd_board_member",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "62847395",
                        "aantal_werknemers": 1200,
                        "omzet": 185000000,  # €185M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Executive Holdings Group NV",
                        "rechtsvorm": "NV",
                        "activiteit": "Holding maatschappij",
                        "governance_focus": True,
                        "csrd_status": "GOVERNANCE_OVERSIGHT",
                    }
                ]
            },
        },
    },
    "39657284": {
        "name": "Global Supply Chain Solutions",
        "description": "Supply chain bedrijf gespecialiseerd in Scope 3 emissies",
        "persona_id": "csrd_supply_chain_manager",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "39657284",
                        "aantal_werknemers": 180,
                        "omzet": 28000000,  # €28M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Global Supply Chain Solutions BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Supply chain management",
                        "specialisatie": "SCOPE3_EMISSIONS",
                    }
                ]
            },
        },
    },
    "51948372": {
        "name": "Audit & Assurance Partners",
        "description": "Audit kantoor gespecialiseerd in CSRD verificatie",
        "persona_id": "csrd_auditor",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "51948372",
                        "aantal_werknemers": 95,
                        "omzet": 18500000,  # €18.5M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Audit & Assurance Partners BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Accountancy en auditing",
                        "specialisatie": "CSRD_VERIFICATION",
                    }
                ]
            },
        },
    },
    # Missing Horeca personas
    "72946385": {
        "name": "Rotterdam Food Safety Experts",
        "description": "Consultancy gespecialiseerd in horeca food safety",
        "persona_id": "horeca_food_safety_specialist",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "72946385",
                        "aantal_werknemers": 15,
                        "omzet": 1250000,  # €1.25M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Rotterdam Food Safety Experts BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Food safety consultancy",
                        "specialisatie": "HACCP_COMPLIANCE",
                        "locatie": "Rotterdam",
                    }
                ]
            },
        },
    },
    "84759631": {
        "name": "HoReCa Permit Adviseurs",
        "description": "Gespecialiseerd in Rotterdam horecavergunningen",
        "persona_id": "horeca_permit_consultant",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "84759631",
                        "aantal_werknemers": 8,
                        "omzet": 850000,  # €850K
                        "status": "ACTIEF",
                        "bedrijfsnaam": "HoReCa Permit Adviseurs BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Horeca vergunning consultancy",
                        "specialisatie": "PERMIT_SPECIALIST",
                        "locatie": "Rotterdam",
                    }
                ]
            },
        },
    },
    "95738264": {
        "name": "Megacorp Hospitality Group",
        "description": "Grote horecagroep met compliance officer",
        "persona_id": "horeca_compliance_officer",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "95738264",
                        "aantal_werknemers": 850,
                        "omzet": 85000000,  # €85M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Megacorp Hospitality Group BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Horeca exploitatie",
                        "aantal_vestigingen": 50,
                        "compliance_focus": True,
                    }
                ]
            },
        },
    },
    "47382951": {
        "name": "Gemeente Rotterdam - Horeca Toezicht",
        "description": "Gemeente Rotterdam horeca inspectie afdeling",
        "persona_id": "horeca_inspector",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "47382951",
                        "aantal_werknemers": 25,
                        "omzet": 0,  # Gemeente
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Gemeente Rotterdam",
                        "rechtsvorm": "GEMEENTE",
                        "activiteit": "Horeca inspectie en handhaving",
                        "locatie": "Rotterdam",
                        "overheid": True,
                    }
                ]
            },
        },
    },
    "63847295": {
        "name": "Strandpaviljoen De Zeemeeuw",
        "description": "Seizoensgebonden strandtent operation",
        "persona_id": "horeca_seasonal_owner",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "63847295",
                        "aantal_werknemers": 12,
                        "omzet": 650000,  # €650K (seizoensgebonden)
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Strandpaviljoen De Zeemeeuw",
                        "rechtsvorm": "EENMANSZAAK",
                        "activiteit": "Strandtent exploitatie",
                        "locatie": "Rotterdam Strand",
                        "seizoensgebonden": True,
                    }
                ]
            },
        },
    },
    "58394726": {
        "name": "Foodtruck Rotterdam Centraal",
        "description": "Mobiele foodtruck operation",
        "persona_id": "horeca_food_truck_operator",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "58394726",
                        "aantal_werknemers": 3,
                        "omzet": 180000,  # €180K
                        "status": "ACTIEF",
                        "bedrijfsnaam": "Foodtruck Rotterdam Centraal",
                        "rechtsvorm": "EENMANSZAAK",
                        "activiteit": "Mobiele horeca",
                        "locatie": "Rotterdam (mobiel)",
                        "mobiel": True,
                    }
                ]
            },
        },
    },
    "74629583": {
        "name": "HoReCa Legal Partners",
        "description": "Juridisch kantoor gespecialiseerd in horecarecht",
        "persona_id": "horeca_legal_advisor",
        "sources": {
            "KVK": {
                "organisaties": [
                    {
                        "kvk_nummer": "74629583",
                        "aantal_werknemers": 18,
                        "omzet": 2800000,  # €2.8M
                        "status": "ACTIEF",
                        "bedrijfsnaam": "HoReCa Legal Partners BV",
                        "rechtsvorm": "BV",
                        "activiteit": "Juridische diensten horeca",
                        "specialisatie": "HORECA_LAW",
                    }
                ]
            },
        },
    },
}


def get_business_data(kvk_nummer: str) -> dict[str, Any]:
    """
    Get business profile data for a specific KVK nummer.
    """
    return BUSINESS_PROFILES.get(kvk_nummer)


def get_business_profile_properties(profile: dict) -> list[str]:
    """Extract key properties from a business profile with emoji representations"""
    properties = []

    if not profile.get("sources") or not profile["sources"].get("KVK"):
        return properties

    kvk_data = profile["sources"]["KVK"]
    org_data = next(iter(kvk_data.get("organisaties", [])), {})

    if not org_data:
        return properties

    # Add employee count
    employees = org_data.get("aantal_werknemers", 0)
    if employees:
        if employees < 10:
            properties.append(f"👥 {employees} werknemers (micro)")
        elif employees < 50:
            properties.append(f"👥 {employees} werknemers (klein)")
        elif employees < 250:
            properties.append(f"👥 {employees} werknemers (middel)")
        else:
            properties.append(f"👥 {employees} werknemers (groot)")

    # Add revenue
    omzet = org_data.get("omzet", 0)
    if omzet:
        if omzet >= 1000000000:  # €1B+
            properties.append(f"💰 €{omzet / 1000000000:.1f}B omzet")
        elif omzet >= 1000000:  # €1M+
            properties.append(f"💰 €{omzet / 1000000:.1f}M omzet")
        else:
            properties.append(f"💰 €{omzet / 1000:.0f}K omzet")

    # Add legal form
    rechtsvorm = org_data.get("rechtsvorm")
    if rechtsvorm:
        properties.append(f"🏢 {rechtsvorm}")

    # Add status
    status = org_data.get("status")
    if status == "ACTIEF":
        properties.append("✅ Actief")
    elif status == "NIEUW":
        properties.append("🆕 Nieuw")

    # Add special characteristics
    if org_data.get("beursgenoteerd"):
        properties.append("📈 Beursgenoteerd")

    if org_data.get("werk_model"):
        work_model = org_data["werk_model"]
        if work_model == "HYBRID_REMOTE":
            properties.append("🏠 Hybrid/Remote")

    # Add CSRD status if applicable
    csrd_status = org_data.get("csrd_status")
    if csrd_status:
        if csrd_status == "EERSTE_JAAR":
            properties.append("📋 CSRD nieuw")
        elif csrd_status == "EXPERT_DIENSTVERLENER":
            properties.append("🎯 CSRD expert")
        elif csrd_status == "ERVAREN_IMPLEMENTATIE":
            properties.append("⭐ CSRD ervaren")

    # Add location for horeca
    locatie = org_data.get("locatie")
    if locatie:
        properties.append(f"📍 {locatie}")

    # Add number of locations if multi-location business
    aantal_vestigingen = org_data.get("aantal_vestigingen")
    if aantal_vestigingen and aantal_vestigingen > 1:
        properties.append(f"🏪 {aantal_vestigingen} vestigingen")

    # Add franchise type for franchise businesses
    franchise_type = org_data.get("franchise_type")
    if franchise_type:
        properties.append(f"🍔 {franchise_type}")

    # Add special operating hours
    openingstijden = org_data.get("openingstijden")
    if openingstijden == "NACHT":
        properties.append("🌙 Nachtclub")

    # Add special permits
    speciale_vergunningen = org_data.get("speciale_vergunningen")
    if speciale_vergunningen == "ALCOHOL_PRODUCTIE":
        properties.append("🍺 Alcoholproductie")

    # Add fleet size for fleet managers
    voertuigen_onder_beheer = org_data.get("voertuigen_onder_beheer")
    if voertuigen_onder_beheer:
        properties.append(f"🚗 {voertuigen_onder_beheer} voertuigen")

    # Add specialization
    specialisatie = org_data.get("specialisatie")
    if specialisatie:
        if specialisatie == "CORPORATE_COMPLIANCE":
            properties.append("⚖️ Compliance")
        elif specialisatie == "WERKNEMERS_PERSONEN_MOBILITEIT":
            properties.append("🚶‍♂️ WPM specialist")
        elif specialisatie == "CORPORATE_TRAVEL":
            properties.append("✈️ Zakelijk reizen")

    return properties


def get_all_profiles() -> dict[str, dict[str, Any]]:
    """Get all available BSN profiles with properties"""
    profiles = PROFILES.copy()

    # Add properties to each profile
    for bsn, profile in profiles.items():
        profile["properties"] = get_profile_properties(profile)

    return profiles


def get_all_business_profiles() -> dict[str, dict[str, Any]]:
    """Get all available business profiles with properties"""
    profiles = BUSINESS_PROFILES.copy()

    # Add properties to each profile
    for kvk_nummer, profile in profiles.items():
        profile["properties"] = get_business_profile_properties(profile)

    return profiles


def get_profile_by_id(profile_id: str) -> dict[str, Any] | None:
    """Get profile data by BSN or KVK number"""
    # Try BSN first
    if profile_id in PROFILES:
        profile = PROFILES[profile_id].copy()
        profile["properties"] = get_profile_properties(profile)
        profile["type"] = "BSN"
        return profile

    # Try KVK number
    if profile_id in BUSINESS_PROFILES:
        profile = BUSINESS_PROFILES[profile_id].copy()
        profile["properties"] = get_business_profile_properties(profile)
        profile["type"] = "KVK"
        return profile

    return None
